# this will be the backend logic of the app

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import ClassVar


# ---------------------------------------------------------------------------
# Priority
# ---------------------------------------------------------------------------

class Priority(Enum):
    """Enumeration of task priority levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class Task:
    """A pet-care task with a title, duration, priority, frequency, and completion status."""

    def __init__(
        self,
        title: str,
        duration_min: int,
        priority: Priority,
        frequency: str = "daily",
        completed: bool = False,
    ):
        """Initialize a Task with title, duration, priority, frequency, and completion status."""
        if not isinstance(priority, Priority):
            raise TypeError(
                f"priority must be a Priority enum member, got {type(priority).__name__!r}"
            )
        self.title: str = title
        self.duration_min: int = duration_min
        self.priority: Priority = priority
        self.frequency: str = frequency      # e.g. "daily", "weekly", "as needed"
        self.completed: bool = completed

    def is_valid(self) -> bool:
        """Return True if the task has a non-empty title and positive duration."""
        return bool(self.title.strip()) and self.duration_min >= 1 and isinstance(self.priority, Priority)

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def next_occurrence(self) -> "Task | None":
        """Return a new incomplete Task for the next occurrence, or None if frequency is 'as needed'."""
        if self.frequency in ("daily", "weekly"):
            return Task(self.title, self.duration_min, self.priority, self.frequency)
        return None

    def mark_incomplete(self) -> None:
        """Reset the task to incomplete."""
        self.completed = False

    def __repr__(self) -> str:
        """Return a debug string showing title, duration, priority, frequency, and status."""
        status = "done" if self.completed else "pending"
        return f"Task({self.title!r}, {self.duration_min} min, {self.priority.value}, {self.frequency}, {status})"


# ---------------------------------------------------------------------------
# ScheduledTask
# ---------------------------------------------------------------------------

class ScheduledTask:
    """A Task that has been placed at a specific start time in the day."""

    def __init__(self, task: Task, start_min: int, reason: str):
        """Store the wrapped task, its start time in minutes from midnight, and scheduling reason."""
        self.task: Task = task
        self.start_min: int = start_min
        self.reason: str = reason

    def start_time_str(self) -> str:
        """Return the start time as a human-readable string (e.g. '09:00')."""
        return f"{self.start_min // 60:02d}:{self.start_min % 60:02d}"

    def end_time_str(self) -> str:
        """Return the end time as a human-readable string (e.g. '09:30')."""
        end = self.start_min + self.task.duration_min
        return f"{end // 60:02d}:{end % 60:02d}"

    # Fix #5: renamed from duration_min() to get_duration_min() to avoid
    # shadowing Task.duration_min (int attribute vs method name collision).
    def get_duration_min(self) -> int:
        """Return the duration of the wrapped task in minutes."""
        return self.task.duration_min

    def __repr__(self) -> str:
        """Return a debug string showing the task title and its scheduled time window."""
        return f"ScheduledTask({self.task.title!r}, {self.start_time_str()}–{self.end_time_str()})"


# ---------------------------------------------------------------------------
# ExcludedTask
# ---------------------------------------------------------------------------

class ExcludedTask:
    """A Task that could not be scheduled, along with the reason why."""

    def __init__(self, task: Task, reason: str):
        """Store the task that was excluded and the reason it could not be scheduled."""
        self.task: Task = task
        self.reason: str = reason

    def __repr__(self) -> str:
        """Return a debug string showing the excluded task title and reason."""
        return f"ExcludedTask({self.task.title!r}, reason={self.reason!r})"


# ---------------------------------------------------------------------------
# DailyPlan
# ---------------------------------------------------------------------------

class DailyPlan:
    """The full schedule for a single day, including scheduled and excluded tasks."""

    # Fix #2 & #4: added owner_name and pet_name so each plan retains context
    # about who and which pet it was built for.
    def __init__(
        self,
        date: str,
        total_available_min: int,
        owner_name: str = "",
        pet_name: str = "",
    ):
        """Initialize an empty daily plan for the given date and available time window."""
        self.date: str = date
        self.total_available_min: int = total_available_min
        self.owner_name: str = owner_name  # Fix #2
        self.pet_name: str = pet_name       # Fix #4
        self.scheduled: list[ScheduledTask] = []
        self.excluded: list[ExcludedTask] = []
        self._used_min: int = 0

    def add_scheduled(self, st: ScheduledTask) -> None:
        """Append a ScheduledTask to the scheduled list."""
        self.scheduled.append(st)
        self._used_min += st.get_duration_min()

    def add_excluded(self, et: ExcludedTask) -> None:
        """Append an ExcludedTask to the excluded list."""
        self.excluded.append(et)

    def total_used_min(self) -> int:
        """Return the sum of minutes used by all scheduled tasks."""
        return self._used_min

    def utilization_pct(self) -> float:
        """Return the percentage of available time used (0–100), or 0.0 if no time is available."""
        if self.total_available_min == 0:
            return 0.0
        return self.total_used_min() / self.total_available_min * 100

    def summary(self) -> str:
        """Return a human-readable summary of the daily plan."""
        lines = [f"Daily Plan for {self.pet_name} ({self.date}) — Owner: {self.owner_name}",
                 f"Available: {self.total_available_min} min | Used: {self.total_used_min()} min "
                 f"({self.utilization_pct():.1f}%)", ""]
        if self.scheduled:
            lines.append("Scheduled tasks:")
            for st in self.scheduled:
                lines.append(f"  {st.start_time_str()}–{st.end_time_str()}  {st.task.title} "
                             f"[{st.task.priority.value}]  — {st.reason}")
        else:
            lines.append("No tasks could be scheduled.")
        if self.excluded:
            lines.append("")
            lines.append("Excluded tasks:")
            for et in self.excluded:
                lines.append(f"  {et.task.title} — {et.reason}")
        return "\n".join(lines)

    def detect_conflicts(self) -> list[tuple[ScheduledTask, ScheduledTask]]:
        """Return pairs of ScheduledTasks whose time windows overlap.

        Because the greedy scheduler places tasks sequentially this should
        always be empty, but the check is useful as a safety net when tasks
        are added to the plan manually or via future scheduling strategies.
        """
        conflicts: list[tuple[ScheduledTask, ScheduledTask]] = []
        by_time = sorted(self.scheduled, key=lambda s: s.start_min)
        for i in range(len(by_time) - 1):
            a = by_time[i]
            a_end = a.start_min + a.task.duration_min
            b = by_time[i + 1]
            if b.start_min < a_end:
                conflicts.append((a, b))
        return conflicts

    def scheduled_by_time(self) -> list[ScheduledTask]:
        """Return scheduled tasks sorted by start time ascending."""
        return sorted(self.scheduled, key=lambda s: s.start_min)

    def __repr__(self) -> str:
        """Return a debug string showing the date and counts of scheduled and excluded tasks."""
        return (f"DailyPlan(date={self.date!r}, scheduled={len(self.scheduled)}, "
                f"excluded={len(self.excluded)})")


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

class Pet:
    """Represents a pet owned by an Owner, with its own list of care tasks."""

    def __init__(self, name: str, species: str, age_years: float, notes: str = ""):
        """Initialize a Pet with identifying details and an empty task list."""
        self.name: str = name
        self.species: str = species
        self.age_years: float = age_years
        self.notes: str = notes
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet. Raises ValueError if a task with the same title already exists."""
        if any(t.title == task.title for t in self.tasks):
            raise ValueError(f"Task {task.title!r} already exists for pet {self.name!r}.")
        self.tasks.append(task)

    def remove_task(self, title: str) -> None:
        """Remove a task by title. Raises ValueError if not found."""
        for i, t in enumerate(self.tasks):
            if t.title == title:
                self.tasks.pop(i)
                return
        raise ValueError(f"No task with title {title!r} found for pet {self.name!r}.")

    def complete_task(self, title: str) -> None:
        """Mark a task complete by title and re-queue it if it recurs (daily/weekly)."""
        for task in self.tasks:
            if task.title == title and not task.completed:
                task.mark_complete()
                next_task = task.next_occurrence()
                if next_task is not None:
                    self.tasks.append(next_task)
                return
        raise ValueError(f"No pending task with title {title!r} found for pet {self.name!r}.")

    def get_pending_tasks(self) -> list[Task]:
        """Return all tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def __repr__(self) -> str:
        """Return a debug string showing the pet's name, species, age, and task count."""
        return f"Pet({self.name!r}, species={self.species!r}, age={self.age_years}, tasks={len(self.tasks)})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner with their available time window and list of pets."""

    def __init__(self, name: str, available_start_min: int, available_end_min: int):
        """Initialize an Owner with a name, available time window (minutes from midnight), and empty pet list."""
        # Fix #7: guard against an inverted or midnight-spanning time window
        if available_start_min >= available_end_min:
            raise ValueError(
                f"available_start_min ({available_start_min}) must be less than "
                f"available_end_min ({available_end_min}). "
                "Midnight-spanning windows (e.g. 22:00–02:00) are not supported."
            )
        self.name: str = name
        self.available_start_min: int = available_start_min
        self.available_end_min: int = available_end_min
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a Pet to this owner's pet list."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return all tasks across all pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks for a specific pet by name. Raises ValueError if not found."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet.tasks
        raise ValueError(f"No pet named {pet_name!r} found.")

    def total_available_min(self) -> int:
        """Return the total number of available minutes in the owner's window."""
        return self.available_end_min - self.available_start_min

    def __repr__(self) -> str:
        """Return a debug string showing the owner's name, time window, and pet count."""
        return f"Owner({self.name!r}, {self.available_start_min}–{self.available_end_min} min, pets={len(self.pets)})"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Builds a DailyPlan by scheduling tasks within an owner's available window."""

    # Fix #9: annotated as ClassVar so type checkers flag accidental instance
    # mutation; treated as a read-only constant.
    _PRIORITY_ORDER: ClassVar[dict] = {
        Priority.HIGH: 0,
        Priority.MEDIUM: 1,
        Priority.LOW: 2,
    }

    def build_plan(self, owner: Owner, date: str, pet: Pet | None = None) -> DailyPlan:
        """Schedule pending tasks for one pet (or all pets) into the owner's available time window."""
        if pet is not None:
            if pet not in owner.pets:
                raise ValueError(
                    f"Pet {pet.name!r} does not belong to owner {owner.name!r}. "
                    "Add the pet via owner.add_pet() before scheduling."
                )
            pet_name = pet.name
            tasks = pet.get_pending_tasks()
        else:
            pet_name = "all pets"
            tasks = [t for t in owner.get_all_tasks() if not t.completed]

        plan = DailyPlan(date, owner.total_available_min(), owner.name, pet_name)
        current_min = owner.available_start_min
        overflow: list[Task] = []

        for task in self._sort_tasks(tasks):
            if not self._is_due(task, date):
                plan.add_excluded(ExcludedTask(task, f"Not due today (frequency: {task.frequency})."))
            elif self._fits(task, current_min, owner.available_end_min):
                plan.add_scheduled(ScheduledTask(task, current_min, self._make_reason(task, current_min)))
                current_min += task.duration_min
            else:
                overflow.append(task)

        # Second pass: fill remaining time with tasks that didn't fit earlier.
        for task in overflow:
            if self._fits(task, current_min, owner.available_end_min):
                plan.add_scheduled(ScheduledTask(task, current_min, self._make_reason(task, current_min)))
                current_min += task.duration_min
            else:
                remaining = owner.available_end_min - current_min
                plan.add_excluded(ExcludedTask(task, self._make_exclusion_reason(task, remaining)))

        return plan

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by priority descending, then duration ascending, then title for determinism."""
        return sorted(tasks, key=lambda t: (self._PRIORITY_ORDER[t.priority], t.duration_min, t.title))

    def _fits(self, task: Task, current_min: int, end_min: int) -> bool:
        """Return True if the task can start at current_min and finish before end_min."""
        return task.duration_min <= (end_min - current_min)

    def _make_reason(self, task: Task, start_min: int) -> str:
        """Return a human-readable reason string for scheduling a task at start_min."""
        h, m = divmod(start_min, 60)
        return f"Scheduled at {h:02d}:{m:02d} ({task.duration_min} min). {task.priority.value.capitalize()} priority."

    def _is_due(self, task: Task, date_str: str) -> bool:
        """Return True if the task is due on the given date based on its frequency.

        - 'daily' and 'as needed': always due.
        - 'weekly': due only on Mondays (weekday == 0).
        """
        if task.frequency == "weekly":
            return datetime.strptime(date_str, "%Y-%m-%d").weekday() == 0
        return True

    def _make_exclusion_reason(self, task: Task, remaining_min: int) -> str:
        """Return a human-readable reason string for excluding a task."""
        return f"Excluded: needed {task.duration_min} min but only {remaining_min} min remained in the day."

    @staticmethod
    def filter_tasks(
        tasks: list[Task],
        priority: Priority | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """Return tasks filtered by optional priority and/or completion status.

        Pass ``priority=Priority.HIGH`` to keep only high-priority tasks.
        Pass ``completed=False`` to keep only pending tasks.
        Omit a parameter (or pass ``None``) to skip that filter.
        """
        result = tasks
        if priority is not None:
            result = [t for t in result if t.priority == priority]
        if completed is not None:
            result = [t for t in result if t.completed == completed]
        return result