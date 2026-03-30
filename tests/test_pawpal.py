import pytest
from pawpal_system import Task, Pet, Priority, Owner, Scheduler, DailyPlan, ScheduledTask, ExcludedTask


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def scheduler():
    return Scheduler()


@pytest.fixture
def owner():
    """Owner with a 2-hour window (09:00–11:00 = 540–660 min = 120 min total)."""
    return Owner("Alice", available_start_min=540, available_end_min=660)


@pytest.fixture
def pet(owner):
    p = Pet("Buddy", "Dog", age_years=3)
    owner.add_pet(p)
    return p


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status():
    """Task completion: mark_complete() should set completed to True."""
    task = Task("Morning Walk", duration_min=30, priority=Priority.HIGH)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_mark_incomplete_resets_status():
    task = Task("Evening Walk", duration_min=20, priority=Priority.LOW)
    task.mark_complete()
    task.mark_incomplete()
    assert task.completed is False


def test_is_valid_normal_task():
    task = Task("Feed", duration_min=10, priority=Priority.MEDIUM)
    assert task.is_valid() is True


def test_is_valid_empty_title():
    task = Task("   ", duration_min=10, priority=Priority.MEDIUM)
    assert task.is_valid() is False


def test_is_valid_zero_duration():
    task = Task("Groom", duration_min=0, priority=Priority.LOW)
    assert task.is_valid() is False


def test_invalid_priority_raises():
    with pytest.raises(TypeError):
        Task("Walk", duration_min=10, priority="HIGH")


# ---------------------------------------------------------------------------
# Task.next_occurrence
# ---------------------------------------------------------------------------

def test_next_occurrence_daily_returns_new_task():
    task = Task("Feed", duration_min=10, priority=Priority.HIGH, frequency="daily")
    task.mark_complete()
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.completed is False
    assert nxt.title == task.title


def test_next_occurrence_weekly_returns_new_task():
    task = Task("Bath", duration_min=30, priority=Priority.MEDIUM, frequency="weekly")
    task.mark_complete()
    nxt = task.next_occurrence()
    assert nxt is not None
    assert nxt.completed is False


def test_next_occurrence_as_needed_returns_none():
    task = Task("Vet Visit", duration_min=60, priority=Priority.HIGH, frequency="as needed")
    task.mark_complete()
    assert task.next_occurrence() is None


def test_next_occurrence_unknown_frequency_returns_none():
    task = Task("Monthly Trim", duration_min=20, priority=Priority.LOW, frequency="monthly")
    assert task.next_occurrence() is None


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

def test_add_task_increases_pet_task_count():
    """Task addition: adding a task to a Pet should increase its task count by 1."""
    pet = Pet(name="Buddy", species="Dog", age_years=3)
    assert len(pet.tasks) == 0
    pet.add_task(Task("Feed Breakfast", duration_min=10, priority=Priority.MEDIUM))
    assert len(pet.tasks) == 1


def test_add_duplicate_task_raises():
    pet = Pet("Milo", "Cat", age_years=2)
    pet.add_task(Task("Feed", duration_min=5, priority=Priority.HIGH))
    with pytest.raises(ValueError):
        pet.add_task(Task("Feed", duration_min=5, priority=Priority.HIGH))


def test_remove_task_decreases_count():
    pet = Pet("Milo", "Cat", age_years=2)
    pet.add_task(Task("Feed", duration_min=5, priority=Priority.HIGH))
    pet.remove_task("Feed")
    assert len(pet.tasks) == 0


def test_remove_nonexistent_task_raises():
    pet = Pet("Milo", "Cat", age_years=2)
    with pytest.raises(ValueError):
        pet.remove_task("Nonexistent")


def test_get_pending_tasks_excludes_completed():
    pet = Pet("Rex", "Dog", age_years=5)
    t1 = Task("Walk", duration_min=30, priority=Priority.HIGH)
    t2 = Task("Feed", duration_min=10, priority=Priority.MEDIUM)
    t1.mark_complete()
    pet.add_task(t1)
    pet.add_task(t2)
    pending = pet.get_pending_tasks()
    assert len(pending) == 1
    assert pending[0].title == "Feed"


