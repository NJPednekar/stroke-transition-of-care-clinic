"""Streamlit entry point for the Stroke Transitions of Care Clinic work queue."""

from datetime import date
from html import escape
from math import ceil
from pathlib import Path

import pandas as pd
import streamlit as st

from stcc_logic import derive_workflow, load_data, readmission_outcome_cohorts


DATA_FILE = Path(__file__).with_name("stroke_transitions_of_care_clinic_synthetic_updated.csv")
STATE_LABELS = {
    "Appointment / Visit Needed + Tasks Pending": "Appointment Needed · Tasks Pending",
    "Appointment / Visit Needed + Tasks Complete": "Appointment Needed · Tasks Complete",
    "Visit Completed + Tasks Pending": "Appointment Completed · Tasks Pending",
    "Visit Completed + Tasks Complete": "Transition Complete",
}
STATE_ORDER = list(STATE_LABELS.values())
PAGE_SIZE = 12

st.set_page_config(page_title="Stroke Transitions of Care Clinic", page_icon="🧠", layout="wide")
st.markdown(
    """
<style>
:root{--navy:#101f35;--navy2:#193552;--wine:#8a2638;--gold:#c49a52;--ink:#172335;--muted:#647184;--warm:#f7f4ef;--line:#dedbd4}
.stApp{background:linear-gradient(180deg,#f7f4ef 0,#fff 33rem)}
.block-container{padding-top:1rem;padding-bottom:4rem;max-width:1500px} h1,h2,h3,h4{color:var(--navy)}
[data-testid="stSidebar"]{background:var(--navy);border-right:3px solid var(--gold)}
[data-testid="stSidebar"] *{color:#f8f5ef!important}[data-testid="stSidebar"] input{color:var(--ink)!important}
[data-testid="stSidebar"] [data-baseweb="select"] *{color:var(--ink)!important}
.hero{position:relative;overflow:hidden;min-height:245px;padding:2.3rem 3rem;border-radius:22px;background:linear-gradient(112deg,#0d1c31 0%,#183754 72%,#6f2234 130%);color:#fff;box-shadow:0 18px 48px #101f3529;margin-bottom:1.5rem}
.brand{font-size:clamp(1rem,1.8vw,1.35rem);font-weight:850;letter-spacing:.12em;color:#f1d9a7;text-transform:uppercase;margin-bottom:1.1rem;max-width:780px}
.hero-title{font-size:clamp(2.1rem,4vw,3.6rem);line-height:1.02;font-weight:780;letter-spacing:-.045em;max-width:790px}.hero-copy{color:#e7e9ec;font-size:1.05rem;line-height:1.55;max-width:680px;margin-top:1rem}
.brain{position:absolute;right:2.2rem;top:1.2rem;width:270px;height:210px;opacity:.82}.brain path,.brain circle{fill:none;stroke:#d3af69;stroke-width:2}.brain .vessel{stroke:#b94a5d;stroke-width:3}
.eyebrow{font-size:.72rem;letter-spacing:.13em;text-transform:uppercase;font-weight:800;color:var(--wine)}.section-title{font-size:1.6rem;font-weight:760;color:var(--navy);margin:.1rem 0 .9rem}
div[data-testid="stButton"] button{border-radius:11px;border:1px solid #d8d4cd;min-height:2.8rem;font-weight:680;background:#fff;color:var(--navy)}div[data-testid="stButton"] button:hover{border-color:var(--wine);color:var(--wine)}
[class*="st-key-state_"] button{min-height:7rem!important;text-align:left!important;justify-content:flex-start!important;border-top:4px solid var(--wine)!important;box-shadow:0 5px 18px #101f3510!important}
[class*="st-key-state_"] button strong{font-size:1.75rem;color:var(--navy)}
.queue-shell{background:#f8f6f2;border:1px solid var(--line);border-radius:18px;padding:1rem 1.15rem .35rem;margin-top:1.2rem}.queue-head{font-size:1.35rem;font-weight:760;color:var(--navy)}
[class*="st-key-row_"] button{min-height:5.1rem!important;text-align:left!important;justify-content:flex-start!important;padding:.7rem .85rem!important;line-height:1.3!important}
[class*="st-key-selected_row_"] button{background:#f8e9e9!important;border:2px solid var(--wine)!important;box-shadow:inset 5px 0 var(--wine)!important}
.snapshot-head{background:linear-gradient(135deg,#101f35,#193552);color:white;border-radius:16px;padding:1.15rem 1.3rem;margin-bottom:.8rem;border-bottom:4px solid var(--gold)}.snapshot-head .eyebrow{color:#ebcd91}.snapshot-name{font-size:1.55rem;font-weight:780}.snapshot-meta{color:#dfe5eb;font-size:.9rem;margin-top:.22rem}
.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.7rem}.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:.95rem;box-shadow:0 4px 14px #101f350b}.card h4{margin:0 0 .7rem;border-bottom:2px solid #e9dfce;padding-bottom:.5rem}.fact{display:flex;justify-content:space-between;gap:.6rem;border-bottom:1px solid #eeeae4;padding:.38rem 0;font-size:.82rem}.fact span:first-child{color:var(--muted)}.fact span:last-child{text-align:right;font-weight:650;color:var(--ink)}
.chip{display:inline-block;border-radius:99px;padding:.15rem .48rem;font-size:.72rem;font-weight:760;background:#eceff2;color:#35465a}.chip.ok{background:#e6f0e9;color:#275f3c}.chip.warn{background:#f7e6e8;color:#84283a}.chip.na{background:#eeece8;color:#6f6a62}
.st-key-mobile_snapshot{display:none}.task-line{border-left:4px solid var(--wine);background:#fff;padding:.65rem .8rem;margin:.4rem 0;border-radius:6px}.small{color:var(--muted);font-size:.8rem}
.outcomes-label{margin-top:.8rem;font-size:.69rem;letter-spacing:.13em;text-transform:uppercase;font-weight:800;color:var(--muted)}
[class*="st-key-outcome_"] button{min-height:3.4rem!important;text-align:left!important;justify-content:flex-start!important;font-size:.82rem!important;background:#fbfaf8!important}
[class*="st-key-outcome_"] button strong{font-size:1.2rem;color:var(--navy)}
div[data-testid="stExpander"]{border:1px solid var(--line)!important;border-radius:12px!important;background:#fff!important}
@media(max-width:900px){.brain{opacity:.28;right:-5rem}.hero{padding:1.6rem 1.3rem}.cards{grid-template-columns:1fr}.st-key-mobile_snapshot{display:block}.st-key-desktop_snapshot{display:none}.block-container{padding-left:.8rem;padding-right:.8rem}}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """<section class="hero"><div class="brand">Stroke Transitions of Care Clinic</div>
    <div class="hero-title">Every transition,<br>clearly in view.</div>
    <div class="hero-copy">One coordinated view of follow-up, unresolved care needs, access barriers, and outcomes after stroke.</div>
    <svg class="brain" viewBox="0 0 300 230" aria-hidden="true"><path d="M151 31c-19-25-58-12-61 16-29-10-51 16-40 42-30 14-27 53 1 64-8 34 31 54 55 34 14 24 45 12 45-13V31Z"/><path d="M154 31c19-25 58-12 61 16 29-10 51 16 40 42 30 14 27 53-1 64 8 34-31 54-55 34-14 24-45 12-45-13V31Z"/><path d="M151 62c-28-8-41 18-27 35-27 2-30 35-9 44M154 78c24-18 49 4 40 24 28-4 39 30 19 43"/><path class="vessel" d="M151 190v-64m0 22-31-27m31 9 36-35m-36 49 39 31"/><circle class="vessel" cx="187" cy="95" r="4"/><circle class="vessel" cx="120" cy="121" r="4"/></svg></section>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## Data & clinic controls")
    st.caption("SESSION WORKSPACE")
    uploaded = st.file_uploader("Patient episode CSV", type="csv", help="Leave empty to use the representative demo population.")
    as_of = st.date_input("Clinical as-of date", value=date(2026, 8, 13))
    target_days = st.number_input("Target follow-up (days)", 1, 60, 14)
    escalation_days = st.number_input("Escalate unscheduled after", 1, 30, 7)
    st.divider()
    st.caption("Updates remain in this browser session and never alter the source dataset.")
    if st.button("Reset session updates", width="stretch"):
        st.session_state.demo_episode_updates = {}
        st.rerun()


def apply_updates(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for (patient_id, discharged), values in st.session_state.get("demo_episode_updates", {}).items():
        mask = (result.patient_id == patient_id) & (result.discharge_date.dt.strftime("%Y-%m-%d") == discharged)
        for field, value in values.items():
            if field in result:
                result.loc[mask, field] = value
    return result


try:
    source_raw = load_data(uploaded if uploaded is not None else DATA_FILE)
    patients, tasks = derive_workflow(apply_updates(source_raw).query("stcc_eligible == 'Yes'"), as_of, int(target_days), int(escalation_days))
except (ValueError, OSError, pd.errors.ParserError) as exc:
    st.error(f"Could not load patient data: {exc}")
    st.stop()

patients["workflow_label"] = patients.workflow_state.map(STATE_LABELS)
readmission_cohorts = readmission_outcome_cohorts(patients)
st.session_state.setdefault("queue_mode", "Patients")
if not tasks.empty:
    tasks["workflow_label"] = tasks.workflow_state.map(STATE_LABELS)


def number(value: object) -> str:
    return str(value).removeprefix("STCC-")


def episode_key(row: pd.Series) -> tuple[str, str]:
    return (str(row.patient_id), row.discharge_date.strftime("%Y-%m-%d"))


def chip(value: str, good: tuple[str, ...] = ("Yes", "Completed", "Scheduled")) -> str:
    if value in good:
        label, style = ("Complete" if value in {"Yes", "Completed"} else value), "ok"
    elif value in {"No", "Pending", "Not scheduled", "Cancelled", "No-show", "Barrier"}:
        label, style = ("Pending" if value == "No" else value.title()), "warn"
    else:
        label, style = "Not Applicable", "na"
    return f'<span class="chip {style}">{escape(label)}</span>'


def fact(label: str, value: str) -> str:
    return f'<div class="fact"><span>{escape(label)}</span><span>{value}</span></div>'


def snapshot_html(row: pd.Series) -> str:
    appointment = row.appointment_date.strftime("%b %d, %Y") if pd.notna(row.appointment_date) else "Not scheduled"
    patient_tasks = tasks[(tasks.patient_id == row.patient_id) & (tasks.discharge_date == row.discharge_date)] if not tasks.empty else tasks
    appointment_need = patient_tasks.loc[patient_tasks.task_domain == "Appointment & scheduling", "outstanding_task"]
    clinic = fact("Appointment status", chip(str(row.appointment_status))) + fact("Scheduled date", escape(appointment)) + fact("Target window", f"{target_days} days") + fact("Visit completed", chip("Yes" if row.appointment_status == "Completed" else "No")) + fact("Open appointment need", escape(str(appointment_need.iloc[0]).replace("STCC", "Stroke clinic")) if len(appointment_need) else chip("Not applicable"))
    monitoring = "Not applicable" if row.cardiac_monitoring_needed != "Yes" else row.cardiac_monitoring_completed
    workup = "Not applicable" if row.other_workup_needed != "Yes" else row.other_workup_completed
    rehab = "Not applicable" if row.rehab_needed != "Yes" else row.rehab_arranged
    referral = "Not applicable" if row.specialty_referral_needed != "Yes" else row.specialty_referral_completed
    coordination = fact("Medication reconciliation", chip(str(row.med_reconciliation_completed))) + fact("Prevention plan", chip(str(row.secondary_prevention_plan_documented))) + fact("PCP follow-up", chip(str(row.pcp_followup_arranged))) + fact("Cardiac monitoring", chip(str(monitoring))) + fact("Other workup", chip(str(workup))) + fact("Rehabilitation", chip(str(rehab))) + fact("Specialty referral", chip(str(referral))) + fact("Caregiver support", chip("Barrier" if row.limited_caregiver_support == "Yes" else "Not applicable"))
    access = fact("Transportation", chip("Barrier" if row.transportation_barrier == "Yes" else "Not applicable")) + fact("Insurance / cost", chip("Barrier" if row.economic_or_insurance_barrier == "Yes" else "Not applicable")) + fact("Financial assistance", chip("Pending" if row.economic_or_insurance_barrier == "Yes" else "Not applicable")) + fact("Housing", chip("Barrier" if row.housing_instability == "Yes" else "Not applicable")) + fact("Food access", chip("Barrier" if row.food_insecurity == "Yes" else "Not applicable")) + fact("Discharge setting", escape(str(row.discharge_disposition)))
    return f'<div class="snapshot-head"><div class="eyebrow">Patient Snapshot · {escape(row.workflow_label)}</div><div class="snapshot-name">Patient {escape(number(row.patient_id))}</div><div class="snapshot-meta">{int(row.age)}-year-old {escape(str(row.sex).lower())} · {escape(str(row.stroke_type))} · discharged {row.discharge_date:%B %d, %Y} · episode {int(row.hospitalization_number)}</div></div><div class="cards"><div class="card"><h4>Clinic Follow-Up</h4>{clinic}</div><div class="card"><h4>Care Coordination</h4>{coordination}</div><div class="card"><h4>Access &amp; Support</h4>{access}</div></div>'


def selected_row(frame: pd.DataFrame) -> pd.Series | None:
    selected = st.session_state.get("selected_episode")
    if not selected:
        return None
    match = frame[(frame.patient_id.astype(str) == selected[0]) & (frame.discharge_date.dt.strftime("%Y-%m-%d") == selected[1])]
    return None if match.empty else match.iloc[0]


def render_update(row: pd.Series, key: str) -> None:
    current = str(row.appointment_status)
    base_status = current if current in ["Not scheduled", "Scheduled", "Cancelled", "No-show"] else "Scheduled"
    with st.form(f"update_{key}_{row.patient_id}_{row.discharge_date:%Y%m%d}"):
        st.markdown("**CLINIC FOLLOW-UP**")
        a, b, c = st.columns(3)
        status = a.selectbox("Appointment status", ["Not scheduled", "Scheduled", "Cancelled", "No-show"], index=["Not scheduled", "Scheduled", "Cancelled", "No-show"].index(base_status))
        appointment = b.date_input("Appointment date", value=row.appointment_date.date() if pd.notna(row.appointment_date) else None)
        completed = c.checkbox("Clinic visit completed", value=current == "Completed")
        st.markdown("**CARE COORDINATION**")
        med = st.checkbox("Medication reconciliation completed", value=row.med_reconciliation_completed == "Yes")
        prevention = st.checkbox("Secondary prevention plan documented", value=row.secondary_prevention_plan_documented == "Yes")
        pcp = st.checkbox("PCP follow-up arranged", value=row.pcp_followup_arranged == "Yes")
        conditional_updates = {}
        st.caption("Applicable workup, rehabilitation & referrals")
        conditional_columns = st.columns(2)
        conditional_index = 0
        if row.cardiac_monitoring_needed == "Yes":
            conditional_updates["cardiac_monitoring_completed"] = conditional_columns[conditional_index % 2].checkbox("Cardiac monitoring completed", value=row.cardiac_monitoring_completed == "Yes")
            conditional_index += 1
        if row.other_workup_needed == "Yes":
            conditional_updates["other_workup_completed"] = conditional_columns[conditional_index % 2].checkbox(f"{row.other_workup_type} completed", value=row.other_workup_completed == "Yes")
            conditional_index += 1
        if row.rehab_needed == "Yes":
            conditional_updates["rehab_arranged"] = conditional_columns[conditional_index % 2].checkbox("Rehabilitation arranged", value=row.rehab_arranged == "Yes")
            conditional_index += 1
            conditional_updates["rehab_completed"] = conditional_columns[conditional_index % 2].checkbox("Rehabilitation completed", value=row.rehab_completed == "Yes")
            conditional_index += 1
        if row.specialty_referral_needed == "Yes":
            conditional_updates["specialty_referral_completed"] = conditional_columns[conditional_index % 2].checkbox("Specialty referral completed", value=row.specialty_referral_completed == "Yes")
        if not conditional_updates:
            st.caption("No additional workup, rehabilitation, or referral is required for this episode.")
        st.markdown("**ACCESS & SUPPORT**")
        access_columns = st.columns(2)
        access_updates = {
            "limited_caregiver_support": access_columns[0].checkbox("Limited caregiver support", value=row.limited_caregiver_support == "Yes"),
            "transportation_barrier": access_columns[1].checkbox("Transportation barrier", value=row.transportation_barrier == "Yes"),
            "economic_or_insurance_barrier": access_columns[0].checkbox("Insurance / economic access barrier", value=row.economic_or_insurance_barrier == "Yes"),
            "housing_instability": access_columns[1].checkbox("Housing instability", value=row.housing_instability == "Yes"),
            "food_insecurity": access_columns[0].checkbox("Food insecurity", value=row.food_insecurity == "Yes"),
        }
        if st.form_submit_button("Save & recalculate", type="primary"):
            if status == "Scheduled" and appointment is None and not completed:
                st.error("Choose an appointment date for a scheduled visit.")
            else:
                values = {
                    "appointment_status": "Completed" if completed else status,
                    "appointment_date": pd.Timestamp(appointment) if appointment else pd.NaT,
                    "med_reconciliation_completed": "Yes" if med else "No",
                    "secondary_prevention_plan_documented": "Yes" if prevention else "No",
                    "pcp_followup_arranged": "Yes" if pcp else "No",
                }
                values.update({field: "Yes" if value else "No" for field, value in conditional_updates.items()})
                values.update({field: "Yes" if value else "No" for field, value in access_updates.items()})
                st.session_state.setdefault("demo_episode_updates", {})[episode_key(row)] = values
                st.rerun()


def render_snapshot(row: pd.Series, key: str) -> None:
    st.markdown(snapshot_html(row), unsafe_allow_html=True)
    patient_tasks = tasks[(tasks.patient_id == row.patient_id) & (tasks.discharge_date == row.discharge_date)] if not tasks.empty else tasks
    with st.expander(f"Outstanding tasks · {len(patient_tasks)}", expanded=False):
        if patient_tasks.empty:
            st.success("No outstanding transition work.")
        for _, task in patient_tasks.iterrows():
            st.markdown(f'<div class="task-line"><strong>{escape(str(task.outstanding_task).replace("STCC", "Stroke clinic"))}</strong><br><span class="small">{escape(str(task.task_domain))} · {escape(str(task.recommended_action).replace("STCC", "stroke clinic"))}</span></div>', unsafe_allow_html=True)
    with st.expander("Clinical & hospitalization history"):
        st.write(f"**Stroke etiology:** {row.stroke_etiology} · **NIHSS:** {row.nihss} · **mRS:** {row.mrs}")
        st.write(f"**Admission:** {row.admission_date:%B %d, %Y} · **Discharge:** {row.discharge_date:%B %d, %Y}")
        st.write(f"**Readmission outcome:** {row.readmission_window}")
    with st.expander("Update Patient Snapshot · session only"):
        render_update(row, key)


st.markdown('<div class="eyebrow">Clinic overview</div><div class="section-title">Four-state transition pathway</div>', unsafe_allow_html=True)
tiles = st.columns(4)
for index, label in enumerate(STATE_ORDER):
    count = int((patients.workflow_label == label).sum())
    with tiles[index], st.container(key=f"state_{index}"):
        if st.button(f"**{count:,}**  \n{label}", key=f"choose_state_{index}", width="stretch"):
            st.session_state.patient_group = label
            st.session_state.queue_mode = "Patients"
            st.session_state.selected_episode = None
            st.session_state.patient_page = 1
            st.rerun()

st.markdown('<div class="outcomes-label">Readmission outcomes</div>', unsafe_allow_html=True)
outcome_tiles = st.columns(3)
for index, (label, cohort) in enumerate(readmission_cohorts.items()):
    with outcome_tiles[index], st.container(key=f"outcome_{index}"):
        if st.button(f"**{len(cohort):,}**  {label}", key=f"choose_outcome_{index}", width="stretch"):
            st.session_state.patient_group = label
            st.session_state.queue_mode = "Patients"
            st.session_state.selected_episode = None
            st.session_state.patient_page = 1
            st.rerun()
st.caption("Outcomes observed to date; episodes may not yet have completed 90 days of follow-up.")

mode = st.segmented_control("Workspace", ["Patients", "Care Team Tasks"], key="queue_mode")
with st.container(key="queue_shell"):
    st.markdown('<div class="queue-head">Clinical work queue</div>', unsafe_allow_html=True)
    if mode == "Patients":
        f1, f2, f3 = st.columns([1.4, 1.2, 1])
        patient_groups = STATE_ORDER + list(readmission_cohorts)
        current_group = st.session_state.get("patient_group", STATE_ORDER[0])
        if current_group not in patient_groups:
            current_group = STATE_ORDER[0]
        group = f1.selectbox("Patient group", patient_groups, index=patient_groups.index(current_group), key="patient_group")
        search = f2.text_input("Search patient", placeholder="ID")
        sort = f3.selectbox("Sort", ["Priority", "Newest discharge", "Oldest discharge"])
        view = (readmission_cohorts[group] if group in readmission_cohorts else patients[patients.workflow_label == group]).copy()
        if search:
            view = view[view.patient_id.str.contains(search, case=False, na=False) | view.patient_id.map(number).str.contains(search, case=False, na=False)]
        if sort == "Newest discharge": view = view.sort_values("discharge_date", ascending=False)
        elif sort == "Oldest discharge": view = view.sort_values("discharge_date")
    else:
        f1, f2, f3 = st.columns([1.2, 1.3, 1.4])
        team = f1.selectbox("Responsible team", ["All outstanding tasks"] + sorted(tasks.task_domain.unique().tolist()) if not tasks.empty else ["All outstanding tasks"])
        task_groups = ["All outstanding tasks", "Appointment & Scheduling", "Care Coordination", "Access & Support"] + STATE_ORDER[:3]
        task_group = f2.selectbox("Patient / workflow group", task_groups)
        search = f3.text_input("Search patient or task", placeholder="ID or need")
        task_view = tasks.copy()
        if team != "All outstanding tasks": task_view = task_view[task_view.task_domain == team]
        if task_group == "Appointment & Scheduling": task_view = task_view[task_view.task_domain == "Appointment & scheduling"]
        elif task_group == "Care Coordination": task_view = task_view[~task_view.task_domain.isin(["Appointment & scheduling", "SDOH & access"])]
        elif task_group == "Access & Support": task_view = task_view[task_view.task_domain == "SDOH & access"]
        elif task_group in STATE_ORDER[:3]: task_view = task_view[task_view.workflow_label == task_group]
        if search: task_view = task_view[task_view.patient_id.str.contains(search, case=False, na=False) | task_view.outstanding_task.str.contains(search, case=False, na=False)]
        # One worklist row per episode; detail retains all episode-specific tasks.
        view = patients.merge(task_view[["patient_id", "discharge_date"]].drop_duplicates(), on=["patient_id", "discharge_date"], how="inner")

    total_pages = max(1, ceil(len(view) / PAGE_SIZE))
    page = min(int(st.session_state.get("patient_page", 1)), total_pages)
    chosen = selected_row(view)
    if chosen is not None:
        with st.container(key="mobile_snapshot"):
            st.markdown(snapshot_html(chosen), unsafe_allow_html=True)
    left, right = st.columns([.82, 1.45], gap="large")
    with left:
        st.caption(f"{len(view):,} episodes · page {page} of {total_pages} · Patient | Stroke Type | Discharge | Days | Priority | Outstanding Need")
        shown = view.iloc[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]
        for _, row in shown.iterrows():
            key = episode_key(row)
            patient_tasks = tasks[(tasks.patient_id == row.patient_id) & (tasks.discharge_date == row.discharge_date)] if not tasks.empty else tasks
            need = "Transition closed" if patient_tasks.empty else str(patient_tasks.iloc[0].outstanding_task).replace("STCC", "Stroke clinic")
            priority = "Complete" if row.workflow_label == "Transition Complete" else row.workflow_category
            selected = st.session_state.get("selected_episode") == key
            with st.container(key=f"{'selected_' if selected else ''}row_{row.patient_id}_{key[1]}"):
                if st.button(f"**Patient {number(row.patient_id)}** · {row.stroke_type}  \n{row.discharge_date:%b %d, %Y} · Day {int(row.days_since_discharge)} · **{priority}**  \n{need}", key=f"open_{mode}_{row.patient_id}_{key[1]}", width="stretch"):
                    st.session_state.selected_episode = key
                    st.rerun()
        p1, p2 = st.columns(2)
        if p1.button("← Previous", disabled=page == 1, width="stretch"):
            st.session_state.patient_page = page - 1; st.rerun()
        if p2.button("Next →", disabled=page == total_pages, width="stretch"):
            st.session_state.patient_page = page + 1; st.rerun()
    with right:
        with st.container(key="desktop_snapshot"):
            if chosen is None:
                st.info("Select a patient episode from the worklist to open the Patient Snapshot here.")
            else:
                render_snapshot(chosen, "shared")

with st.expander("Workflow definitions & history"):
    st.markdown("**Appointment Needed · Tasks Pending** — visit incomplete and transition tasks remain.  \n**Appointment Needed · Tasks Complete** — transition tasks are complete while the visit remains scheduled or needed.  \n**Appointment Completed · Tasks Pending** — clinic visit occurred, but unresolved work remains.  \n**Transition Complete** — clinic visit and all applicable transition tasks are complete. History remains available through the Patient group filter.")
    st.caption(f"Current as of {as_of:%B %d, %Y} · {len(patients):,} eligible episodes · counts are calculated from episode data")

with st.expander("HOW PATIENTS ARE PRIORITIZED"):
    st.markdown("**Immediate Action Required**  \nTime-sensitive follow-up issue such as a cancelled/no-show visit, a scheduled visit date that has passed without completion, an unscheduled patient beyond the configured outreach threshold, or multiple unresolved care needs combined with a documented access barrier.\n\n**Action Needed**  \nFollow-up or transition-care work remains, but the episode does not meet the Immediate Action Required threshold.\n\n**On Track**  \nThe stroke clinic appointment is scheduled within the target follow-up window and there are no documented pre-visit actions requiring attention.")
    st.caption("Priority is calculated automatically from appointment timing, unresolved care needs, and documented barriers. It is not manually assigned.")
