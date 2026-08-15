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
    :root {--navy:#132b46; --blue:#245f82; --teal:#16827b; --sky:#eaf4f7; --burgundy:#8b3152; --ink:#172536; --muted:#607080; --surface:#f4f7f8;}
    .stApp {background:linear-gradient(180deg,#f7fafb 0,#fff 24rem);}
    .block-container {padding-top: 1.25rem; padding-bottom:4rem; max-width:1440px;}
    h1, h2, h3, h4 {color:var(--ink); letter-spacing:-.015em;}
    h1 {color:var(--blue); margin-bottom:.15rem;}
    [data-testid="stSidebar"] {background:#f7f8fc; border-right:1px solid #e4e7ef;}
    [data-testid="stSidebar"] h2 {color:var(--blue);}
    .hero {position:relative; overflow:hidden; padding:2.6rem 2.8rem; border-radius:22px; color:white; margin-bottom:1.7rem; background:linear-gradient(120deg,#102a45 0%,#1d536f 62%,#16827b 115%); box-shadow:0 18px 45px #17354a24;}
    .hero:after {content:""; position:absolute; width:330px; height:330px; border:1px solid #ffffff24; border-radius:50%; right:-80px; top:-170px; box-shadow:0 0 0 45px #ffffff0a,0 0 0 90px #ffffff08;}
    .hero-kicker {font-size:.72rem; letter-spacing:.16em; text-transform:uppercase; font-weight:750; color:#b9e4df; margin-bottom:.7rem;}
    .hero-title {font-size:clamp(2rem,4vw,3.35rem); line-height:1.03; max-width:760px; letter-spacing:-.04em; font-weight:730;}
    .hero-copy {font-size:1.05rem; line-height:1.65; color:#e2edf1; max-width:720px; margin-top:1rem;}
    .eyebrow {font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; font-weight:750; color:var(--teal); margin-bottom:.2rem;}
    .section-heading {font-size:1.55rem; color:var(--navy); font-weight:720; letter-spacing:-.02em;}
    .section-copy {color:var(--muted); margin:-.15rem 0 1rem;}
    div[data-testid="stButton"] button {border-radius:14px; border:1px solid #d8e3e7; min-height:3rem; font-weight:650; transition:.18s ease;}
    div[data-testid="stButton"] button:hover {border-color:var(--teal); color:var(--teal); transform:translateY(-1px); box-shadow:0 7px 18px #17485a16;}
    div[data-testid="stExpander"] {background:#fff; border:1px solid #dce6e9; border-radius:15px; box-shadow:0 6px 20px #16344b0a; overflow:hidden; margin-bottom:.75rem;}
    div[data-testid="stExpander"] summary {font-weight:680; color:var(--navy); padding:.2rem .45rem;}
    .snapshot-head {background:linear-gradient(135deg,#edf6f7,#f7fafb); border:1px solid #d5e5e7; border-radius:17px; padding:1.25rem 1.4rem; margin:1.1rem 0;}
    .snapshot-name {font-size:1.45rem; color:var(--navy); font-weight:740;}
    .snapshot-meta {color:var(--muted); margin-top:.2rem;}
    .module {background:white; border:1px solid #dce6e9; border-radius:15px; padding:1rem 1.15rem; min-height:150px; box-shadow:0 5px 18px #16344b09;}
    .module-title {color:var(--navy); font-weight:720; margin-bottom:.65rem;}
    .progress-label {display:flex; justify-content:space-between; color:var(--muted); font-size:.82rem; margin:.3rem 0;}
    .progress-track {height:8px; background:#e4ecee; border-radius:99px; overflow:hidden; margin-bottom:1.1rem;}
    .progress-fill {height:100%; background:linear-gradient(90deg,var(--teal),#59afa2); border-radius:99px;}
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
    @media(max-width:800px) {.priority-grid {grid-template-columns:1fr;} .flow-arrow {display:none;} .hero{padding:1.7rem 1.35rem;border-radius:16px}.hero-title{font-size:2rem}.block-container{padding-left:1rem;padding-right:1rem} div[data-testid="stHorizontalBlock"]{gap:.65rem}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<section class="hero"><div class="hero-kicker">Stroke Transitions of Care Clinic</div>'
    '<div class="hero-title">Every transition, clearly in view.</div>'
    '<div class="hero-copy">A focused clinical workspace for the vulnerable weeks after stroke—bringing follow-up, care gaps, access needs, and readmission outcomes into one coordinated view.</div></section>',
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

st.markdown('<div class="eyebrow">Command center</div><div class="section-heading">Transition overview</div>', unsafe_allow_html=True)
st.markdown('<div class="section-copy">Select a tile to open the corresponding patient cohort below.</div>', unsafe_allow_html=True)

st.markdown("#### Active Transitions")
active_tiles = st.columns(3)
active_tile_data = [
    ("active", "Appointment needed", len(active), "Coordinate the clinic visit"),
    ("post", "Follow-up needs", len(post_visit), "Close post-visit care gaps"),
    ("closed", "Transition complete", len(completed), "Review closed-loop episodes"),
]
for column, (focus, label, count, help_text) in zip(active_tiles, active_tile_data):
    with column:
        st.metric(label, f"{count:,}", help=help_text)
        if st.button(f"View {label.lower()} →", key=f"tile_{focus}", width="stretch"):
            st.session_state.cohort_focus = focus

st.markdown("#### Needs Attention")
attention_tiles = st.columns(3)
attention_data = [
    ("Immediate action", int((active.workflow_category == "Immediate Action Required").sum()), "immediate"),
    ("Action needed", int((active.workflow_category == "Action Needed").sum()), "action"),
    ("On track", int((active.workflow_category == "On Track").sum()), "track"),
]
for column, (label, count, focus) in zip(attention_tiles, attention_data):
    with column:
        st.metric(label, f"{count:,}")
        if st.button(f"Explore {label.lower()} →", key=f"attention_{focus}", width="stretch"):
            st.session_state.cohort_focus = "active"
            st.session_state["cat_active"] = [
                {"immediate": "Immediate Action Required", "action": "Action Needed", "track": "On Track"}[focus]
            ]

st.markdown("#### Readmission Outcomes")
outcome_tiles = st.columns(2)
for column, label, count, key in (
    (outcome_tiles[0], "Within 30 days", len(readmissions_30), "30"),
    (outcome_tiles[1], "31–90 days", len(readmissions_90), "90"),
):
    with column:
        st.metric(label, f"{count:,}", help="Readmission documented for this transition episode")
        if st.button(f"Review {label.lower()} outcomes →", key=f"readmission_{key}", width="stretch"):
            st.session_state.cohort_focus = "readmission"

st.caption(f"Current as of **{as_of:%B %d, %Y}** · {len(active_episodes):,} active eligible episodes")


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


def yes_no(value: object) -> str:
    """Turn source flags into concise, accessible UI labels."""
    return "Complete" if value == "Yes" else "Needs attention"


def render_patient_list(frame: pd.DataFrame, key: str, *, appointment_controls: bool = False) -> None:
    """Render a compact cohort and progressively disclose the selected episode."""
    filtered = appointment_filters(frame, key) if appointment_controls else patient_search(frame, key)
    st.caption(f"{len(filtered):,} patient episodes")
    display = filtered.copy()
    display["patient_id"] = display.patient_id.map(lambda value: f"Patient {patient_number(value)}")
    if key == "closed":
        display["workflow_category"] = "Completed"
    # Keep the cohort view intentionally scannable; detail belongs in the snapshot.
    columns = [
        "patient_id", "workflow_category", "appointment_status", "discharge_date",
        "days_since_discharge", "unresolved_task_count", "recorded_barrier_count",
    ]
    st.dataframe(
        display[columns], width="stretch", hide_index=True,
        column_config={
            "patient_id": "Patient", "workflow_category": "Priority",
            "appointment_status": "Follow-up", "discharge_date": st.column_config.DateColumn("Discharged"),
            "days_since_discharge": "Days out", "unresolved_task_count": "Open tasks",
            "recorded_barrier_count": "Access needs",
        },
    )
    if filtered.empty:
        st.info("No episodes match the current filters.")
        return

    episode_options = list(filtered[["patient_id", "discharge_date"]].itertuples(index=False, name=None))
    selected_id, selected_discharge = st.selectbox(
        "Open Patient Snapshot", episode_options,
        format_func=lambda value: episode_label(value[0], value[1]), key=f"patient_{key}",
    )
    row = filtered.loc[
        (filtered.patient_id == selected_id) & (filtered.discharge_date == selected_discharge)
    ].iloc[0]
    patient_tasks = tasks[(tasks.patient_id == selected_id) & (tasks.discharge_date == selected_discharge)]
    completed_steps = 1 + int(row.appointment_status == "Completed") + int(row.med_reconciliation_completed == "Yes") + int(row.secondary_prevention_plan_documented == "Yes") + int(row.pcp_followup_arranged == "Yes")
    progress = 100 if row.patient_section == "Closed Loop / Completed" else round(completed_steps / 5 * 100)
    appointment = row.appointment_date.strftime("%b %d, %Y") if pd.notna(row.appointment_date) else "Not scheduled"
    context = "Transition Complete" if row.patient_section == "Closed Loop / Completed" else row.workflow_category

    st.markdown(
        f'<div class="snapshot-head"><div class="eyebrow">Patient Snapshot · {context}</div>'
        f'<div class="snapshot-name">Patient {patient_number(row.patient_id)}</div>'
        f'<div class="snapshot-meta">{row.age}-year-old {str(row.sex).lower()} · {row.stroke_type} · discharged {row.discharge_date:%B %d, %Y}</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="progress-label"><span>Transition progress</span><strong>{progress}%</strong></div>'
        f'<div class="progress-track"><div class="progress-fill" style="width:{progress}%"></div></div>',
        unsafe_allow_html=True,
    )
    if row.patient_section == "Closed Loop / Completed":
        st.success("Transition Complete — clinic follow-up and all documented transition needs are closed.", icon="✓")
    else:
        st.info(str(row.primary_reason).replace("STCC", "stroke clinic"), icon="→")

    clinic, coordination, access = st.columns(3)
    with clinic:
        st.markdown('<div class="module"><div class="module-title">Clinic Follow-Up</div>', unsafe_allow_html=True)
        st.write(f"**Status**  \n{row.appointment_status}")
        st.write(f"**Appointment**  \n{appointment}")
        st.write(f"**Target window**  \n{target_days} days after discharge")
        st.markdown('</div>', unsafe_allow_html=True)
    with coordination:
        st.markdown('<div class="module"><div class="module-title">Care Coordination</div>', unsafe_allow_html=True)
        st.write(f"**Medication reconciliation**  \n{yes_no(row.med_reconciliation_completed)}")
        st.write(f"**Prevention plan**  \n{yes_no(row.secondary_prevention_plan_documented)}")
        st.write(f"**PCP follow-up**  \n{yes_no(row.pcp_followup_arranged)}")
        st.markdown('</div>', unsafe_allow_html=True)
    with access:
        st.markdown('<div class="module"><div class="module-title">Access & Support</div>', unsafe_allow_html=True)
        barrier_labels = {
            "transportation_barrier": "Transportation", "housing_instability": "Housing",
            "food_insecurity": "Food access", "economic_or_insurance_barrier": "Coverage / cost",
            "limited_caregiver_support": "Caregiver support",
        }
        needs = [label for field, label in barrier_labels.items() if row[field] == "Yes"]
        if needs:
            for need in needs:
                st.write(f"• {need}")
        else:
            st.write("No documented access barriers")
        st.write(f"**Discharge setting**  \n{row.discharge_disposition}")
        st.markdown('</div>', unsafe_allow_html=True)

    with st.expander(f"Care Team Tasks · {len(patient_tasks)} open", expanded=False):
        if patient_tasks.empty:
            st.success("No outstanding transition needs.")
        else:
            for _, task in patient_tasks.iterrows():
                gap = str(task.outstanding_task).replace("STCC", "Stroke clinic")
                action = str(task.recommended_action).replace("STCC", "stroke clinic")
                st.markdown(f"**{task.task_domain} · {gap}**  \n{action}")
                st.divider()
    with st.expander("Clinical Snapshot", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Stroke type", row.stroke_type)
        c2.metric("Etiology", row.stroke_etiology)
        c3.metric("NIHSS", row.nihss)
        c4.metric("mRS", row.mrs)
        st.caption(f"Admitted {row.admission_date:%b %d, %Y} · discharged to {row.discharge_disposition}")
    with st.expander("Hospitalization & Readmission History", expanded=False):
        st.write(f"**Index admission:** {row.admission_date:%B %d, %Y} – {row.discharge_date:%B %d, %Y}")
        st.write(f"**Readmission outcome:** {row.readmission_window}")
    with st.expander("Update Patient Snapshot · session only", expanded=False):
        render_status_update(row, key)


st.divider()
st.markdown('<div class="eyebrow">Patient workspace</div><div class="section-heading">Patient cohorts</div>', unsafe_allow_html=True)
st.markdown('<div class="section-copy">Cohorts stay collapsed until you are ready to review patients and open a snapshot.</div>', unsafe_allow_html=True)
focus = st.session_state.get("cohort_focus")

if st.toggle(f"Appointment Needed · {len(active):,}", value=focus == "active", key="show_active"):
    st.write("Recently discharged patients who still need to complete their stroke clinic visit.")
    render_patient_list(active, "active", appointment_controls=True)

if st.toggle(f"Follow-Up Needs · {len(post_visit):,}", value=focus == "post", key="show_post"):
    st.write("The clinic visit is complete, but one or more transition needs remain open.")
    render_context("Appointment status: Completed")
    render_patient_list(post_visit, "post")

if st.toggle(f"Readmission Outcomes · {len(readmissions_30) + len(readmissions_90):,}", value=focus == "readmission", key="show_readmission"):
    readmission_view = patients[patients.readmission_window.isin(["Readmission within 30 days", "Readmission within 31–90 days"])]
    st.write("Review transition episodes with a documented readmission within 90 days.")
    render_patient_list(readmission_view, "readmission")

if st.toggle(f"Transition Complete · {len(completed):,}", value=focus == "closed", key="show_closed"):
    st.write("Clinic follow-up and all documented transition needs are complete.")
    render_context("Status: Completed", "Closed loop")
    render_patient_list(completed, "closed")

with st.expander(f"All Care Team Tasks · {len(tasks):,}", expanded=False):
    st.write("Filter outstanding work by accountable care team or patient cohort.")
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
        task_display["outstanding_task"] = task_display.outstanding_task.str.replace("STCC", "Stroke clinic", regex=False)
        task_display["recommended_action"] = task_display.recommended_action.str.replace("STCC", "stroke clinic", regex=False)
        st.dataframe(
            task_display[["patient_id", "patient_section", "task_domain", "outstanding_task", "recommended_action"]],
            width="stretch", hide_index=True,
            column_config={"patient_id": "Patient", "patient_section": "Cohort", "task_domain": "Care team", "outstanding_task": "Open task", "recommended_action": "Recommended next action"},
        )

with st.expander("How patients are prioritized", expanded=False):
    st.markdown(
        f"""**Immediate Action Required**
A visit was cancelled or missed, a scheduled date passed without completion, the patient remains
unscheduled more than **{escalation_days} days** after discharge, or cross-domain needs and an access barrier require coordination.

**Action Needed**
Another scheduling or transition need is open, including an appointment outside the **{target_days}-day** target window.

**On Track**
The patient is scheduled within the target window with no pre-visit action needed.

After a clinic visit, patients with remaining needs move to **Follow-Up Needs**. Patients with no remaining needs move to **Transition Complete**."""
    )
