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
    "Alternative Transition Pathway": "Other Transition Pathway",
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

try:
    source = uploaded if uploaded is not None else DATA_FILE
    raw = load_data(source)
    patients, tasks = derive_workflow(raw, as_of, int(target_days), int(escalation_days))
except (ValueError, OSError, pd.errors.ParserError) as exc:
    st.error(f"Could not load the patient data: {exc}")
    st.stop()


def patient_number(patient_id: object) -> str:
    """Return a clinician-friendly identifier without changing the stored ID."""
    value = str(patient_id)
    if value.upper().startswith("STCC-"):
        value = value[5:]
    return value


active = patients[patients.patient_section == "Active STCC Queue"]
post_visit = patients[patients.patient_section == "Post-Visit Care-Gap Queue"]
alternate = patients[patients.patient_section == "Alternative Transition Pathway"]
completed = patients[patients.patient_section == "Closed Loop / Completed"]
eligible = patients[patients.stcc_eligible == "Yes"]
completed_visits = patients[
    (patients.stcc_eligible == "Yes") & (patients.appointment_status == "Completed")
]

st.markdown("### Patient overview")
overview = st.columns([1, .16, 1, .16, 1, .16, 1, .16, 1])
flow_values = [
    ("Total stroke patients", len(patients)),
    ("Stroke clinic eligible", len(eligible)),
    ("Clinic visit completed", len(completed_visits)),
    ("Appointment needed", len(active)),
    ("Other transition pathway", len(alternate)),
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
completed_columns = st.columns(2)
completed_columns[0].markdown(
    f'<div class="flow-card"><div class="flow-label">Visit completed — follow-up needs remain</div><div class="flow-value">{len(post_visit):,}</div></div>',
    unsafe_allow_html=True,
)
completed_columns[1].markdown(
    f'<div class="flow-card"><div class="flow-label">Visit completed — no remaining needs</div><div class="flow-value">{len(completed):,}</div></div>',
    unsafe_allow_html=True,
)
st.caption(f"Current as of **{as_of:%B %d, %Y}**")

active_tab, post_tab, tasks_tab, alternate_tab, closed_tab, rules_tab = st.tabs(
    [
        "Appointment Needed",
        "Follow-Up Needs",
        "Care Team Tasks",
        "Other Transition Pathway",
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


def render_patient_list(frame: pd.DataFrame, key: str, *, appointment_controls: bool = False) -> None:
    filtered = appointment_filters(frame, key) if appointment_controls else patient_search(frame, key)
    st.markdown(f'<div class="section-count"><b>{len(filtered):,}</b> patients</div>', unsafe_allow_html=True)
    display = filtered.copy()
    display["patient_id"] = display.patient_id.map(lambda value: f"Patient {patient_number(value)}")
    display["primary_reason"] = display.primary_reason.str.replace("STCC", "stroke clinic", regex=False)
    if key == "alternate":
        display["workflow_category"] = "Other Transition Pathway"
    elif key == "closed":
        display["workflow_category"] = "Completed"
    columns = [
        "workflow_category", "patient_id", "appointment_status", "discharge_date",
        "days_since_discharge", "appointment_date", "days_until_appointment", "primary_reason",
        "unresolved_task_count", "recorded_barrier_count", "stroke_type", "nihss", "mrs",
        "discharge_disposition",
    ]
    st.dataframe(
        display[columns], use_container_width=True, hide_index=True,
        column_config={
            "workflow_category": "Priority", "patient_id": "Patient",
            "appointment_status": "Appointment status",
            "discharge_date": st.column_config.DateColumn("Discharged"),
            "days_since_discharge": "Days since discharge",
            "appointment_date": st.column_config.DateColumn("Appointment date"),
            "days_until_appointment": "Days until appointment",
            "primary_reason": "Why attention is needed", "unresolved_task_count": "Tasks",
            "recorded_barrier_count": "Barriers", "stroke_type": "Stroke type", "nihss": "NIHSS",
            "mrs": "mRS", "discharge_disposition": "Disposition",
        },
    )
    if filtered.empty:
        return
    id_options = filtered.patient_id.tolist()
    selected_id = st.selectbox(
        "Patient detail", id_options, format_func=lambda value: f"Patient {patient_number(value)}",
        key=f"patient_{key}",
    )
    row = filtered.loc[filtered.patient_id == selected_id].iloc[0]
    heading_context = row.workflow_category
    if row.patient_section == "Alternative Transition Pathway":
        heading_context = "Other Transition Pathway"
    elif row.patient_section == "Closed Loop / Completed":
        heading_context = "Completed"
    st.subheader(f"Patient {patient_number(row.patient_id)} · {heading_context}")
    left, right = st.columns([1.15, 1])
    with left:
        st.markdown("#### Why this patient is here")
        st.info(str(row.primary_reason).replace("STCC", "stroke clinic"))
        st.markdown("#### Outstanding needs")
        patient_tasks = tasks[tasks.patient_id == selected_id]
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
            f"**Discharged:** {row.discharge_date:%b %d, %Y}  \n"
            f"**Status:** {row.appointment_status}  \n**Stroke clinic appointment:** {appt}  \n"
            f"**Days since discharge:** {row.days_since_discharge}"
        )
        st.markdown("#### Clinical context")
        st.write(
            f"**{row.age}-year-old {str(row.sex).lower()}**  \n{row.stroke_type} · {row.stroke_etiology}  \n"
            f"NIHSS {row.nihss} · mRS {row.mrs}  \nDischarged to: {row.discharge_disposition}"
        )


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
                "Other Transition Pathway"
                if row.patient_section == "Other Transition Pathway"
                else "Completed" if row.patient_section == "Completed" else row.workflow_category
            ),
            axis=1,
        )
        st.write(f"**{len(task_display):,} tasks**")
        st.dataframe(
            task_display, use_container_width=True, hide_index=True,
            column_config={
                "patient_id": "Patient", "patient_section": "Patient group",
                "workflow_category": "Priority", "appointment_status": "Appointment status",
                "days_since_discharge": "Days since discharge", "task_domain": "Care team",
                "outstanding_task": "Outstanding task", "recommended_action": "Recommended next action",
            },
        )

with alternate_tab:
    st.header("Other Transition Pathway")
    st.write("Patients who are not eligible for the stroke clinic and need follow-up through another appropriate care pathway.")
    render_context("Patient group: Other Transition Pathway")
    render_patient_list(alternate, "alternate")

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
with no remaining needs move to **Completed**. Patients who are not eligible for the stroke clinic
move to **Other Transition Pathway**.
"""
    )
