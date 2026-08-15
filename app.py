"""Streamlit entry point for the Stroke Transitions of Care Clinic dashboard."""

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from stcc_logic import derive_workflow, load_data


DATA_FILE = Path(__file__).with_name("stroke_transitions_of_care_clinic_synthetic_updated.csv")
SECTION_LABELS = {
    "Active STCC Queue": "Appointment Needed",
    "Post-Visit Care-Gap Queue": "Follow-Up Needs",
    "Closed Loop / Completed": "Completed",
}

st.set_page_config(
    page_title="Stroke Transitions of Care Clinic Navigator", page_icon="🧠", layout="wide"
)
st.markdown(
    """
<style>
    :root {--blue:#243b83; --blue2:#4056a1; --burgundy:#7a2645; --ink:#17223b; --muted:#5e6779; --surface:#f5f7fb;}
    .block-container {padding-top: 1.8rem; padding-bottom: 3rem; max-width: 1500px;}
    h1, h2, h3, h4 {color:var(--ink); letter-spacing:-.015em;}
    h1 {color:var(--blue); margin-bottom:.15rem;}
    [data-testid="stSidebar"] {background:#f7f8fc; border-right:1px solid #e4e7ef;}
    [data-testid="stSidebar"] h2 {color:var(--blue);}
    .intro-kicker {font-size:1.22rem; font-weight:650; color:var(--burgundy); margin:.15rem 0 .45rem;}
    .intro-copy {color:#485266; max-width:880px; font-size:1rem; margin-bottom:1.4rem;}
    .flow-label {font-size:.75rem; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); font-weight:700;}
    .flow-value {font-size:1.75rem; line-height:1.15; color:var(--blue); font-weight:750;}
    .flow-card {background:white; border:1px solid #dfe3ec; border-top:4px solid var(--blue); border-radius:10px; padding:14px 16px; min-height:95px; box-shadow:0 2px 8px #17223b0b;}
    .flow-arrow {text-align:center; color:#7b8495; font-size:1.5rem; padding-top:28px;}
    .flow-branch {background:var(--surface); border:1px solid #e0e4ed; border-radius:12px; padding:14px 16px; margin:12px 0 22px;}
    .branch-title {color:var(--blue); font-weight:700; margin-bottom:10px;}
    .priority-grid {display:grid; grid-template-columns:repeat(3,1fr); gap:10px;}
    .priority {border-radius:8px; padding:11px 13px; background:white; border-left:6px solid;}
    .priority.immediate {border-color:var(--burgundy); background:#fbf3f6;}
    .priority.action {border-color:#4056a1; background:#f2f4fb;}
    .priority.track {border-color:#8290bd;}
    .priority strong {display:block; color:var(--ink);}
    .priority span {font-size:1.35rem; font-weight:750; color:var(--blue);}
    .fixed-context {display:inline-block; background:#eef1f8; border:1px solid #d9deeb; color:#34436f; border-radius:999px; padding:5px 11px; margin:0 7px 10px 0; font-size:.88rem; font-weight:600;}
    .section-count {color:var(--muted); margin:.2rem 0 .75rem;}
    div[data-baseweb="tab-list"] {gap:.2rem; border-bottom:1px solid #dfe3ec;}
    button[data-baseweb="tab"] {color:#4a5366; font-weight:600; padding-left:.9rem; padding-right:.9rem;}
    button[data-baseweb="tab"][aria-selected="true"] {color:var(--blue);}
    @media(max-width:800px) {.priority-grid {grid-template-columns:1fr;} .flow-arrow {display:none;}}
</style>
""",
    unsafe_allow_html=True,
)

st.title("Stroke Transitions of Care Clinic Navigator")
st.markdown('<div class="intro-kicker">Supporting timely follow-up after stroke discharge</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="intro-copy">The early post-discharge period is a high-risk time for readmission. '
    "This navigator helps the care team identify recently discharged stroke patients who need "
    "follow-up and coordinate their next steps.</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Before you begin:")
    uploaded = st.file_uploader(
        "Update recently discharged stroke patient data",
        type="csv",
        help="Leave empty to use the included patient data.",
    )
    as_of = st.date_input("Today’s date:", value=date(2026, 8, 13))
    target_days = st.number_input(
        "Target follow-up window (days)", min_value=1, max_value=60, value=14
    )
    escalation_days = st.number_input(
        "Flag unscheduled patients after (days)", min_value=1, max_value=30, value=7
    )
    st.divider()
    st.caption(
        "Status changes in this demonstration are temporary and do not alter the source patient data."
    )
    if st.button("Reset demo status changes", width="stretch"):
        st.session_state.demo_episode_updates = {}
        st.rerun()


