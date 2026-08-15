# Stroke Transitions of Care Clinic Prioritization Dashboard

A Streamlit prototype that turns a synthetic stroke transitions-of-care dataset into transparent, actionable patient and task work queues.

## What it does

- Separates ineligible patients into an Alternative Transition Pathway.
- Presents a compact master-detail worklist, with the selected episode's snapshot and actions beside the cohort.
- Organizes every eligible episode into one of four deterministic states: **Appointment Needed · Tasks Pending**, **Appointment Needed · Tasks Complete**, **Appointment Completed · Tasks Pending**, or **Transition Complete**.
- Assigns explainable operational priorities: **Immediate Action Required**, **Action Needed**, and **On Track**.
- Creates team-oriented work queues for scheduling, medication/prevention, monitoring, workup, rehabilitation, referrals, and access barriers.
- Displays stroke severity and functional information as context without using it to determine workflow priority.

This is a synthetic educational prototype, not a validated clinical risk score or prediction model.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

The included representative population of 200 synthetic patients loads by default. Repeat hospitalizations remain separate episodes. Use the sidebar uploader to inspect another CSV with the same schema.

## Test

```bash
python -m pytest -q
```

The effective date and the 14-day follow-up and 7-day unscheduled-outreach assumptions can be adjusted in the dashboard sidebar.