def test_complete_task_requeues_daily():
    """Completing a daily task should append a new pending occurrence."""
    pet = Pet("Buddy", "Dog", age_years=3)
    pet.add_task(Task("Feed", duration_min=10, priority=Priority.HIGH, frequency="daily"))
    pet.complete_task("Feed")
    assert len(pet.tasks) == 2
    assert pet.tasks[0].completed is True
    assert pet.tasks[1].completed is False


def test_complete_task_does_not_requeue_as_needed():
    pet = Pet("Buddy", "Dog", age_years=3)
    pet.add_task(Task("Vet", duration_min=60, priority=Priority.HIGH, frequency="as needed"))
    pet.complete_task("Vet")
    assert len(pet.tasks) == 1
    assert pet.tasks[0].completed is True


def test_complete_nonexistent_task_raises():
    pet = Pet("Buddy", "Dog", age_years=3)
    with pytest.raises(ValueError):
        pet.complete_task("Nonexistent")


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

def test_owner_inverted_window_raises():
    with pytest.raises(ValueError):
        Owner("Bob", available_start_min=660, available_end_min=540)


def test_owner_equal_window_raises():
    with pytest.raises(ValueError):
        Owner("Bob", available_start_min=540, available_end_min=540)


def test_owner_total_available_min():
    owner = Owner("Alice", available_start_min=540, available_end_min=660)
    assert owner.total_available_min() == 120


def test_owner_get_tasks_for_unknown_pet_raises():
    owner = Owner("Alice", available_start_min=540, available_end_min=660)
    with pytest.raises(ValueError):
        owner.get_tasks_for_pet("Ghost")


def test_owner_get_all_tasks_across_pets():
    owner = Owner("Alice", available_start_min=540, available_end_min=660)
    p1 = Pet("Buddy", "Dog", age_years=3)
    p2 = Pet("Milo", "Cat", age_years=1)
    p1.add_task(Task("Walk", duration_min=30, priority=Priority.HIGH))
    p2.add_task(Task("Feed", duration_min=10, priority=Priority.MEDIUM))
    owner.add_pet(p1)
    owner.add_pet(p2)
    assert len(owner.get_all_tasks()) == 2


# ---------------------------------------------------------------------------
# Scheduler._sort_tasks
# ---------------------------------------------------------------------------

def test_sort_tasks_priority_order(scheduler):
    tasks = [
        Task("Low Task",  duration_min=10, priority=Priority.LOW),
        Task("High Task", duration_min=10, priority=Priority.HIGH),
        Task("Mid Task",  duration_min=10, priority=Priority.MEDIUM),
    ]
    sorted_tasks = scheduler._sort_tasks(tasks)
    assert sorted_tasks[0].priority == Priority.HIGH
    assert sorted_tasks[1].priority == Priority.MEDIUM
    assert sorted_tasks[2].priority == Priority.LOW


def test_sort_tasks_duration_tiebreak(scheduler):
    """Same priority: shorter duration should come first."""
    tasks = [
        Task("Long",  duration_min=60, priority=Priority.HIGH),
        Task("Short", duration_min=10, priority=Priority.HIGH),
    ]
    sorted_tasks = scheduler._sort_tasks(tasks)
    assert sorted_tasks[0].title == "Short"


def test_sort_tasks_alpha_tiebreak(scheduler):
    """Same priority and duration: alphabetical title ordering."""
    tasks = [
        Task("Zoomies", duration_min=15, priority=Priority.MEDIUM),
        Task("Bath",    duration_min=15, priority=Priority.MEDIUM),
    ]
    sorted_tasks = scheduler._sort_tasks(tasks)
    assert sorted_tasks[0].title == "Bath"


def test_sort_tasks_deterministic(scheduler):
    """Sorting the same list twice gives the same result."""
    tasks = [
        Task("Walk",  duration_min=30, priority=Priority.HIGH),
        Task("Feed",  duration_min=10, priority=Priority.HIGH),
        Task("Groom", duration_min=20, priority=Priority.LOW),
    ]
    assert scheduler._sort_tasks(tasks) == scheduler._sort_tasks(tasks)


# ---------------------------------------------------------------------------
# Scheduler._is_due
# ---------------------------------------------------------------------------

def test_is_due_daily_always_true(scheduler):
    task = Task("Feed", duration_min=10, priority=Priority.HIGH, frequency="daily")
    assert scheduler._is_due(task, "2026-03-24") is True  # Tuesday
    assert scheduler._is_due(task, "2026-03-28") is True  # Saturday


