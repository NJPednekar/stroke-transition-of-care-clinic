"""Streamlit interface for the Stroke Transitions of Care Clinic Navigator."""

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from stcc_logic import derive_workflow, load_data


DATA_FILE = Path(__file__).with_name("stroke_transitions_of_care_clinic_synthetic_updated.csv")
BARRIER_LABELS = {
    "transportation_barrier": "Transportation",
    "housing_instability": "Housing stability",
    "food_insecurity": "Food access",
    "economic_or_insurance_barrier": "Economic or insurance access",
    "limited_caregiver_support": "Caregiver support",
}

st.set_page_config(
    page_title="Stroke Transitions of Care Clinic Navigator", page_icon="🧠", layout="wide"
)
st.markdown(
    """
<style>
:root {--blue:#243b83;--blue2:#4056a1;--burgundy:#7a2645;--ink:#17223b;--muted:#667085;--line:#e2e6ef;--surface:#f7f8fb;}
.block-container {padding-top:2rem;padding-bottom:4rem;max-width:1380px;}
[data-testid="stSidebar"] {background:#f8f9fc;border-right:1px solid #e8eaf0;}
[data-testid="stSidebar"] h2 {color:var(--blue);font-size:1.05rem;}
h1,h2,h3,h4 {color:var(--ink);letter-spacing:-.025em;}
.hero {position:relative;padding:1.7rem 0 2.6rem;max-width:960px;}
.eyebrow,.section-label {color:var(--blue);font-size:.73rem;font-weight:750;letter-spacing:.14em;text-transform:uppercase;}
.hero h1 {color:var(--blue);font-size:3.25rem;line-height:1.02;margin:.65rem 0 1.15rem;max-width:760px;}
.hero-lead {color:var(--burgundy);font-size:1.35rem;font-weight:650;margin-bottom:.65rem;}
.hero-copy {color:#566074;font-size:1.02rem;line-height:1.65;max-width:850px;}
.section-head {margin-top:2.6rem;margin-bottom:.85rem;}
.section-title {font-size:1.25rem;font-weight:720;color:var(--ink);margin-top:.3rem;}
.section-subtitle {color:var(--muted);font-size:.92rem;margin-top:.25rem;}
div[data-testid="stButton"] > button {min-height:98px;border:1px solid #d9deea;background:white;color:var(--ink);border-radius:9px;box-shadow:0 2px 10px rgba(23,34,59,.035);font-weight:650;white-space:pre-line;transition:all .15s ease;}
div[data-testid="stButton"] > button:hover {border-color:var(--blue2);color:var(--blue);box-shadow:0 7px 20px rgba(36,59,131,.09);transform:translateY(-1px);}
div[data-testid="stButton"] > button[kind="primary"] {background:var(--blue);border-color:var(--blue);color:white;}
[data-testid="stSidebar"] div[data-testid="stButton"] > button,.quiet-actions div[data-testid="stButton"] > button {min-height:2.6rem;}
.cohort-shell {border-top:1px solid var(--line);margin-top:2.8rem;padding-top:2rem;}
.cohort-kicker {color:var(--blue);font-size:.72rem;font-weight:750;letter-spacing:.12em;text-transform:uppercase;}
.cohort-title {font-size:1.65rem;font-weight:720;color:var(--ink);margin:.3rem 0 .25rem;}
.cohort-meta {color:var(--muted);font-size:.92rem;margin-bottom:1rem;}
.snapshot-head {border-top:1px solid var(--line);margin-top:2.3rem;padding-top:2rem;}
.snapshot-id {font-size:2rem;font-weight:740;color:var(--blue);margin:.25rem 0;}
.snapshot-meta {color:var(--muted);font-size:.92rem;}
.status-line {margin:1.2rem 0 .9rem;padding:.8rem 1rem;border-left:4px solid var(--blue);background:#f6f7fb;}
.status-line.urgent {border-left-color:var(--burgundy);background:#fbf5f7;}
.status-name {font-size:.73rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase;color:var(--burgundy);}
.status-reason {color:var(--ink);font-weight:600;margin-top:.15rem;}
.progress-wrap {display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:1rem 0 1.7rem;}
.progress-step {padding:.65rem .75rem;border-top:3px solid #d8dce7;color:#7a8292;font-size:.82rem;font-weight:650;}
.progress-step.done {border-top-color:var(--blue);color:var(--blue);}
.progress-step.current {border-top-color:var(--burgundy);color:var(--burgundy);}
.module {border:1px solid var(--line);border-radius:9px;padding:1.1rem 1.2rem;min-height:150px;background:white;margin-bottom:.7rem;}
.module-label {font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--blue);font-weight:750;margin-bottom:.75rem;}
.module-value {font-size:1.12rem;color:var(--ink);font-weight:680;}
.module-copy {color:var(--muted);font-size:.88rem;line-height:1.5;margin-top:.3rem;}
.complete-note {border-left:4px solid var(--blue);background:#f3f5fb;padding:1rem 1.15rem;margin:1rem 0;color:var(--ink);}
[data-testid="stDataFrame"] {border:1px solid var(--line);border-radius:8px;overflow:hidden;}
[data-testid="stExpander"] {border:1px solid var(--line);border-radius:8px;background:white;}
.small-note {color:var(--muted);font-size:.85rem;}
hr {border-color:var(--line);}
@media(max-width:800px){.hero h1{font-size:2.4rem}.progress-wrap{grid-template-columns:1fr 1fr}.block-container{padding-top:1rem}}
</style>
""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Before you begin:")
    uploaded = st.file_uploader(
        "Update to recently discharged stroke patient data",
        type="csv",
        help="Leave empty to use the included patient data.",
    )
    as_of = st.date_input("Today’s date", value=date(2026, 8, 13))
    target_days = st.number_input(
        "Target follow-up window (days)", min_value=1, max_value=60, value=14
    )
    escalation_days = st.number_input(
        "Flag unscheduled patients after (days)", min_value=1, max_value=30, value=7
    )
    st.divider()
    st.caption("Changes made here are temporary and leave the original patient data unchanged.")
    if st.button("Reset status changes", width="stretch"):
        st.session_state.demo_episode_updates = {}
        st.session_state.pop("last_updated_episode", None)
        st.rerun()


def apply_demo_updates(frame: pd.DataFrame) -> pd.DataFrame:
    """Overlay session-only episode updates without modifying loaded source data."""
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
    value = str(patient_id)
    return value[5:] if value.upper().startswith("STCC-") else value


def episode_key(row: pd.Series) -> tuple[str, str]:
    return str(row.patient_id), row.discharge_date.strftime("%Y-%m-%d")


def episode_label(value: tuple[object, object]) -> str:
    return f"Patient {patient_number(value[0])} · discharged {pd.Timestamp(value[1]):%b %d, %Y}"


active = patients[patients.patient_section == "Active STCC Queue"]
post_visit = patients[patients.patient_section == "Post-Visit Care-Gap Queue"]
completed = patients[patients.patient_section == "Closed Loop / Completed"]
active_episodes = patients[patients.patient_section != "Closed Loop / Completed"]
readmissions_30 = patients[patients.readmission_window == "Readmission within 30 days"]
readmissions_90 = patients[patients.readmission_window == "Readmission within 31–90 days"]
repeat_ids = set(patients.loc[patients.patient_id.duplicated(False), "patient_id"])
no_readmission = patients[
    (patients.readmission_window == "First recorded hospitalization")
    & (~patients.patient_id.isin(repeat_ids))
]

st.markdown(
    """
<section class="hero">
  <div class="eyebrow">Stroke Transitions of Care</div>
  <h1>Stroke Transitions of Care<br>Clinic Navigator</h1>
  <div class="hero-lead">Helping the care team keep stroke patients on track after discharge.</div>
  <div class="hero-copy">The early post-discharge period is an important time for recovery and care coordination. The Navigator brings together clinic follow-up, outstanding care needs, and readmission outcomes so the team can quickly see what needs attention and what has been completed.</div>
</section>
""",
    unsafe_allow_html=True,
)

last_updated = st.session_state.get("last_updated_episode")
if last_updated:
    updated_row = patients[
        (patients.patient_id == last_updated[0])
        & (patients.discharge_date.dt.strftime("%Y-%m-%d") == last_updated[1])
    ]
    if not updated_row.empty and updated_row.iloc[0].workflow_state == "Visit Completed + Tasks Complete":
        st.markdown(
            '<div class="complete-note"><strong>✓ Transition complete</strong><br>'
            "All documented follow-up requirements have been completed.</div>",
            unsafe_allow_html=True,
        )


def choose_cohort(key: str) -> None:
    st.session_state.selected_cohort = key
    st.session_state.pop("selected_episode", None)


def tile_row(items: list[tuple[str, str, int]], prefix: str) -> None:
    columns = st.columns(len(items))
    for column, (key, label, count) in zip(columns, items):
        with column:
            selected = st.session_state.get("selected_cohort") == key
            st.button(
                f"{count:,}\n{label}", key=f"{prefix}_{key}",
                type="primary" if selected else "secondary", width="stretch",
                on_click=choose_cohort, args=(key,),
            )


st.markdown('<div class="section-head"><div class="section-label">Active Transitions</div><div class="section-title">Where each transition stands</div></div>', unsafe_allow_html=True)
tile_row(
    [
        ("active_all", "Active Episodes", len(active_episodes)),
        ("visit_needed", "Visit Needed", len(active)),
        ("tasks_pending", "Visit Complete · Tasks Pending", len(post_visit)),
        ("transition_complete", "Transition Complete", len(completed)),
    ],
    "active",
)

st.markdown('<div class="section-head"><div class="section-label">Needs Attention</div><div class="section-title">Appointment priorities</div></div>', unsafe_allow_html=True)
tile_row(
    [
        ("priority_immediate", "Immediate Action", int((active.workflow_category == "Immediate Action Required").sum())),
        ("priority_action", "Action Needed", int((active.workflow_category == "Action Needed").sum())),
        ("priority_track", "On Track", int((active.workflow_category == "On Track").sum())),
    ],
    "priority",
)

st.markdown('<div class="section-head"><div class="section-label">Readmission Outcomes</div><div class="section-title">Observed hospital utilization following stroke discharge.</div></div>', unsafe_allow_html=True)
tile_row(
    [
        ("readmit_30", "0–30 Day Readmissions", len(readmissions_30)),
        ("readmit_90", "31–90 Day Readmissions", len(readmissions_90)),
        ("no_readmission", "No Readmission Observed", len(no_readmission)),
    ],
    "readmission",
)
st.caption("Episodes without a subsequent hospitalization are described as no readmission observed to date; this does not imply 90 days of follow-up.")

quiet = st.columns([1, 1, 4])
with quiet[0]:
    st.button("Care Team Tasks", key="show_tasks", width="stretch", on_click=choose_cohort, args=("care_tasks",))
with quiet[1]:
    st.button("How prioritization works", key="show_rules", width="stretch", on_click=choose_cohort, args=("rules",))


COHORTS = {
    "active_all": ("Active Episodes", active_episodes, False),
    "visit_needed": ("Visit Needed", active, False),
    "tasks_pending": ("Visit Complete · Tasks Pending", post_visit, False),
    "transition_complete": ("Transition Complete", completed, False),
    "priority_immediate": ("Immediate Action", active[active.workflow_category == "Immediate Action Required"], False),
    "priority_action": ("Action Needed", active[active.workflow_category == "Action Needed"], False),
    "priority_track": ("On Track", active[active.workflow_category == "On Track"], False),
    "readmit_30": ("0–30 Day Readmissions", readmissions_30, True),
    "readmit_90": ("31–90 Day Readmissions", readmissions_90, True),
    "no_readmission": ("No Readmission Observed to Date", no_readmission, False),
}


def close_cohort() -> None:
    st.session_state.pop("selected_cohort", None)
    st.session_state.pop("selected_episode", None)


def cohort_table(frame: pd.DataFrame, readmission: bool) -> pd.DataFrame:
    view = frame.copy()
    view["patient_display"] = view.patient_id.map(lambda value: f"Patient {patient_number(value)}")
    if readmission:
        view["prior_discharge"] = view.admission_date - pd.to_timedelta(
            view.days_since_prior_discharge.fillna(0), unit="D"
        )
        return view[["patient_display", "prior_discharge", "admission_date", "days_since_prior_discharge", "readmission_window"]]
    return view[["patient_display", "discharge_date", "days_since_discharge", "appointment_status", "outstanding_needs"]]


def save_patient_update(
    row: pd.Series, appointment_status: str, appointment_date: object, visit_completed: bool,
    standard_updates: dict[str, bool], conditional_updates: dict[str, bool],
    barrier_updates: dict[str, bool],
) -> None:
    values = {
        "appointment_status": "Completed" if visit_completed else appointment_status,
        "appointment_date": pd.Timestamp(appointment_date) if appointment_date else pd.NaT,
    }
    values.update({field: "Yes" if complete else "No" for field, complete in standard_updates.items()})
    values.update({field: "Yes" if complete else "No" for field, complete in conditional_updates.items()})
    values.update({field: "No" if resolved else "Yes" for field, resolved in barrier_updates.items()})
    key = episode_key(row)
    st.session_state.setdefault("demo_episode_updates", {})[key] = values
    st.session_state.last_updated_episode = key
    st.rerun()


def render_progress(row: pd.Series) -> None:
    scheduled = row.appointment_status in {"Scheduled", "Completed"}
    visited = row.appointment_status == "Completed"
    complete = row.workflow_state == "Visit Completed + Tasks Complete"
    states = [True, scheduled, visited, complete]
    labels = ["Discharged ✓", "Visit Scheduled", "Visit Completed", "Transition Complete"]
    current = max(index for index, done in enumerate(states) if done)
    html = '<div class="progress-wrap">'
    for index, (label, done) in enumerate(zip(labels, states)):
        css = "done" if done else ""
        if index == current and not complete:
            css += " current"
        html += f'<div class="progress-step {css.strip()}">{label}</div>'
    st.markdown(html + "</div>", unsafe_allow_html=True)


def render_patient_snapshot(row: pd.Series) -> None:
    selected_id, selected_discharge = row.patient_id, row.discharge_date
    patient_tasks = tasks[
        (tasks.patient_id == selected_id) & (tasks.discharge_date == selected_discharge)
    ]
    access_tasks = patient_tasks[patient_tasks.task_domain == "SDOH & access"]
    care_tasks = patient_tasks[patient_tasks.task_domain != "SDOH & access"]
    status_name = (
        "Immediate Action" if row.workflow_category == "Immediate Action Required"
        else "Transition Complete" if row.workflow_state == "Visit Completed + Tasks Complete"
        else row.workflow_category
    )
    urgent_class = " urgent" if row.workflow_category == "Immediate Action Required" else ""

    st.markdown('<div class="snapshot-head"><div class="section-label">Patient Snapshot</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="snapshot-id">Patient {patient_number(row.patient_id)}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="snapshot-meta">{row.stroke_type} &nbsp;·&nbsp; Discharged {row.discharge_date:%b %d, %Y} &nbsp;·&nbsp; {row.days_since_discharge} days since discharge</div></div>',
        unsafe_allow_html=True,
    )
    reason = str(row.primary_reason).replace("STCC", "Stroke clinic")
    st.markdown(
        f'<div class="status-line{urgent_class}"><div class="status-name">{status_name}</div><div class="status-reason">{reason}</div></div>',
        unsafe_allow_html=True,
    )
    render_progress(row)
    if row.workflow_state == "Visit Completed + Tasks Complete":
        st.markdown('<div class="complete-note"><strong>✓ Transition complete</strong><br>All documented follow-up requirements have been completed.</div>', unsafe_allow_html=True)

    form_key = f"snapshot_{row.patient_id}_{row.discharge_date:%Y-%m-%d}"
    statuses = ["Not scheduled", "Scheduled", "Cancelled", "No-show"]
    default_status = row.appointment_status if row.appointment_status in statuses else (
        "Scheduled" if pd.notna(row.appointment_date) else "Not scheduled"
    )
    with st.form(form_key):
        clinic, coordination, access = st.columns(3)
        clinic = clinic.container(border=True)
        coordination = coordination.container(border=True)
        access = access.container(border=True)
        with clinic:
            st.markdown('<div class="module-label">Clinic Follow-Up</div>', unsafe_allow_html=True)
            appointment_status = st.selectbox("Appointment status", statuses, index=statuses.index(default_status))
            appointment_date = st.date_input(
                "Appointment date",
                value=row.appointment_date.date() if pd.notna(row.appointment_date) else None,
            )
            visit_completed = st.checkbox("Clinic visit completed", value=row.appointment_status == "Completed")
            st.caption(f"Target follow-up: {target_days} days after discharge")
        with coordination:
            st.markdown('<div class="module-label">Care Coordination</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="module-value">{len(care_tasks)} outstanding</div>', unsafe_allow_html=True)
            if not care_tasks.empty:
                for need in care_tasks.outstanding_task.head(3):
                    st.caption(f"• {str(need).replace('STCC', 'Stroke clinic')}")
            standard_updates = {
                "med_reconciliation_completed": st.checkbox("Medication reconciliation completed", value=row.med_reconciliation_completed == "Yes"),
                "secondary_prevention_plan_documented": st.checkbox("Secondary prevention plan documented", value=row.secondary_prevention_plan_documented == "Yes"),
                "pcp_followup_arranged": st.checkbox("PCP follow-up arranged", value=row.pcp_followup_arranged == "Yes"),
            }
            conditional_updates: dict[str, bool] = {}
            conditional_fields = [
                ("cardiac_monitoring_needed", "cardiac_monitoring_completed", "Cardiac monitoring completed"),
                ("other_workup_needed", "other_workup_completed", "Other stroke workup completed"),
                ("specialty_referral_needed", "specialty_referral_completed", "Specialty referral completed"),
            ]
            for needed, completed_field, label in conditional_fields:
                if row[needed] == "Yes":
                    conditional_updates[completed_field] = st.checkbox(label, value=row[completed_field] == "Yes")
            if row.rehab_needed == "Yes":
                conditional_updates["rehab_arranged"] = st.checkbox("Rehabilitation arranged", value=row.rehab_arranged == "Yes")
                conditional_updates["rehab_completed"] = st.checkbox("Rehabilitation completed", value=row.rehab_completed == "Yes")
        with access:
            st.markdown('<div class="module-label">Access & Support</div>', unsafe_allow_html=True)
            barrier_updates: dict[str, bool] = {}
            documented = [(field, label) for field, label in BARRIER_LABELS.items() if row[field] == "Yes"]
            if not documented:
                st.markdown('<div class="module-value">No needs documented</div><div class="module-copy">No access or support follow-up is currently recorded.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="module-value">{len(documented)} need(s)</div>', unsafe_allow_html=True)
                for field, label in documented:
                    barrier_updates[field] = st.checkbox(f"{label} need resolved", value=False)
        saved = st.form_submit_button("Save patient update", type="primary")
        if saved:
            if appointment_status == "Scheduled" and appointment_date is None and not visit_completed:
                st.error("Add an appointment date before saving a scheduled appointment.")
            else:
                save_patient_update(
                    row, appointment_status, appointment_date, visit_completed,
                    standard_updates, conditional_updates, barrier_updates,
                )

    with st.expander("Care Team Tasks"):
        if patient_tasks.empty:
            st.success("No outstanding transition needs.")
        else:
            for _, task in patient_tasks.iterrows():
                st.markdown(f"**{task.task_domain} — {str(task.outstanding_task).replace('STCC', 'Stroke clinic')}**")
                st.caption(str(task.recommended_action).replace("STCC", "stroke clinic"))
    with st.expander("Clinical Snapshot"):
        c1, c2 = st.columns(2)
        c1.markdown(f"**Stroke type**  \n{row.stroke_type}  \n\n**Etiology**  \n{row.stroke_etiology}")
        c2.markdown(f"**NIHSS**  \n{row.nihss}  \n\n**mRS**  \n{row.mrs}  \n\n**Disposition**  \n{row.discharge_disposition}")
    with st.expander("Hospitalization & Readmission History"):
        history = patients[patients.patient_id == row.patient_id].sort_values("discharge_date")
        for index, (_, episode) in enumerate(history.iterrows()):
            label = "Initial hospitalization" if index == 0 else episode.readmission_window
            st.markdown(f"**{label}** — admitted {episode.admission_date:%b %d, %Y}, discharged {episode.discharge_date:%b %d, %Y}")
            if index > 0:
                st.caption(f"↓ {int(episode.days_since_prior_discharge)} days after prior discharge")


selected = st.session_state.get("selected_cohort")
if selected == "rules":
    st.markdown('<div class="cohort-shell"><div class="cohort-kicker">Clinical Workflow</div><div class="cohort-title">How patients are prioritized</div></div>', unsafe_allow_html=True)
    st.markdown(
        f"""**Immediate Action Required** — a visit was cancelled or missed, a scheduled date passed, the patient remains unscheduled more than **{escalation_days} days**, or multiple care areas and an access need require coordination.

**Action Needed** — another scheduling or transition need remains, including an appointment outside the **{target_days}-day** target.

**On Track** — the visit is scheduled within the target window and no pre-visit action is needed."""
    )
    st.button("Close", on_click=close_cohort)
elif selected == "care_tasks":
    st.markdown('<div class="cohort-shell"><div class="cohort-kicker">Care Team Tasks</div><div class="cohort-title">Outstanding follow-up work</div></div>', unsafe_allow_html=True)
    domain = st.selectbox("Care team", ["All care teams"] + sorted(tasks.task_domain.unique().tolist()))
    task_view = tasks if domain == "All care teams" else tasks[tasks.task_domain == domain]
    display = task_view.copy()
    display["patient_id"] = display.patient_id.map(lambda value: f"Patient {patient_number(value)}")
    st.dataframe(
        display[["patient_id", "discharge_date", "task_domain", "outstanding_task", "recommended_action"]],
        width="stretch", hide_index=True,
        column_config={"patient_id":"Patient","discharge_date":st.column_config.DateColumn("Discharged"),"task_domain":"Care team","outstanding_task":"Outstanding task","recommended_action":"Next step"},
    )
    st.button("Close", on_click=close_cohort)
elif selected in COHORTS:
    title, frame, is_readmission = COHORTS[selected]
    st.markdown(f'<div class="cohort-shell"><div class="cohort-kicker">Selected Cohort</div><div class="cohort-title">{title}</div><div class="cohort-meta">{len(frame):,} transition episodes</div></div>', unsafe_allow_html=True)
    controls = st.columns([5, 1])
    query = controls[0].text_input("Find patient", placeholder="Patient identifier")
    controls[1].button("Close cohort", width="stretch", on_click=close_cohort)
    filtered = frame
    if query:
        normalized = filtered.patient_id.map(patient_number)
        filtered = filtered[filtered.patient_id.str.contains(query, case=False, na=False) | normalized.str.contains(query, case=False, na=False)]
    st.dataframe(
        cohort_table(filtered, is_readmission), width="stretch", hide_index=True,
        column_config={
            "patient_display":"Patient", "discharge_date":st.column_config.DateColumn("Discharge date"),
            "days_since_discharge":"Days since discharge", "appointment_status":"Visit status",
            "outstanding_needs":"Outstanding needs", "prior_discharge":st.column_config.DateColumn("Prior discharge"),
            "admission_date":st.column_config.DateColumn("Readmission date"),
            "days_since_prior_discharge":"Days to readmission", "readmission_window":"Readmission window",
        },
    )
    if not filtered.empty:
        options = list(filtered[["patient_id", "discharge_date"]].itertuples(index=False, name=None))
        selected_episode = st.selectbox("Open Patient Snapshot", options, format_func=episode_label)
        selected_row = filtered[
            (filtered.patient_id == selected_episode[0])
            & (filtered.discharge_date == selected_episode[1])
        ].iloc[0]
        render_patient_snapshot(selected_row)
