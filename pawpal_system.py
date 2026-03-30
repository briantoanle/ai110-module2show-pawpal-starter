# this will be the backend logic of the app

from enum import Enum


# ---------------------------------------------------------------------------
# Priority
# ---------------------------------------------------------------------------

class Priority(Enum):
    """Enumeration of task priority levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    def numeric_value(self) -> int:
        """Return an integer representation of the priority level."""
        # TODO: implement (e.g. LOW=1, MEDIUM=2, HIGH=3)
        pass


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

class Task:
    """A pet-care task with a title, duration, and priority."""

    def __init__(self, title: str, duration_min: int, priority: Priority):
        self.title: str = title
        self.duration_min: int = duration_min
        self.priority: Priority = priority

    def is_valid(self) -> bool:
        """Return True if the task has a non-empty title and positive duration."""
        # TODO: implement validation logic
        pass

    def __repr__(self) -> str:
        # TODO: implement
        pass


# ---------------------------------------------------------------------------
# ScheduledTask
# ---------------------------------------------------------------------------

class ScheduledTask:
    """A Task that has been placed at a specific start time in the day."""

    def __init__(self, task: Task, start_min: int, reason: str):
        self.task: Task = task
        self.start_min: int = start_min
        self.reason: str = reason

    def start_time_str(self) -> str:
        """Return the start time as a human-readable string (e.g. '09:00')."""
        # TODO: implement (convert minutes-since-midnight to HH:MM)
        pass

    def end_time_str(self) -> str:
        """Return the end time as a human-readable string (e.g. '09:30')."""
        # TODO: implement
        pass

    def duration_min(self) -> int:
        """Return the duration of the wrapped task in minutes."""
        # TODO: delegate to self.task.duration_min
        pass

    def __repr__(self) -> str:
        # TODO: implement
        pass


# ---------------------------------------------------------------------------
# ExcludedTask
# ---------------------------------------------------------------------------

class ExcludedTask:
    """A Task that could not be scheduled, along with the reason why."""

    def __init__(self, task: Task, reason: str):
        self.task: Task = task
        self.reason: str = reason

    def __repr__(self) -> str:
        # TODO: implement
        pass


# ---------------------------------------------------------------------------
# DailyPlan
# ---------------------------------------------------------------------------

class DailyPlan:
    """The full schedule for a single day, including scheduled and excluded tasks."""

    def __init__(self, date: str, total_available_min: int):
        self.date: str = date
        self.total_available_min: int = total_available_min
        self.scheduled: list[ScheduledTask] = []
        self.excluded: list[ExcludedTask] = []

    def add_scheduled(self, st: ScheduledTask) -> None:
        """Append a ScheduledTask to the scheduled list."""
        # TODO: implement
        pass

    def add_excluded(self, et: ExcludedTask) -> None:
        """Append an ExcludedTask to the excluded list."""
        # TODO: implement
        pass

    def total_used_min(self) -> int:
        """Return the sum of minutes used by all scheduled tasks."""
        # TODO: implement
        pass

    def utilization_pct(self) -> float:
        """Return the percentage of available time that is used (0–100)."""
        # TODO: implement (total_used_min / total_available_min * 100)
        pass

    def summary(self) -> str:
        """Return a human-readable summary of the daily plan."""
        # TODO: implement
        pass

    def __repr__(self) -> str:
        # TODO: implement
        pass


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

class Pet:
    """Represents a pet owned by an Owner."""

    def __init__(self, name: str, species: str, age_years: float, notes: str = ""):
        self.name: str = name
        self.species: str = species
        self.age_years: float = age_years
        self.notes: str = notes

    def __repr__(self) -> str:
        # TODO: implement
        pass


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner with their available time window and list of pets."""

    def __init__(self, name: str, available_start_min: int, available_end_min: int):
        self.name: str = name
        self.available_start_min: int = available_start_min
        self.available_end_min: int = available_end_min
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a Pet to this owner's pet list."""
        # TODO: implement
        pass

    def total_available_min(self) -> int:
        """Return the total number of available minutes in the owner's window."""
        # TODO: implement (available_end_min - available_start_min)
        pass

    def __repr__(self) -> str:
        # TODO: implement
        pass


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Builds a DailyPlan by scheduling tasks within an owner's available window."""

    _PRIORITY_ORDER: dict = {
        Priority.HIGH: 0,
        Priority.MEDIUM: 1,
        Priority.LOW: 2,
    }

    def build_plan(self, owner: Owner, pet: Pet, tasks: list, date: str) -> DailyPlan:
        """
        Create and return a DailyPlan for the given owner, pet, tasks, and date.

        Tasks are sorted by priority (high → low) and greedily scheduled into
        the owner's available window. Tasks that don't fit are excluded.
        """
        # TODO: implement
        pass

    def _sort_tasks(self, tasks: list) -> list:
        """Return a new list of tasks sorted by priority (high first)."""
        # TODO: implement using _PRIORITY_ORDER
        pass

    def _fits(self, task: Task, current_min: int, end_min: int) -> bool:
        """Return True if the task can start at current_min and finish before end_min."""
        # TODO: implement
        pass

    def _make_reason(self, task: Task, start_min: int) -> str:
        """Return a human-readable reason string for scheduling a task at start_min."""
        # TODO: implement
        pass

    def _make_exclusion_reason(self, task: Task, remaining_min: int) -> str:
        """Return a human-readable reason string for excluding a task."""
        # TODO: implement
        pass