def test_is_due_as_needed_always_true(scheduler):
    task = Task("Vet", duration_min=60, priority=Priority.HIGH, frequency="as needed")
    assert scheduler._is_due(task, "2026-03-25") is True  # Wednesday


def test_is_due_weekly_on_monday(scheduler):
    task = Task("Bath", duration_min=30, priority=Priority.MEDIUM, frequency="weekly")
    assert scheduler._is_due(task, "2026-03-23") is True  # Monday


def test_is_due_weekly_not_monday(scheduler):
    task = Task("Bath", duration_min=30, priority=Priority.MEDIUM, frequency="weekly")
    assert scheduler._is_due(task, "2026-03-24") is False  # Tuesday
    assert scheduler._is_due(task, "2026-03-29") is False  # Sunday


# ---------------------------------------------------------------------------
# Scheduler.build_plan — core scheduling
# ---------------------------------------------------------------------------

def test_build_plan_schedules_fitting_tasks(scheduler, owner, pet):
    pet.add_task(Task("Walk", duration_min=30, priority=Priority.HIGH))
    plan = scheduler.build_plan(owner, "2026-03-23")
    assert len(plan.scheduled) == 1
    assert plan.scheduled[0].task.title == "Walk"


def test_build_plan_excludes_oversized_task(scheduler, owner, pet):
    """A task longer than the full window must be excluded."""
    pet.add_task(Task("Marathon", duration_min=200, priority=Priority.HIGH))
    plan = scheduler.build_plan(owner, "2026-03-23")
    assert len(plan.scheduled) == 0
    assert len(plan.excluded) == 1


def test_build_plan_exact_fit(scheduler, owner, pet):
    """A task equal to total_available_min should be scheduled with nothing left."""
    pet.add_task(Task("Training", duration_min=120, priority=Priority.HIGH))
    plan = scheduler.build_plan(owner, "2026-03-23")
    assert len(plan.scheduled) == 1
    assert plan.total_used_min() == 120
    assert len(plan.excluded) == 0


def test_build_plan_excludes_weekly_on_non_monday(scheduler, owner, pet):
    pet.add_task(Task("Bath", duration_min=30, priority=Priority.MEDIUM, frequency="weekly"))
    plan = scheduler.build_plan(owner, "2026-03-24")  # Tuesday
    assert len(plan.scheduled) == 0
    assert len(plan.excluded) == 1
    assert "frequency" in plan.excluded[0].reason


def test_build_plan_schedules_weekly_on_monday(scheduler, owner, pet):
    pet.add_task(Task("Bath", duration_min=30, priority=Priority.MEDIUM, frequency="weekly"))
    plan = scheduler.build_plan(owner, "2026-03-23")  # Monday
    assert len(plan.scheduled) == 1


def test_build_plan_high_priority_scheduled_before_low(scheduler, owner, pet):
    pet.add_task(Task("Low Task",  duration_min=60, priority=Priority.LOW))
    pet.add_task(Task("High Task", duration_min=60, priority=Priority.HIGH))
    plan = scheduler.build_plan(owner, "2026-03-23")
    assert plan.scheduled[0].task.priority == Priority.HIGH


def test_build_plan_second_pass_rescues_overflow(scheduler, owner, pet):
    """A short low-priority task bumped in pass 1 should be rescued in pass 2."""
    # HIGH task takes 100 min, leaving 20 min; LOW short task fits in the gap
    pet.add_task(Task("Long High", duration_min=100, priority=Priority.HIGH))
    pet.add_task(Task("Short Low", duration_min=20,  priority=Priority.LOW))
    plan = scheduler.build_plan(owner, "2026-03-23")
    titles = [st.task.title for st in plan.scheduled]
    assert "Short Low" in titles
    assert len(plan.excluded) == 0


def test_build_plan_all_tasks_excluded_when_no_time(scheduler):
    """When available window is 1 min, tasks needing more time are excluded."""
    owner = Owner("Bob", available_start_min=540, available_end_min=541)
    pet = Pet("Tiny", "Cat", age_years=1)
    owner.add_pet(pet)
    pet.add_task(Task("Walk", duration_min=30, priority=Priority.HIGH))
    plan = scheduler.build_plan(owner, "2026-03-23")
    assert len(plan.scheduled) == 0
    assert len(plan.excluded) == 1