def apply_demo_updates(frame: pd.DataFrame) -> pd.DataFrame:
    """Overlay session-only episode updates without modifying the loaded source data."""
    updated = frame.copy()
    for (patient_id, discharge_date), values in st.session_state.get(
        "demo_episode_updates", {}
    ).items():
        episode = (updated.patient_id == patient_id) & (
            updated.discharge_date.dt.strftime("%Y-%m-%d") == discharge_date
        )
        for field, value in values.items():
            if field in updated.columns:
                updated.loc[episode, field] = value
    return updated

try:
    source = uploaded if uploaded is not None else DATA_FILE
    source_raw = load_data(source)
    raw = apply_demo_updates(source_raw)
    eligible_raw = raw[raw.stcc_eligible == "Yes"].copy()
    patients, tasks = derive_workflow(
        eligible_raw, as_of, int(target_days), int(escalation_days)
    )
except (ValueError, OSError, pd.errors.ParserError) as exc:
    st.error(f"Could not load the patient data: {exc}")
    st.stop()


def patient_number(patient_id: object) -> str:
    """Return a clinician-friendly identifier without changing the stored ID."""
    value = str(patient_id)
    if value.upper().startswith("STCC-"):
        value = value[5:]
    return value


def episode_label(patient_id: object, discharge_date: object) -> str:
    """Distinguish repeated transitions while keeping the patient identifier familiar."""
    discharged = pd.Timestamp(discharge_date).strftime("%b %d, %Y")
    return f"Patient {patient_number(patient_id)} · discharged {discharged}"


active = patients[patients.patient_section == "Active STCC Queue"]
post_visit = patients[patients.patient_section == "Post-Visit Care-Gap Queue"]
completed = patients[patients.patient_section == "Closed Loop / Completed"]
active_episodes = patients[patients.patient_section != "Closed Loop / Completed"]
readmissions_30 = patients[patients.readmission_window == "Readmission within 30 days"]
readmissions_90 = patients[patients.readmission_window == "Readmission within 31–90 days"]

st.markdown("### Patient overview")
overview = st.columns([1, .16, 1, .16, 1, .16, 1])
flow_values = [
    ("STCC eligible active episodes", len(active_episodes)),
    ("Appointment / visit needed", len(active)),
    ("Visit completed — tasks pending", len(post_visit)),
    ("Transition complete", len(completed)),
]
for index, (label, value) in enumerate(flow_values):
    card_index = index * 2
    overview[card_index].markdown(
        f'<div class="flow-card"><div class="flow-label">{label}</div>'
        f'<div class="flow-value">{value:,}</div></div>',
        unsafe_allow_html=True,
    )
    if index < len(flow_values) - 1:
        overview[card_index + 1].markdown('<div class="flow-arrow">→</div>', unsafe_allow_html=True)

