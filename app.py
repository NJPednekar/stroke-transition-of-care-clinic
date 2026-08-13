"""Streamlit entry point for the Stroke Transitions of Care Clinic dashboard."""

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from stcc_logic import derive_workflow, load_data


DATA_FILE = Path(__file__).with_name("stroke_transitions_of_care_clinic_synthetic_updated.csv")
SECTIONS = ["Active STCC Queue", "Post-Visit Care-Gap Queue", "Alternative Transition Pathway", "Closed Loop / Completed"]

st.set_page_config(page_title="STCC Prioritization Dashboard", page_icon="🧠", layout="wide")
st.markdown("""
<style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    [data-testid="stMetric"] {background: #f5f8fb; border: 1px solid #dce5ec; border-radius: 12px; padding: 14px;}
    .prototype-note {background:#eef6ff; border-left:5px solid #2463a0; padding:12px 16px; border-radius:6px; margin-bottom:18px;}
    .context-note {color:#52606d; font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

st.title("Stroke Transitions of Care Clinic")
st.caption("Prioritization Dashboard · transparent workflow support for recently discharged stroke patients")
st.markdown('<div class="prototype-note"><b>Synthetic educational prototype.</b> Categories organize operational work; they are not a validated clinical risk score, prediction model, or substitute for clinical judgment.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Queue controls")
    uploaded = st.file_uploader("Use another STCC CSV", type="csv", help="Leave empty to use the included synthetic dataset.")
    as_of = st.date_input("Effective date", value=date(2026, 8, 13))
    target_days = st.number_input("Target follow-up window (days)", min_value=1, max_value=60, value=14)
    escalation_days = st.number_input("Unscheduled outreach threshold (days)", min_value=1, max_value=30, value=7)
    st.divider()
    st.caption("Thresholds are configurable workflow assumptions for this prototype.")

try:
    source = uploaded if uploaded is not None else DATA_FILE
    raw = load_data(source)
    patients, tasks = derive_workflow(raw, as_of, int(target_days), int(escalation_days))
except (ValueError, OSError, pd.errors.ParserError) as exc:
    st.error(f"Could not load the dataset: {exc}")
    st.stop()

active = patients[patients.patient_section == "Active STCC Queue"]
metrics = st.columns(7)
metric_values = [
    ("Active STCC", len(active)),
    ("Immediate", (active.workflow_category == "Immediate Action Required").sum()),
    ("Action needed", (active.workflow_category == "Action Needed").sum()),
    ("On track", (active.workflow_category == "On Track").sum()),
    ("Post-visit gaps", (patients.patient_section == "Post-Visit Care-Gap Queue").sum()),
    ("Alternate pathway", (patients.patient_section == "Alternative Transition Pathway").sum()),
    ("Closed loop", (patients.patient_section == "Closed Loop / Completed").sum()),
]
for container, (label, value) in zip(metrics, metric_values):
    container.metric(label, int(value))

st.caption(f"Effective date: **{as_of:%B %d, %Y}** · {len(raw):,} records loaded · operational counts are based on documented CSV fields")

active_tab, post_tab, tasks_tab, alternate_tab, closed_tab, rules_tab = st.tabs([
    "Active STCC", "Post-Visit Gaps", "Task Work Queues", "Alternative Pathway", "Closed Loop", "How it works"
])

def queue_filters(frame: pd.DataFrame, key: str) -> pd.DataFrame:
    """Render compact filters and return the filtered patient frame."""
    c1, c2, c3 = st.columns([1.3, 1.3, 2])
    categories = c1.multiselect("Workflow category", sorted(frame.workflow_category.unique()), key=f"cat_{key}")
    statuses = c2.multiselect("Appointment status", sorted(frame.appointment_status.unique()), key=f"status_{key}")
    query = c3.text_input("Find patient ID", key=f"search_{key}").strip()
    result = frame
    if categories:
        result = result[result.workflow_category.isin(categories)]
    if statuses:
        result = result[result.appointment_status.isin(statuses)]
    if query:
        result = result[result.patient_id.str.contains(query, case=False, na=False)]
    return result

def render_patient_queue(frame: pd.DataFrame, key: str) -> None:
    filtered = queue_filters(frame, key)
    st.write(f"**{len(filtered):,} patients**")
    columns = ["workflow_category", "patient_id", "appointment_status", "discharge_date", "days_since_discharge",
               "appointment_date", "days_until_appointment", "primary_reason", "unresolved_task_count",
               "recorded_barrier_count", "stroke_type", "nihss", "mrs", "discharge_disposition"]
    st.dataframe(filtered[columns], use_container_width=True, hide_index=True, column_config={
        "workflow_category": "Workflow category", "patient_id": "Patient", "appointment_status": "Appointment",
        "discharge_date": st.column_config.DateColumn("Discharged"), "days_since_discharge": "Days since discharge",
        "appointment_date": st.column_config.DateColumn("Appointment date"), "days_until_appointment": "Days until appointment",
        "primary_reason": "Why attention is needed", "unresolved_task_count": "Tasks", "recorded_barrier_count": "Barriers",
        "stroke_type": "Stroke type", "nihss": "NIHSS", "mrs": "mRS", "discharge_disposition": "Disposition",
    })
    if filtered.empty:
        return
    selected_id = st.selectbox("Patient detail", filtered.patient_id.tolist(), key=f"patient_{key}")
    row = filtered.loc[filtered.patient_id == selected_id].iloc[0]
    st.subheader(f"{row.patient_id} · {row.workflow_category}")
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("#### Why this patient is here")
        st.info(row.primary_reason)
        st.markdown("#### Outstanding needs")
        patient_tasks = tasks[tasks.patient_id == selected_id]
        if patient_tasks.empty:
            st.success("No documented outstanding transition needs.")
        else:
            for _, task in patient_tasks.iterrows():
                st.markdown(f"**{task.task_domain} — {task.outstanding_task}**  \n{task.recommended_action}")
    with right:
        st.markdown("#### Appointment timeline")
        appt = row.appointment_date.strftime("%b %d, %Y") if pd.notna(row.appointment_date) else "Not scheduled"
        st.write(f"**Discharged:** {row.discharge_date:%b %d, %Y}  \n**Status:** {row.appointment_status}  \n**Appointment:** {appt}  \n**Days since discharge:** {row.days_since_discharge}")
        st.markdown("#### Clinical context")
        st.write(f"**{row.age}-year-old {str(row.sex).lower()}**  \n{row.stroke_type} · {row.stroke_etiology}  \nNIHSS {row.nihss} · mRS {row.mrs}  \nDischarged to: {row.discharge_disposition}")
        st.markdown('<p class="context-note">Clinical variables provide context and do not independently determine workflow category.</p>', unsafe_allow_html=True)

with active_tab:
    st.header("Active STCC Queue")
    st.write("Eligible patients whose STCC visit has not been completed. Appointment status and timing lead the workflow category.")
    render_patient_queue(active, "active")

with post_tab:
    st.header("Post-Visit Care-Gap Queue")
    st.write("The STCC visit is complete, but documented transition tasks or recorded barriers still require follow-up.")
    render_patient_queue(patients[patients.patient_section == "Post-Visit Care-Gap Queue"], "post")

with tasks_tab:
    st.header("Task Work Queues")
    st.write("One patient may appear in multiple queues so each team member can find work in their domain.")
    if tasks.empty:
        st.success("No outstanding tasks.")
    else:
        domain = st.selectbox("Task domain", ["All domains"] + sorted(tasks.task_domain.unique().tolist()))
        task_view = tasks if domain == "All domains" else tasks[tasks.task_domain == domain]
        section_filter = st.multiselect("Patient section", sorted(task_view.patient_section.unique()))
        if section_filter:
            task_view = task_view[task_view.patient_section.isin(section_filter)]
        st.write(f"**{len(task_view):,} tasks**")
        st.dataframe(task_view, use_container_width=True, hide_index=True, column_config={
            "patient_id": "Patient", "patient_section": "Patient queue", "workflow_category": "Workflow category",
            "appointment_status": "Appointment", "days_since_discharge": "Days since discharge",
            "task_domain": "Team workflow", "outstanding_task": "Outstanding task", "recommended_action": "Recommended next action",
        })

with alternate_tab:
    st.header("Alternative Transition Pathway")
    st.write("Patients documented as not eligible for STCC. Confirm and route outstanding needs through the appropriate pathway.")
    render_patient_queue(patients[patients.patient_section == "Alternative Transition Pathway"], "alternate")

with closed_tab:
    st.header("Closed Loop / Completed")
    st.write("The STCC visit and all documented transition requirements are complete. Records remain available for review but are removed from active work.")
    render_patient_queue(patients[patients.patient_section == "Closed Loop / Completed"], "closed")

with rules_tab:
    st.header("Transparent workflow rules")
    st.markdown(f"""
**Immediate Action Required** when the visit was cancelled or recorded as a no-show, a scheduled date passed without completion, the patient remains unscheduled more than **{escalation_days} days** after discharge, or multiple care domains and an access barrier require coordination.

**Action Needed** when the patient has another scheduling or transition task, including an appointment outside the **{target_days}-day** target window.

**On Track** when an eligible patient is scheduled within the target window and has no documented pre-visit action.

Completed visits with remaining needs move to **Post-Visit Care-Gap Queue**. Completed visits with no remaining documented needs move to **Closed Loop**. Ineligible patients move to **Alternative Transition Pathway**.

Task and barrier counts are operational sorting aids representing documented workload—not measures of clinical risk. A recorded social barrier is treated as a status-confirmation task because the CSV does not contain barrier-resolution fields.
""")