def test_build_plan_pet_not_belonging_to_owner_raises(scheduler, owner):
    stranger_pet = Pet("Stray", "Cat", age_years=2)
    with pytest.raises(ValueError):
        scheduler.build_plan(owner, "2026-03-23", pet=stranger_pet)


def test_build_plan_for_specific_pet_only(scheduler, owner):
    p1 = Pet("Buddy", "Dog", age_years=3)
    p2 = Pet("Milo",  "Cat", age_years=1)
    owner.add_pet(p1)
    owner.add_pet(p2)
    p1.add_task(Task("Walk", duration_min=30, priority=Priority.HIGH))
    p2.add_task(Task("Feed", duration_min=10, priority=Priority.MEDIUM))
    plan = scheduler.build_plan(owner, "2026-03-23", pet=p1)
    titles = [st.task.title for st in plan.scheduled]
    assert "Walk" in titles
    assert "Feed" not in titles


def test_build_plan_no_tasks_produces_empty_plan(scheduler, owner, pet):
    plan = scheduler.build_plan(owner, "2026-03-23")
    assert len(plan.scheduled) == 0
    assert len(plan.excluded) == 0


# ---------------------------------------------------------------------------
# DailyPlan helpers
# ---------------------------------------------------------------------------

def test_utilization_pct_full():
    plan = DailyPlan("2026-03-23", total_available_min=60)
    task = Task("Walk", duration_min=60, priority=Priority.HIGH)
    plan.add_scheduled(ScheduledTask(task, start_min=540, reason="test"))
    assert plan.utilization_pct() == pytest.approx(100.0)


def test_utilization_pct_zero_available():
    plan = DailyPlan("2026-03-23", total_available_min=0)
    assert plan.utilization_pct() == 0.0


def test_detect_conflicts_no_overlap():
    plan = DailyPlan("2026-03-23", total_available_min=120)
    t1 = Task("Walk", duration_min=30, priority=Priority.HIGH)
    t2 = Task("Feed", duration_min=30, priority=Priority.MEDIUM)
    plan.add_scheduled(ScheduledTask(t1, start_min=540, reason=""))
    plan.add_scheduled(ScheduledTask(t2, start_min=570, reason=""))
    assert plan.detect_conflicts() == []


def test_detect_conflicts_with_overlap():
    plan = DailyPlan("2026-03-23", total_available_min=120)
    t1 = Task("Walk", duration_min=60, priority=Priority.HIGH)
    t2 = Task("Feed", duration_min=30, priority=Priority.MEDIUM)
    plan.add_scheduled(ScheduledTask(t1, start_min=540, reason=""))
    plan.add_scheduled(ScheduledTask(t2, start_min=560, reason=""))  # overlaps t1
    assert len(plan.detect_conflicts()) == 1


def test_scheduled_by_time_order():
    plan = DailyPlan("2026-03-23", total_available_min=120)
    t1 = Task("Feed", duration_min=10, priority=Priority.MEDIUM)
    t2 = Task("Walk", duration_min=30, priority=Priority.HIGH)
    plan.add_scheduled(ScheduledTask(t1, start_min=570, reason=""))
    plan.add_scheduled(ScheduledTask(t2, start_min=540, reason=""))
    ordered = plan.scheduled_by_time()
    assert ordered[0].start_min == 540
    assert ordered[1].start_min == 570


# ---------------------------------------------------------------------------
# ScheduledTask time strings
# ---------------------------------------------------------------------------

def test_scheduled_task_start_time_str():
    task = Task("Walk", duration_min=30, priority=Priority.HIGH)
    st = ScheduledTask(task, start_min=540, reason="")
    assert st.start_time_str() == "09:00"


def test_scheduled_task_end_time_str():
    task = Task("Walk", duration_min=30, priority=Priority.HIGH)
    st = ScheduledTask(task, start_min=540, reason="")
    assert st.end_time_str() == "09:30"


def test_scheduled_task_midnight_boundary():
    task = Task("Late Feed", duration_min=30, priority=Priority.LOW)
    st = ScheduledTask(task, start_min=1410, reason="")  # 23:30
    assert st.start_time_str() == "23:30"
    assert st.end_time_str() == "24:00"


