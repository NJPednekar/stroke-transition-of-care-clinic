from datetime import date
from pathlib import Path

import pandas as pd

from stcc_logic import derive_workflow, load_data


DATA = Path(__file__).parents[1] / "stroke_transitions_of_care_clinic_synthetic_updated.csv"


def base_patient(**overrides):
    row = load_data(DATA).iloc[0].copy()
    defaults = {
        "stcc_eligible": "Yes", "appointment_status": "Scheduled",
        "admission_date": pd.Timestamp("2026-07-28"), "discharge_date": pd.Timestamp("2026-08-01"),
        "appointment_date": pd.Timestamp("2026-08-10"), "med_reconciliation_completed": "Yes",
        "secondary_prevention_plan_documented": "Yes", "cardiac_monitoring_needed": "No",
        "cardiac_monitoring_completed": "Not applicable", "other_workup_needed": "No",
        "other_workup_type": "None", "other_workup_completed": "Not applicable", "rehab_needed": "No",
        "rehab_arranged": "Not applicable", "rehab_completed": "Not applicable", "pcp_followup_arranged": "Yes",
        "specialty_referral_needed": "No", "specialty_referral_completed": "Not applicable",
        "transportation_barrier": "No", "housing_instability": "No", "food_insecurity": "No",
        "economic_or_insurance_barrier": "No", "limited_caregiver_support": "No",
    }
    for key, value in (defaults | overrides).items():
        row[key] = value
    return row


def classify(**overrides):
    patients, tasks = derive_workflow(pd.DataFrame([base_patient(**overrides)]), date(2026, 8, 5))
    return patients.iloc[0], tasks


def test_ineligible_patient_uses_alternative_pathway():
    patient, _ = classify(stcc_eligible="No", appointment_status="Not scheduled", appointment_date=pd.NaT)
    assert patient.patient_section == "Alternative Transition Pathway"


def test_completed_patient_without_gaps_is_closed_loop():
    patient, tasks = classify(appointment_status="Completed")
    assert patient.patient_section == "Closed Loop / Completed"
    assert patient.workflow_state == "Visit Completed + Tasks Complete"
    assert tasks.empty


def test_completed_patient_with_gap_moves_to_post_visit_queue():
    patient, tasks = classify(appointment_status="Completed", med_reconciliation_completed="No")
    assert patient.patient_section == "Post-Visit Care-Gap Queue"
    assert patient.workflow_state == "Visit Completed + Tasks Pending"
    assert tasks.iloc[0].task_domain == "Medication & prevention"


def test_cancelled_and_no_show_require_immediate_action():
    for status in ("Cancelled", "No-show"):
        patient, _ = classify(appointment_status=status)
        assert patient.workflow_category == "Immediate Action Required"


def test_old_unscheduled_patient_requires_immediate_action():
    patient, _ = classify(appointment_status="Not scheduled", appointment_date=pd.NaT, discharge_date=pd.Timestamp("2026-07-20"))
    assert patient.workflow_category == "Immediate Action Required"


def test_scheduled_in_window_without_gaps_is_on_track():
    patient, _ = classify()
    assert patient.workflow_category == "On Track"
    assert patient.workflow_state == "Appointment / Visit Needed + Tasks Complete"


def test_visit_needed_with_gap_has_tasks_pending_state():
    patient, _ = classify(med_reconciliation_completed="No")
    assert patient.workflow_state == "Appointment / Visit Needed + Tasks Pending"


def test_scheduling_appointment_recalculates_priority_without_manual_priority_input():
    unscheduled, _ = classify(
        appointment_status="Not scheduled", appointment_date=pd.NaT,
        discharge_date=pd.Timestamp("2026-07-20"),
    )
    scheduled, _ = classify()

    assert unscheduled.workflow_category == "Immediate Action Required"
    assert scheduled.workflow_category == "On Track"


def test_completing_visit_and_all_applicable_tasks_closes_transition():
    pending, _ = classify(
        appointment_status="Completed", cardiac_monitoring_needed="Yes",
        cardiac_monitoring_completed="No",
    )
    complete, tasks = classify(
        appointment_status="Completed", cardiac_monitoring_needed="Yes",
        cardiac_monitoring_completed="Yes",
    )

    assert pending.workflow_state == "Visit Completed + Tasks Pending"
    assert complete.workflow_state == "Visit Completed + Tasks Complete"
    assert complete.patient_section == "Closed Loop / Completed"
    assert tasks.empty


def test_clinical_context_does_not_change_category():
    first, _ = classify(nihss=0, mrs=0, discharge_disposition="Home")
    second, _ = classify(nihss=35, mrs=5, discharge_disposition="Skilled nursing facility")
    assert first.workflow_category == second.workflow_category == "On Track"


def test_multiple_gaps_create_multiple_task_rows():
    _, tasks = classify(med_reconciliation_completed="No", pcp_followup_arranged="No", food_insecurity="Yes")
    assert len(tasks) == 3
    assert set(tasks.task_domain) == {"Medication & prevention", "PCP & specialty", "SDOH & access"}


def test_repeat_hospitalizations_are_distinct_transition_episodes():
    first = base_patient(
        patient_id="STCC-TEST", admission_date=pd.Timestamp("2026-06-25"),
        discharge_date=pd.Timestamp("2026-07-01"), appointment_status="Completed",
        appointment_date=pd.Timestamp("2026-07-08"),
    )
    second = base_patient(
        patient_id="STCC-TEST", admission_date=pd.Timestamp("2026-07-20"),
        discharge_date=pd.Timestamp("2026-07-24"), appointment_status="Not scheduled",
        appointment_date=pd.NaT,
    )
    patients, _ = derive_workflow(pd.DataFrame([first, second]), date(2026, 8, 5))

    assert len(patients) == 2
    later = patients.loc[patients.discharge_date == pd.Timestamp("2026-07-24")].iloc[0]
    assert later.hospitalization_number == 2
    assert later.days_since_prior_discharge == 19
    assert later.readmission_window == "Readmission within 30 days"

    second.med_reconciliation_completed = "No"
    updated, _ = derive_workflow(pd.DataFrame([first, second]), date(2026, 8, 5))
    updated_later = updated.loc[
        updated.discharge_date == pd.Timestamp("2026-07-24")
    ].iloc[0]
    assert updated_later.readmission_window == later.readmission_window
    assert updated_later.days_since_prior_discharge == later.days_since_prior_discharge


def test_updated_dataset_has_valid_admissions_and_repeat_episode_windows():
    frame = load_data(DATA)
    assert (frame.admission_date < frame.discharge_date).all()
    assert not frame.duplicated(["patient_id", "discharge_date"]).any()

    repeated = frame[frame.duplicated("patient_id", keep=False)].sort_values(
        ["patient_id", "discharge_date"]
    )
    intervals = (
        repeated.admission_date - repeated.groupby("patient_id").discharge_date.shift()
    ).dt.days.dropna()
    assert intervals.between(0, 30).any()
    assert intervals.between(31, 90).any()
