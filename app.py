import streamlit as st
from datetime import date, time

from pawpal_system import Owner, Pet, Task, Priority, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "tasks" not in st.session_state:
    st.session_state.tasks = []   # list[dict]: title, duration_min, priority
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
            st.session_state.plan = None  # invalidate stale plan
with col_clear:
    if st.button("Clear tasks"):
        st.session_state.tasks = []
        st.session_state.plan = None

if st.session_state.tasks:
    filter_priorities = st.multiselect(
        "Filter by priority",
        ["HIGH", "MEDIUM", "LOW"],
        default=["HIGH", "MEDIUM", "LOW"],
        key="filter_priorities",
    )
    displayed = [t for t in st.session_state.tasks if t["priority"] in filter_priorities]
    st.dataframe(displayed, use_container_width=True)
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

    conflicts = plan.detect_conflicts()
    if conflicts:
        for a, b in conflicts:
            st.warning(
                f"Conflict: **{a.task.title}** ({a.start_time_str()}–{a.end_time_str()}) "
                f"overlaps **{b.task.title}** ({b.start_time_str()}–{b.end_time_str()})"
            )

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
            st.markdown(f"- **{et.task.title}** — {et.reason}")

    with st.expander("Full plan summary"):
        st.text(plan.summary())