# ---------------------------------------------------------------------------
# Scheduler.filter_tasks
# ---------------------------------------------------------------------------

def test_filter_tasks_by_priority():
    tasks = [
        Task("A", duration_min=10, priority=Priority.HIGH),
        Task("B", duration_min=10, priority=Priority.LOW),
    ]
    result = Scheduler.filter_tasks(tasks, priority=Priority.HIGH)
    assert len(result) == 1
    assert result[0].title == "A"


def test_filter_tasks_by_completed():
    t1 = Task("A", duration_min=10, priority=Priority.HIGH)
    t2 = Task("B", duration_min=10, priority=Priority.LOW)
    t1.mark_complete()
    result = Scheduler.filter_tasks([t1, t2], completed=False)
    assert len(result) == 1
    assert result[0].title == "B"


def test_filter_tasks_combined_filters():
    t1 = Task("A", duration_min=10, priority=Priority.HIGH)
    t2 = Task("B", duration_min=10, priority=Priority.HIGH)
    t1.mark_complete()
    result = Scheduler.filter_tasks([t1, t2], priority=Priority.HIGH, completed=False)
    assert len(result) == 1
    assert result[0].title == "B"


def test_filter_tasks_empty_list():
    assert Scheduler.filter_tasks([]) == []


def test_filter_tasks_no_filters_returns_all():
    tasks = [
        Task("A", duration_min=10, priority=Priority.HIGH),
        Task("B", duration_min=10, priority=Priority.LOW),
    ]
    assert Scheduler.filter_tasks(tasks) == tasks


# ---------------------------------------------------------------------------
# Sorting Correctness: scheduled_by_time returns chronological order
# ---------------------------------------------------------------------------

def test_build_plan_scheduled_by_time_is_chronological(scheduler, owner, pet):
    """Tasks in the built plan must appear in ascending start-time order."""
    pet.add_task(Task("Walk",  duration_min=30, priority=Priority.HIGH))
    pet.add_task(Task("Feed",  duration_min=20, priority=Priority.HIGH))
    pet.add_task(Task("Groom", duration_min=15, priority=Priority.HIGH))
    plan = scheduler.build_plan(owner, "2026-03-23")
    ordered = plan.scheduled_by_time()
    start_times = [st.start_min for st in ordered]
    assert start_times == sorted(start_times)


def test_scheduled_by_time_multiple_tasks_correct_sequence(scheduler, owner, pet):
    """Each task starts exactly where the previous one ended."""
    pet.add_task(Task("A", duration_min=10, priority=Priority.HIGH))
    pet.add_task(Task("B", duration_min=20, priority=Priority.HIGH))
    pet.add_task(Task("C", duration_min=30, priority=Priority.HIGH))
    plan = scheduler.build_plan(owner, "2026-03-23")
    ordered = plan.scheduled_by_time()
    for i in range(len(ordered) - 1):
        current_end = ordered[i].start_min + ordered[i].task.duration_min
        assert ordered[i + 1].start_min == current_end


def test_scheduled_by_time_single_task_is_ordered(scheduler, owner, pet):
    pet.add_task(Task("Solo", duration_min=45, priority=Priority.MEDIUM))
    plan = scheduler.build_plan(owner, "2026-03-23")
    assert plan.scheduled_by_time() == plan.scheduled


def test_scheduled_by_time_stable_across_priority_mix(scheduler, owner, pet):
    """HIGH tasks appear before MEDIUM which appear before LOW in time."""
    pet.add_task(Task("Low Task",  duration_min=10, priority=Priority.LOW))
    pet.add_task(Task("High Task", duration_min=10, priority=Priority.HIGH))
    pet.add_task(Task("Mid Task",  duration_min=10, priority=Priority.MEDIUM))
    plan = scheduler.build_plan(owner, "2026-03-23")
    ordered = plan.scheduled_by_time()
    priorities = [st.task.priority for st in ordered]
    assert priorities == [Priority.HIGH, Priority.MEDIUM, Priority.LOW]


# ---------------------------------------------------------------------------
# Recurrence Logic: daily task completion creates a new pending task
# ---------------------------------------------------------------------------

