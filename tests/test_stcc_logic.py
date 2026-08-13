from datetime import date
from pathlib import Path

import pandas as pd

from stcc_logic import derive_workflow, load_data


DATA = Path(__file__).parents[1] / "stroke_transitions_of_care_clinic_synthetic_updated.csv"


def base_patient(**overrides):
    row = load_data(DATA).iloc[0].copy()
    defaults = {
        "stcc_eligible": "Yes", "appointment_status": "Scheduled", "discharge_date": pd.Timestamp("2026-08-01"),
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
    assert tasks.empty


def test_completed_patient_with_gap_moves_to_post_visit_queue():
    patient, tasks = classify(appointment_status="Completed", med_reconciliation_completed="No")
    assert patient.patient_section == "Post-Visit Care-Gap Queue"
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


def test_clinical_context_does_not_change_category():
    first, _ = classify(nihss=0, mrs=0, discharge_disposition="Home")
    second, _ = classify(nihss=35, mrs=5, discharge_disposition="Skilled nursing facility")
    assert first.workflow_category == second.workflow_category == "On Track"


def test_multiple_gaps_create_multiple_task_rows():
    _, tasks = classify(med_reconciliation_completed="No", pcp_followup_arranged="No", food_insecurity="Yes")
    assert len(tasks) == 3
    assert set(tasks.task_domain) == {"Medication & prevention", "PCP & specialty", "SDOH & access"}