st.markdown(
    f"""
<div class="flow-branch">
  <div class="branch-title">Appointment needed — priority</div>
  <div class="priority-grid">
    <div class="priority immediate"><strong>Immediate Action Required</strong><span>{int((active.workflow_category == 'Immediate Action Required').sum()):,}</span></div>
    <div class="priority action"><strong>Action Needed</strong><span>{int((active.workflow_category == 'Action Needed').sum()):,}</span></div>
    <div class="priority track"><strong>On Track</strong><span>{int((active.workflow_category == 'On Track').sum()):,}</span></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)
readmission_columns = st.columns(2)
readmission_columns[0].markdown(
    f'<div class="flow-card"><div class="flow-label">Readmissions within 30 days</div><div class="flow-value">{len(readmissions_30):,}</div></div>',
    unsafe_allow_html=True,
)
readmission_columns[1].markdown(
    f'<div class="flow-card"><div class="flow-label">Readmissions within 31–90 days</div><div class="flow-value">{len(readmissions_90):,}</div></div>',
    unsafe_allow_html=True,
)
st.caption(f"Current as of **{as_of:%B %d, %Y}**")

active_tab, post_tab, tasks_tab, closed_tab, rules_tab = st.tabs(
    [
        "Appointment Needed",
        "Follow-Up Needs",
        "Care Team Tasks",
        "Completed",
        "How Patients Are Prioritized",
    ]
)


def render_context(*items: str) -> None:
    st.markdown(
        "".join(f'<span class="fixed-context">{item}</span>' for item in items),
        unsafe_allow_html=True,
    )


def patient_search(frame: pd.DataFrame, key: str) -> pd.DataFrame:
    query = st.text_input("Find patient", key=f"search_{key}").strip()
    if not query:
        return frame
    normalized = frame.patient_id.map(patient_number)
    return frame[
        frame.patient_id.str.contains(query, case=False, na=False)
        | normalized.str.contains(query, case=False, na=False)
    ]


def appointment_filters(frame: pd.DataFrame, key: str) -> pd.DataFrame:
    c1, c2, c3 = st.columns([1.3, 1.3, 2])
    categories = c1.multiselect(
        "Priority",
        ["Immediate Action Required", "Action Needed", "On Track"],
        key=f"cat_{key}",
    )
    statuses = c2.multiselect(
        "Appointment status", sorted(frame.appointment_status.unique()), key=f"status_{key}"
    )
    query = c3.text_input("Find patient", key=f"search_{key}").strip()
    result = frame
    if categories:
        result = result[result.workflow_category.isin(categories)]
    if statuses:
        result = result[result.appointment_status.isin(statuses)]
    if query:
        normalized = result.patient_id.map(patient_number)
        result = result[
            result.patient_id.str.contains(query, case=False, na=False)
            | normalized.str.contains(query, case=False, na=False)
        ]
    return result


def render_status_update(row: pd.Series, key: str) -> None:
    """Collect session-only fact updates and let deterministic logic recalculate status."""
    episode_key = (row.patient_id, row.discharge_date.strftime("%Y-%m-%d"))
    form_key = f"update_{key}_{row.patient_id}_{episode_key[1]}"
    current_status = row.appointment_status
    scheduling_statuses = ["Not scheduled", "Scheduled", "Cancelled", "No-show"]
    default_status = current_status if current_status in scheduling_statuses else (
        "Scheduled" if pd.notna(row.appointment_date) else "Not scheduled"
    )

    st.markdown("#### Update patient status")
    st.caption(
        "Demo changes are stored only for this session. Priority and patient status are recalculated automatically."
    )
    with st.form(form_key):
        appointment_column, task_column = st.columns(2)
        with appointment_column:
            appointment_status = st.selectbox(
                "Appointment status",
                scheduling_statuses,
                index=scheduling_statuses.index(default_status),
                key=f"appointment_status_{form_key}",
            )
            appointment_value = (
                row.appointment_date.date() if pd.notna(row.appointment_date) else None
            )
            appointment_date = st.date_input(
                "Appointment date", value=appointment_value, key=f"appointment_date_{form_key}"
            )
            visit_completed = st.checkbox(
                "Clinic visit completed",
                value=current_status == "Completed",
                key=f"visit_completed_{form_key}",
            )
        with task_column:
            med_reconciliation = st.checkbox(
                "Medication reconciliation completed",
                value=row.med_reconciliation_completed == "Yes",
                key=f"med_reconciliation_{form_key}",
            )
            prevention_plan = st.checkbox(
                "Secondary prevention plan documented",
                value=row.secondary_prevention_plan_documented == "Yes",
                key=f"prevention_plan_{form_key}",
            )
            pcp_followup = st.checkbox(
                "PCP follow-up arranged",
                value=row.pcp_followup_arranged == "Yes",
                key=f"pcp_followup_{form_key}",
            )
            conditional_updates: dict[str, bool] = {}
            if row.cardiac_monitoring_needed == "Yes":
                conditional_updates["cardiac_monitoring_completed"] = st.checkbox(
                    "Cardiac monitoring completed",
                    value=row.cardiac_monitoring_completed == "Yes",
                    key=f"cardiac_monitoring_{form_key}",
                )
            if row.other_workup_needed == "Yes":
                conditional_updates["other_workup_completed"] = st.checkbox(
                    "Other stroke workup completed",
                    value=row.other_workup_completed == "Yes",
                    key=f"other_workup_{form_key}",
                )
            if row.rehab_needed == "Yes":
                conditional_updates["rehab_arranged"] = st.checkbox(
                    "Rehabilitation arranged",
                    value=row.rehab_arranged == "Yes",
                    key=f"rehab_arranged_{form_key}",
                )
                conditional_updates["rehab_completed"] = st.checkbox(
                    "Rehabilitation completed",
                    value=row.rehab_completed == "Yes",
                    key=f"rehab_completed_{form_key}",
                )
            if row.specialty_referral_needed == "Yes":
                conditional_updates["specialty_referral_completed"] = st.checkbox(
                    "Specialty referral completed",
                    value=row.specialty_referral_completed == "Yes",
                    key=f"specialty_referral_{form_key}",
                )
            barrier_updates: dict[str, bool] = {}
            barrier_labels = {
                "transportation_barrier": "Transportation need resolved",
                "housing_instability": "Housing need resolved",
                "food_insecurity": "Food-support need resolved",
                "economic_or_insurance_barrier": "Economic or insurance need resolved",
                "limited_caregiver_support": "Caregiver-support need resolved",
            }
            for field, label in barrier_labels.items():
                if row[field] == "Yes":
                    barrier_updates[field] = st.checkbox(
                        label, value=False, key=f"{field}_{form_key}"
                    )

        saved = st.form_submit_button("Save status update", type="primary")
        if saved:
            if appointment_status == "Scheduled" and appointment_date is None and not visit_completed:
                st.error("Add an appointment date before saving a scheduled appointment.")
            else:
                values = {
                    "appointment_status": "Completed" if visit_completed else appointment_status,
                    "appointment_date": pd.Timestamp(appointment_date) if appointment_date else pd.NaT,
                    "med_reconciliation_completed": "Yes" if med_reconciliation else "No",
                    "secondary_prevention_plan_documented": "Yes" if prevention_plan else "No",
                    "pcp_followup_arranged": "Yes" if pcp_followup else "No",
                }
                values.update(
                    {field: "Yes" if complete else "No" for field, complete in conditional_updates.items()}
                )
                values.update(
                    {field: "No" if resolved else "Yes" for field, resolved in barrier_updates.items()}
                )
                updates = st.session_state.setdefault("demo_episode_updates", {})
                updates[episode_key] = values
                st.rerun()


def render_patient_list(frame: pd.DataFrame, key: str, *, appointment_controls: bool = False) -> None:
    filtered = appointment_filters(frame, key) if appointment_controls else patient_search(frame, key)
    st.markdown(f'<div class="section-count"><b>{len(filtered):,}</b> patients</div>', unsafe_allow_html=True)
    display = filtered.copy()
    display["patient_id"] = display.patient_id.map(lambda value: f"Patient {patient_number(value)}")
    display["primary_reason"] = display.primary_reason.str.replace("STCC", "stroke clinic", regex=False)
    if key == "closed":
        display["workflow_category"] = "Completed"
    columns = [
        "workflow_state", "workflow_category", "patient_id", "appointment_status", "admission_date", "discharge_date",
        "days_since_discharge", "appointment_date", "days_until_appointment", "primary_reason",
        "unresolved_task_count", "recorded_barrier_count", "stroke_type", "nihss", "mrs",
        "discharge_disposition", "readmission_window",
    ]
    st.dataframe(
        display[columns], width="stretch", hide_index=True,
        column_config={
            "workflow_state": "Patient status", "workflow_category": "Priority", "patient_id": "Patient",
            "appointment_status": "Appointment status",
            "admission_date": st.column_config.DateColumn("Admitted"),
            "discharge_date": st.column_config.DateColumn("Discharged"),
            "days_since_discharge": "Days since discharge",
            "appointment_date": st.column_config.DateColumn("Appointment date"),
            "days_until_appointment": "Days until appointment",
            "primary_reason": "Why attention is needed", "unresolved_task_count": "Tasks",
            "recorded_barrier_count": "Barriers", "stroke_type": "Stroke type", "nihss": "NIHSS",
            "mrs": "mRS", "discharge_disposition": "Disposition",
            "readmission_window": "Hospitalization history",
        },
    )
    if filtered.empty:
        return
    episode_options = list(filtered[["patient_id", "discharge_date"]].itertuples(index=False, name=None))
    selected_id, selected_discharge = st.selectbox(
        "Patient detail", episode_options,
        format_func=lambda value: episode_label(value[0], value[1]),
        key=f"patient_{key}",
    )
    row = filtered.loc[
        (filtered.patient_id == selected_id) & (filtered.discharge_date == selected_discharge)
    ].iloc[0]
    heading_context = row.workflow_category
    if row.patient_section == "Closed Loop / Completed":
        heading_context = "Completed"
    st.subheader(f"Patient {patient_number(row.patient_id)} · {heading_context}")
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("#### Why this patient is here")
        st.info(str(row.primary_reason).replace("STCC", "stroke clinic"))
        st.markdown("#### Outstanding needs")
        patient_tasks = tasks[
            (tasks.patient_id == selected_id) & (tasks.discharge_date == selected_discharge)
        ]
        if patient_tasks.empty:
            st.success("No outstanding transition needs.")
        else:
            for _, task in patient_tasks.iterrows():
                gap = str(task.outstanding_task).replace("STCC", "Stroke clinic")
                action = str(task.recommended_action).replace("STCC", "stroke clinic")
                st.markdown(f"**{task.task_domain} — {gap}**  \n{action}")
    with right:
        st.markdown("#### Appointment timeline")
        appt = row.appointment_date.strftime("%b %d, %Y") if pd.notna(row.appointment_date) else "Not scheduled"
        st.write(
            f"**Admitted:** {row.admission_date:%b %d, %Y}  \n"
            f"**Discharged:** {row.discharge_date:%b %d, %Y}  \n"
            f"**Status:** {row.appointment_status}  \n**Stroke clinic appointment:** {appt}  \n"
            f"**Days since discharge:** {row.days_since_discharge}  \n"
            f"**Hospitalization history:** {row.readmission_window}"
        )
        st.markdown("#### Clinical context")
        st.write(
            f"**{row.age}-year-old {str(row.sex).lower()}**  \n{row.stroke_type} · {row.stroke_etiology}  \n"
            f"NIHSS {row.nihss} · mRS {row.mrs}  \nDischarged to: {row.discharge_disposition}"
        )
    render_status_update(row, key)


with active_tab:
    st.header("Appointment Needed")
    st.write("Recently discharged stroke patients who still need to complete their stroke clinic visit.")
    render_patient_list(active, "active", appointment_controls=True)

with post_tab:
    st.header("Follow-Up Needs")
    st.write("The stroke clinic visit is complete, but one or more follow-up needs still require attention.")
    render_context("Appointment status: Completed")
    render_patient_list(post_visit, "post")

with tasks_tab:
    st.header("Care Team Tasks")
    st.write("View outstanding follow-up tasks and identify which care team needs to take the next step.")
    if tasks.empty:
        st.success("No outstanding tasks.")
    else:
        domain = st.selectbox("Care team", ["All care teams"] + sorted(tasks.task_domain.unique().tolist()))
        task_view = tasks if domain == "All care teams" else tasks[tasks.task_domain == domain]
        section_options = sorted(task_view.patient_section.unique())
        selected_groups = st.multiselect(
            "Patient group", section_options, format_func=lambda value: SECTION_LABELS.get(value, value)
        )
        if selected_groups:
            task_view = task_view[task_view.patient_section.isin(selected_groups)]
        task_display = task_view.copy()
        task_display["patient_id"] = task_display.patient_id.map(lambda value: f"Patient {patient_number(value)}")
        task_display["patient_section"] = task_display.patient_section.map(SECTION_LABELS)
        task_display["outstanding_task"] = task_display.outstanding_task.str.replace(
            "STCC", "Stroke clinic", regex=False
        )
        task_display["recommended_action"] = task_display.recommended_action.str.replace(
            "STCC", "stroke clinic", regex=False
        )
        task_display["workflow_category"] = task_display.apply(
            lambda row: (
                "Completed" if row.patient_section == "Completed" else row.workflow_category
            ),
            axis=1,
        )
        st.write(f"**{len(task_display):,} tasks**")
        st.dataframe(
            task_display, width="stretch", hide_index=True,
            column_config={
                "patient_id": "Patient", "patient_section": "Patient group",
                "workflow_state": "Patient status", "workflow_category": "Priority",
                "appointment_status": "Appointment status",
                "discharge_date": st.column_config.DateColumn("Episode discharge"),
                "days_since_discharge": "Days since discharge", "task_domain": "Care team",
                "outstanding_task": "Outstanding task", "recommended_action": "Recommended next action",
            },
        )

with closed_tab:
    st.header("Completed")
    st.write("Patients who completed their stroke clinic visit and have no remaining documented transition needs.")
    render_context("Status: Completed", "Transition needs: Complete")
    render_patient_list(completed, "closed")

with rules_tab:
    st.header("How Patients Are Prioritized")
    st.markdown(
        f"""
**Immediate Action Required**

The visit was cancelled or missed, a scheduled date has passed without completion, the patient
remains unscheduled more than **{escalation_days} days** after discharge, or needs across multiple
care areas and an access barrier require coordination.

**Action Needed**

The patient has another scheduling or transition need, including an appointment outside the
**{target_days}-day** target follow-up window.

**On Track**

The patient is scheduled within the target window and has no pre-visit action needed.

After a stroke clinic visit, patients with remaining needs move to **Follow-Up Needs**. Patients
with no remaining needs move to **Completed**.
"""
    )