def test_daily_task_complete_adds_new_pending_task():
    """Completing a daily task must leave exactly one new pending occurrence."""
    pet = Pet("Buddy", "Dog", age_years=3)
    pet.add_task(Task("Feed", duration_min=10, priority=Priority.HIGH, frequency="daily"))
    pet.complete_task("Feed")
    pending = pet.get_pending_tasks()
    assert len(pending) == 1
    assert pending[0].title == "Feed"
    assert pending[0].completed is False


def test_daily_task_complete_preserves_attributes():
    """The re-queued task must carry the same duration, priority, and frequency."""
    pet = Pet("Buddy", "Dog", age_years=3)
    original = Task("Feed", duration_min=15, priority=Priority.MEDIUM, frequency="daily")
    pet.add_task(original)
    pet.complete_task("Feed")
    new_task = pet.get_pending_tasks()[0]
    assert new_task.duration_min == 15
    assert new_task.priority == Priority.MEDIUM
    assert new_task.frequency == "daily"


def test_completing_daily_task_twice_accumulates_occurrences():
    """Each completion of a daily task should add one more pending occurrence."""
    pet = Pet("Buddy", "Dog", age_years=3)
    pet.add_task(Task("Feed", duration_min=10, priority=Priority.HIGH, frequency="daily"))
    pet.complete_task("Feed")   # completes original, adds occurrence #1
    pet.complete_task("Feed")   # completes occurrence #1, adds occurrence #2
    completed = [t for t in pet.tasks if t.completed]
    pending = pet.get_pending_tasks()
    assert len(completed) == 2
    assert len(pending) == 1


def test_weekly_task_complete_also_requeues():
    """Weekly tasks should behave the same as daily — one new pending occurrence."""
    pet = Pet("Buddy", "Dog", age_years=3)
    pet.add_task(Task("Bath", duration_min=30, priority=Priority.MEDIUM, frequency="weekly"))
    pet.complete_task("Bath")
    pending = pet.get_pending_tasks()
    assert len(pending) == 1
    assert pending[0].frequency == "weekly"


def test_as_needed_task_complete_does_not_requeue():
    """'as needed' tasks must not create a new occurrence after completion."""
    pet = Pet("Buddy", "Dog", age_years=3)
    pet.add_task(Task("Vet", duration_min=60, priority=Priority.HIGH, frequency="as needed"))
    pet.complete_task("Vet")
    assert len(pet.get_pending_tasks()) == 0


def test_new_occurrence_is_independent_of_original():
    """Marking the original complete must not affect the new pending task."""
    pet = Pet("Buddy", "Dog", age_years=3)
    pet.add_task(Task("Feed", duration_min=10, priority=Priority.HIGH, frequency="daily"))
    pet.complete_task("Feed")
    original, new_task = pet.tasks[0], pet.tasks[1]
    assert original.completed is True
    assert new_task.completed is False


# ---------------------------------------------------------------------------
# Conflict Detection: Scheduler flags duplicate / overlapping start times
# ---------------------------------------------------------------------------

def test_detect_conflicts_same_start_time():
    """Two tasks starting at the exact same minute must be flagged as a conflict."""
    plan = DailyPlan("2026-03-23", total_available_min=120)
    t1 = Task("Walk", duration_min=30, priority=Priority.HIGH)
    t2 = Task("Feed", duration_min=20, priority=Priority.MEDIUM)
    plan.add_scheduled(ScheduledTask(t1, start_min=540, reason=""))
    plan.add_scheduled(ScheduledTask(t2, start_min=540, reason=""))  # same start
    conflicts = plan.detect_conflicts()
    assert len(conflicts) == 1
    titles = {conflicts[0][0].task.title, conflicts[0][1].task.title}
    assert titles == {"Walk", "Feed"}


def test_detect_conflicts_partial_overlap():
    """Task B starting before task A finishes must be flagged."""
    plan = DailyPlan("2026-03-23", total_available_min=120)
    t1 = Task("Walk", duration_min=60, priority=Priority.HIGH)
    t2 = Task("Feed", duration_min=30, priority=Priority.MEDIUM)
    plan.add_scheduled(ScheduledTask(t1, start_min=540, reason=""))   # 09:00–10:00
    plan.add_scheduled(ScheduledTask(t2, start_min=570, reason=""))   # 09:30–10:00 — overlaps
    assert len(plan.detect_conflicts()) == 1


