import json
import streamlit as st
from datetime import date, time
from pathlib import Path

from pawpal_system import Owner, Pet, Task, Priority, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------
_SAVE_FILE = Path("pawpal_tasks.json")

def _load_tasks() -> list:
    if _SAVE_FILE.exists():
        try:
            return json.loads(_SAVE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []

def _save_tasks(tasks: list) -> None:
    _SAVE_FILE.write_text(json.dumps(tasks, indent=2))

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "tasks" not in st.session_state:
    st.session_state.tasks = _load_tasks()
if "plan" not in st.session_state:
    st.session_state.plan = None  # DailyPlan | None

# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------
st.subheader("Owner")
col1, col2, col3 = st.columns(3)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    start_time = st.time_input("Available from", value=time(7, 0))
with col3:
    end_time = st.time_input("Available until", value=time(9, 0))

# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------
st.subheader("Pet")
col1, col2, col3 = st.columns(3)
with col1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col3:
    age = st.number_input("Age (years)", min_value=0.0, max_value=30.0, value=3.0, step=0.5)

# ---------------------------------------------------------------------------
# Task management
# ---------------------------------------------------------------------------
st.subheader("Tasks")
col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["HIGH", "MEDIUM", "LOW"])
with col4:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "as needed"])

col_add, col_clear = st.columns(2)
with col_add:
    if st.button("Add task"):
        stripped = task_title.strip()
        if not stripped:
            st.warning("Task title cannot be empty.")
        elif any(t["title"] == stripped for t in st.session_state.tasks):
            st.warning(f"A task named '{stripped}' already exists.")
        else:
            st.session_state.tasks.append({
                "title": stripped,
                "duration_min": int(duration),
                "priority": priority,
                "frequency": frequency,
            })
            _save_tasks(st.session_state.tasks)
            st.session_state.plan = None  # invalidate stale plan
with col_clear:
    if st.button("Clear tasks"):
        st.session_state.tasks = []
        _save_tasks(st.session_state.tasks)
        st.session_state.plan = None

if st.session_state.tasks:
    filter_priorities = st.multiselect(
        "Filter by priority",
        ["HIGH", "MEDIUM", "LOW"],
        default=["HIGH", "MEDIUM", "LOW"],
        key="filter_priorities",
    )
    _PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    _PRIORITY_ICON = {"HIGH": "🔴 HIGH", "MEDIUM": "🟡 MEDIUM", "LOW": "🟢 LOW"}
    displayed = sorted(
        [t for t in st.session_state.tasks if t["priority"] in filter_priorities],
        key=lambda t: (_PRIORITY_ORDER.get(t["priority"], 9), t["duration_min"], t["title"]),
    )
    if displayed:
        table_rows = [
            {
                "Priority": _PRIORITY_ICON.get(t["priority"], t["priority"]),
                "Title": t["title"],
                "Duration (min)": t["duration_min"],
                "Frequency": t["frequency"],
            }
            for t in displayed
        ]
        st.table(table_rows)
    else:
        st.info("No tasks match the selected priorities.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Schedule generation
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")
schedule_date = st.date_input("Date", value=date.today())

if st.button("Generate schedule", type="primary"):
    if not st.session_state.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        start_min = start_time.hour * 60 + start_time.minute
        end_min = end_time.hour * 60 + end_time.minute
        try:
            owner = Owner(owner_name, start_min, end_min)
            pet = Pet(pet_name, species, float(age))
            for t in st.session_state.tasks:
                pet.add_task(Task(
                    title=t["title"],
                    duration_min=t["duration_min"],
                    priority=Priority[t["priority"]],
                    frequency=t.get("frequency", "daily"),
                ))
            owner.add_pet(pet)
            st.session_state.plan = Scheduler().build_plan(owner, str(schedule_date), pet)
        except ValueError as e:
            st.error(str(e))

# ---------------------------------------------------------------------------
# Plan display
# ---------------------------------------------------------------------------
if st.session_state.plan:
    plan = st.session_state.plan

    col1, col2, col3 = st.columns(3)
    col1.metric("Available", f"{plan.total_available_min} min")
    col2.metric("Used", f"{plan.total_used_min()} min")
    col3.metric("Utilization", f"{plan.utilization_pct():.1f}%")

    util = plan.utilization_pct()
    if util <= 75:
        st.success(f"Schedule looks good — {util:.1f}% of available time used.")
    elif util <= 95:
        st.warning(f"Schedule is fairly full — {util:.1f}% of available time used.")
    else:
        st.error(f"Schedule is over-packed — {util:.1f}% of available time used.")

    conflicts = Scheduler().detect_conflicts(plan)
    if conflicts:
        for a, b in conflicts:
            st.warning(
                f"Conflict: **{a.task.title}** ({a.start_time_str()}–{a.end_time_str()}) "
                f"overlaps **{b.task.title}** ({b.start_time_str()}–{b.end_time_str()})"
            )
    else:
        st.success("No scheduling conflicts detected.")

    if plan.scheduled:
        st.markdown("### Scheduled Tasks *(sorted by time)*")
        priority_colors = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}
        for st_task in plan.scheduled_by_time():
            icon = priority_colors.get(st_task.task.priority.value, "")
            freq_badge = (
                f" *({st_task.task.frequency})*" if st_task.task.frequency != "daily" else ""
            )
            st.markdown(
                f"**{st_task.start_time_str()} – {st_task.end_time_str()}** &nbsp; "
                f"{icon} {st_task.task.title}{freq_badge}  \n"
                f"<small>{st_task.reason}</small>",
                unsafe_allow_html=True,
            )

    if plan.excluded:
        st.markdown("### Excluded Tasks")
        for et in plan.excluded:
            st.warning(f"**{et.task.title}** — {et.reason}")

    with st.expander("Full plan summary"):
        st.text(plan.summary())
