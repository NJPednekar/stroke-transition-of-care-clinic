"""Transparent workflow rules for the STCC educational prototype."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd


REQUIRED_COLUMNS = {
    "patient_id", "age", "sex", "stroke_type", "stroke_etiology", "nihss", "mrs",
    "admission_date", "discharge_date", "discharge_disposition", "stcc_eligible", "appointment_status",
    "appointment_date", "med_reconciliation_completed",
    "secondary_prevention_plan_documented", "cardiac_monitoring_needed",
    "cardiac_monitoring_completed", "other_workup_needed", "other_workup_type",
    "other_workup_completed", "rehab_needed", "rehab_arranged", "rehab_completed",
    "pcp_followup_arranged", "specialty_referral_needed", "specialty_referral_completed",
    "transportation_barrier", "housing_instability", "food_insecurity",
    "economic_or_insurance_barrier", "limited_caregiver_support",
}
APPOINTMENT_STATUSES = {"Not scheduled", "Scheduled", "Completed", "Cancelled", "No-show"}
BARRIER_FIELDS = {
    "transportation_barrier": ("Transportation barrier", "Confirm transportation for the next visit or test and coordinate assistance if needed."),
    "housing_instability": ("Housing instability", "Confirm current housing needs and connect the patient with social work or community resources."),
    "food_insecurity": ("Food insecurity", "Confirm ongoing food-support needs and connect the patient with available resources."),
    "economic_or_insurance_barrier": ("Economic or insurance barrier", "Engage insurance navigation, financial counseling, or assistance resources as appropriate."),
    "limited_caregiver_support": ("Limited caregiver support", "Confirm a reliable contact and support plan with the patient and care team."),
}


@dataclass(frozen=True)
class Gap:
    domain: str
    gap: str
    action: str
    kind: str = "care_gap"


def load_data(source: str | Path | object) -> pd.DataFrame:
    """Load and minimally validate the prototype CSV."""
    frame = pd.read_csv(source, dtype={"patient_id": "string"})
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    invalid = sorted(set(frame["appointment_status"].dropna()) - APPOINTMENT_STATUSES)
    if invalid:
        raise ValueError(f"Unexpected appointment_status values: {', '.join(invalid)}")
    frame["admission_date"] = pd.to_datetime(frame["admission_date"], errors="raise")
    frame["discharge_date"] = pd.to_datetime(frame["discharge_date"], errors="raise")
    if frame.duplicated(["patient_id", "discharge_date"]).any():
        raise ValueError("patient_id and discharge_date combinations must be unique.")
    if (frame["admission_date"] >= frame["discharge_date"]).any():
        raise ValueError("admission_date must be before discharge_date.")
    frame["appointment_date"] = pd.to_datetime(frame["appointment_date"], errors="coerce")
    return frame


def identify_gaps(row: pd.Series) -> list[Gap]:
    """Return actionable gaps; recorded barriers are explicitly status-review tasks."""
    gaps: list[Gap] = []
    if row.med_reconciliation_completed == "No":
        gaps.append(Gap("Medication & prevention", "Medication reconciliation incomplete", "Complete medication reconciliation with the patient/caregiver and responsible clinician."))
    if row.secondary_prevention_plan_documented == "No":
        gaps.append(Gap("Medication & prevention", "Secondary prevention plan not documented", "Confirm and document the secondary prevention plan."))
    if row.cardiac_monitoring_needed == "Yes" and row.cardiac_monitoring_completed == "No":
        gaps.append(Gap("Cardiac monitoring", "Required cardiac monitoring incomplete", "Confirm monitoring ordering, access, activation, and completion status."))
    if row.other_workup_needed == "Yes" and row.other_workup_completed == "No":
        workup = row.other_workup_type
        gaps.append(Gap("Other stroke workup", f"{workup} incomplete", f"Confirm scheduling and completion of the outstanding {str(workup).lower()}."))
    if row.rehab_needed == "Yes" and row.rehab_arranged == "No":
        gaps.append(Gap("Rehabilitation", "Required rehabilitation not arranged", "Coordinate the needed rehabilitation referral and access plan."))
    elif row.rehab_needed == "Yes" and row.rehab_completed == "No":
        gaps.append(Gap("Rehabilitation", "Arranged rehabilitation not yet completed", "Confirm rehabilitation status, expected course, and any participation or access barriers."))
    if row.pcp_followup_arranged == "No":
        gaps.append(Gap("PCP & specialty", "PCP follow-up not arranged", "Arrange PCP follow-up and communicate the discharge plan."))
    if row.specialty_referral_needed == "Yes" and row.specialty_referral_completed == "No":
        gaps.append(Gap("PCP & specialty", "Required specialty referral incomplete", "Confirm the required referral, scheduling status, and responsible service."))
    for field, (label, action) in BARRIER_FIELDS.items():
        if row[field] == "Yes":
            gaps.append(Gap("SDOH & access", f"{label} recorded; status requires confirmation", action, "barrier"))
    return gaps


def _appointment_gap(row: pd.Series, as_of: date, target_days: int, escalation_days: int) -> Gap | None:
    status, days = row.appointment_status, row.days_since_discharge
    if status in {"Cancelled", "No-show"}:
        return Gap("Appointment & scheduling", f"STCC appointment {status.lower()}", "Contact the patient/caregiver, assess barriers, and reschedule the STCC visit.", "appointment")
    if status == "Scheduled" and pd.notna(row.appointment_date) and row.appointment_date.date() < as_of:
        return Gap("Appointment & scheduling", "Scheduled date has passed without a completed status", "Verify attendance and appointment status; reschedule if the visit did not occur.", "appointment")
    if status == "Not scheduled":
        urgency = " beyond the outreach threshold" if days > escalation_days else ""
        return Gap("Appointment & scheduling", f"STCC visit not scheduled{urgency}", "Contact the patient/caregiver and schedule the earliest appropriate STCC visit.", "appointment")
    if status == "Scheduled" and row.days_discharge_to_appointment > target_days:
        return Gap("Appointment & scheduling", f"Appointment is outside the {target_days}-day target window", "Review whether an earlier STCC appointment is available and appropriate.", "appointment")
    return None


def derive_workflow(frame: pd.DataFrame, as_of: date, target_days: int = 14, escalation_days: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Derive mutually exclusive patient sections and a one-row-per-task table."""
    df = frame.copy().reset_index(drop=True)
    as_timestamp = pd.Timestamp(as_of)
    df["days_since_discharge"] = (as_timestamp - df["discharge_date"]).dt.days
    df["days_discharge_to_appointment"] = (df["appointment_date"] - df["discharge_date"]).dt.days.astype("Int64")
    df["days_until_appointment"] = (df["appointment_date"] - as_timestamp).dt.days.astype("Int64")
    episode_order = df.sort_values(["patient_id", "discharge_date"]).index
    ordered = df.loc[episode_order]
    df.loc[episode_order, "hospitalization_number"] = (
        ordered.groupby("patient_id").cumcount().add(1).to_numpy()
    )
    df["hospitalization_number"] = df["hospitalization_number"].astype("Int64")
    prior_discharge = ordered.groupby("patient_id")["discharge_date"].shift()
    df.loc[episode_order, "days_since_prior_discharge"] = (
        ordered["admission_date"] - prior_discharge
    ).dt.days.astype("Int64").to_numpy()
    df["days_since_prior_discharge"] = df["days_since_prior_discharge"].astype("Int64")
    intervals = df["days_since_prior_discharge"]
    df["readmission_window"] = "First recorded hospitalization"
    df.loc[intervals.between(0, 30), "readmission_window"] = "Readmission within 30 days"
    df.loc[intervals.between(31, 90), "readmission_window"] = "Readmission within 31–90 days"
    df.loc[intervals > 90, "readmission_window"] = "Readmission after 90 days"

    records, tasks = [], []
    for _, row in df.iterrows():
        gaps = identify_gaps(row)
        visit_completed = row.appointment_status == "Completed"
        tasks_complete = not gaps
        if visit_completed:
            workflow_state = (
                "Visit Completed + Tasks Complete"
                if tasks_complete
                else "Visit Completed + Tasks Pending"
            )
        else:
            workflow_state = (
                "Appointment / Visit Needed + Tasks Complete"
                if tasks_complete
                else "Appointment / Visit Needed + Tasks Pending"
            )
        appointment_gap = None
        if row.stcc_eligible == "No":
            section, category = "Alternative Transition Pathway", "Route to alternate pathway"
            reason = "Patient is not eligible for the STCC workflow."
        elif row.appointment_status == "Completed":
            if gaps:
                section, category = "Post-Visit Care-Gap Queue", "Action Needed"
                reason = f"STCC visit completed; {len(gaps)} transition task{'s' if len(gaps) != 1 else ''} require follow-up."
            else:
                section, category = "Closed Loop / Completed", "Closed Loop"
                reason = "STCC visit and all documented transition requirements are complete."
        else:
            section = "Active STCC Queue"
            appointment_gap = _appointment_gap(row, as_of, target_days, escalation_days)
            barrier_count = sum(g.kind == "barrier" for g in gaps)
            domains = len({g.domain for g in gaps if g.kind != "barrier"})
            immediate = (
                row.appointment_status in {"Cancelled", "No-show"}
                or (row.appointment_status == "Scheduled" and pd.notna(row.appointment_date) and row.appointment_date.date() < as_of)
                or (row.appointment_status == "Not scheduled" and row.days_since_discharge > escalation_days)
                or (domains >= 2 and barrier_count >= 1)
            )
            if immediate:
                category = "Immediate Action Required"
            elif appointment_gap or gaps:
                category = "Action Needed"
            else:
                category = "On Track"
            if appointment_gap:
                reason = appointment_gap.gap + "."
            elif category == "On Track":
                reason = f"Appointment is scheduled within the {target_days}-day target window with no documented pre-visit action needed."
            else:
                reason = f"Appointment is scheduled, but {len(gaps)} transition task{'s' if len(gaps) != 1 else ''} require attention."

        all_tasks = ([appointment_gap] if appointment_gap else []) + gaps
        clinical_gaps = [g for g in gaps if g.kind != "barrier"]
        barriers = [g for g in gaps if g.kind == "barrier"]
        result = row.to_dict() | {
            "patient_section": section, "workflow_category": category,
            "workflow_state": workflow_state, "primary_reason": reason,
            "unresolved_task_count": len(all_tasks), "unresolved_domain_count": len({g.domain for g in clinical_gaps}),
            "recorded_barrier_count": len(barriers), "outstanding_needs": "; ".join(g.gap for g in all_tasks) or "None documented",
            "next_actions": " | ".join(g.action for g in all_tasks) or "No action required",
        }
        records.append(result)
        for task in all_tasks:
            tasks.append({"patient_id": row.patient_id, "discharge_date": row.discharge_date,
                          "patient_section": section, "workflow_category": category,
                          "workflow_state": workflow_state,
                          "appointment_status": row.appointment_status, "days_since_discharge": row.days_since_discharge,
                          "task_domain": task.domain, "outstanding_task": task.gap, "recommended_action": task.action})
    patients = pd.DataFrame(records)
    rank = {"Immediate Action Required": 0, "Action Needed": 1, "On Track": 2, "Route to alternate pathway": 3, "Closed Loop": 4}
    patients["_rank"] = patients["workflow_category"].map(rank)
    patients = patients.sort_values(["_rank", "days_since_discharge", "unresolved_task_count", "patient_id"], ascending=[True, False, False, True]).drop(columns="_rank")
    return patients, pd.DataFrame(tasks)


def section_counts(patients: pd.DataFrame, sections: Iterable[str]) -> dict[str, int]:
    return {section: int((patients.patient_section == section).sum()) for section in sections}


def readmission_outcome_cohorts(patients: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return episode cohorts using the already-derived readmission window."""
    observed = patients.readmission_window
    return {
        "Readmission within 30 days": patients[observed == "Readmission within 30 days"],
        "Readmission 31–90 days": patients[observed == "Readmission within 31–90 days"],
        "No readmission observed to date": patients[observed == "First recorded hospitalization"],
    }