def test_detect_conflicts_back_to_back_no_conflict():
    """Tasks scheduled consecutively (end of A == start of B) must not conflict."""
    plan = DailyPlan("2026-03-23", total_available_min=120)
    t1 = Task("Walk", duration_min=30, priority=Priority.HIGH)
    t2 = Task("Feed", duration_min=30, priority=Priority.MEDIUM)
    plan.add_scheduled(ScheduledTask(t1, start_min=540, reason=""))   # 09:00–09:30
    plan.add_scheduled(ScheduledTask(t2, start_min=570, reason=""))   # 09:30–10:00
    assert plan.detect_conflicts() == []


def test_detect_conflicts_greedy_plan_is_conflict_free(scheduler, owner, pet):
    """A plan produced by the greedy scheduler must never have conflicts."""
    pet.add_task(Task("Walk",  duration_min=30, priority=Priority.HIGH))
    pet.add_task(Task("Feed",  duration_min=20, priority=Priority.MEDIUM))
    pet.add_task(Task("Groom", duration_min=25, priority=Priority.LOW))
    plan = scheduler.build_plan(owner, "2026-03-23")
    assert plan.detect_conflicts() == []


def test_detect_conflicts_multiple_overlaps():
    """Three mutually overlapping tasks should produce two conflict pairs."""
    plan = DailyPlan("2026-03-23", total_available_min=180)
    t1 = Task("A", duration_min=60, priority=Priority.HIGH)
    t2 = Task("B", duration_min=60, priority=Priority.MEDIUM)
    t3 = Task("C", duration_min=60, priority=Priority.LOW)
    plan.add_scheduled(ScheduledTask(t1, start_min=540, reason=""))   # 09:00–10:00
    plan.add_scheduled(ScheduledTask(t2, start_min=560, reason=""))   # 09:20–10:20 — overlaps A
    plan.add_scheduled(ScheduledTask(t3, start_min=580, reason=""))   # 09:40–10:40 — overlaps B
    assert len(plan.detect_conflicts()) == 2


def test_detect_conflicts_single_task_no_conflict():
    plan = DailyPlan("2026-03-23", total_available_min=60)
    plan.add_scheduled(ScheduledTask(Task("Walk", duration_min=30, priority=Priority.HIGH), 540, ""))
    assert plan.detect_conflicts() == []


def test_detect_conflicts_empty_plan_no_conflict():
    plan = DailyPlan("2026-03-23", total_available_min=60)
    assert plan.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Conflict detection — same pet, two tasks
# ---------------------------------------------------------------------------

def test_same_pet_two_tasks_no_conflict_when_scheduled(scheduler, owner, pet):
    """Greedy scheduler places a single pet's tasks sequentially — no overlap within the plan."""
    pet.add_task(Task("Walk", duration_min=30, priority=Priority.HIGH))
    pet.add_task(Task("Feed", duration_min=20, priority=Priority.MEDIUM))
    plan = scheduler.build_plan(owner, "2026-03-23", pet=pet)
    assert plan.detect_conflicts() == []


def test_same_pet_two_tasks_manual_overlap_detected():
    """Manually-inserted overlapping ScheduledTasks for one pet are caught by DailyPlan.detect_conflicts."""
    plan = DailyPlan("2026-03-23", total_available_min=120, pet_name="Buddy")
    t1 = Task("Walk", duration_min=60, priority=Priority.HIGH)
    t2 = Task("Feed", duration_min=30, priority=Priority.MEDIUM)
    # t2 starts inside t1's window (540+60=600; t2 at 560 < 600)
    plan.add_scheduled(ScheduledTask(t1, start_min=540, reason="manual", pet_name="Buddy"))
    plan.add_scheduled(ScheduledTask(t2, start_min=560, reason="manual", pet_name="Buddy"))
    conflicts = plan.detect_conflicts()
    assert len(conflicts) == 1
    titles = {conflicts[0][0].task.title, conflicts[0][1].task.title}
    assert titles == {"Walk", "Feed"}


def test_same_pet_duplicate_task_title_raises():
    """Pet.add_task rejects a second task whose title already exists on that pet."""
    pet = Pet("Buddy", "Dog", age_years=3)
    pet.add_task(Task("Walk", duration_min=30, priority=Priority.HIGH))
    with pytest.raises(ValueError, match="Walk"):
        pet.add_task(Task("Walk", duration_min=15, priority=Priority.LOW))


def test_same_pet_adjacent_tasks_not_a_conflict():
    """Back-to-back tasks (end of first == start of second) must not be flagged."""
    plan = DailyPlan("2026-03-23", total_available_min=120, pet_name="Buddy")
    t1 = Task("Walk", duration_min=30, priority=Priority.HIGH)
    t2 = Task("Feed", duration_min=20, priority=Priority.MEDIUM)
    plan.add_scheduled(ScheduledTask(t1, start_min=540, reason="manual", pet_name="Buddy"))
    plan.add_scheduled(ScheduledTask(t2, start_min=570, reason="manual", pet_name="Buddy"))  # 540+30
    assert plan.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Conflict detection — two pets, same task title
# ---------------------------------------------------------------------------

def test_two_pets_same_task_title_is_allowed():
    """Different pets may each have a task with the same title — no error raised."""
    p1 = Pet("Buddy", "Dog", age_years=3)
    p2 = Pet("Mochi", "Cat", age_years=2)
    p1.add_task(Task("Morning Walk", duration_min=20, priority=Priority.HIGH))
    p2.add_task(Task("Morning Walk", duration_min=20, priority=Priority.HIGH))
    assert len(p1.tasks) == 1
    assert len(p2.tasks) == 1


def test_two_pets_same_task_independent_plans_conflict_detected(scheduler, owner):
    """When each pet's plan is built independently both start at available_start_min,
    so their same-named tasks occupy the same window. Scheduler.detect_conflicts must flag it."""
    p1 = Pet("Buddy", "Dog", age_years=3)
    p2 = Pet("Mochi", "Cat", age_years=2)
    owner.add_pet(p1)
    owner.add_pet(p2)
    p1.add_task(Task("Morning Walk", duration_min=30, priority=Priority.HIGH))
    p2.add_task(Task("Morning Walk", duration_min=30, priority=Priority.HIGH))

    plan1 = scheduler.build_plan(owner, "2026-03-23", pet=p1)  # 09:00–09:30
    plan2 = scheduler.build_plan(owner, "2026-03-23", pet=p2)  # 09:00–09:30 — overlap

    conflicts = scheduler.detect_conflicts(plan1, plan2)
    assert len(conflicts) == 1
    assert conflicts[0][0].task.title == "Morning Walk"
    assert conflicts[0][1].task.title == "Morning Walk"


def test_two_pets_same_task_combined_plan_no_conflict(scheduler, owner):
    """build_plan without a specific pet schedules all pets sequentially — no overlap."""
    p1 = Pet("Buddy", "Dog", age_years=3)
    p2 = Pet("Mochi", "Cat", age_years=2)
    owner.add_pet(p1)
    owner.add_pet(p2)
    p1.add_task(Task("Morning Walk", duration_min=20, priority=Priority.HIGH))
    p2.add_task(Task("Morning Walk", duration_min=20, priority=Priority.HIGH))

    combined = scheduler.build_plan(owner, "2026-03-23")  # no pet= → all pets sequential
    assert scheduler.detect_conflicts(combined) == []


def test_two_pets_different_task_titles_cross_plan_overlap_detected():
    """Cross-plan conflict detection works even when task titles differ between pets."""
    plan1 = DailyPlan("2026-03-23", total_available_min=120, pet_name="Buddy")
    plan2 = DailyPlan("2026-03-23", total_available_min=120, pet_name="Mochi")
    t1 = Task("Walk",  duration_min=60, priority=Priority.HIGH)
    t2 = Task("Groom", duration_min=30, priority=Priority.MEDIUM)
    plan1.add_scheduled(ScheduledTask(t1, start_min=540, reason="manual", pet_name="Buddy"))
    plan2.add_scheduled(ScheduledTask(t2, start_min=560, reason="manual", pet_name="Mochi"))  # inside t1
    conflicts = Scheduler().detect_conflicts(plan1, plan2)
    assert len(conflicts) == 1
    titles = {conflicts[0][0].task.title, conflicts[0][1].task.title}
    assert titles == {"Walk", "Groom"}
