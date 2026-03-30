# PawPal+

A Streamlit application that helps pet owners build conflict-free daily care schedules. PawPal+ models owners, pets, and tasks as first-class objects, then applies a deterministic priority-first scheduling algorithm to fit as many tasks as possible into the owner's available time window.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture](#architecture)
3. [Core Algorithms](#core-algorithms)
4. [Features](#features)
5. [Running Tests](#running-tests)
6. [File Reference](#file-reference)

---

## Getting Started

### Requirements

- Python 3.10+
- Packages listed in `requirements.txt` (Streamlit, pytest)

### Installation

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running the App

```bash
streamlit run app.py
```

---

## Architecture

PawPal+ is built around six classes in `pawpal_system.py`:

| Class | Role |
|---|---|
| `Priority` | Enum with three levels: `HIGH`, `MEDIUM`, `LOW` |
| `Task` | A single pet-care task with title, duration, priority, frequency, and completion state |
| `ScheduledTask` | A `Task` placed at a specific minute offset within a day |
| `ExcludedTask` | A `Task` that could not be scheduled, with a human-readable reason |
| `DailyPlan` | The full result of one scheduling run — lists of scheduled and excluded tasks, plus utilization metrics |
| `Pet` | A pet with its own task list and completion tracking |
| `Owner` | An owner with an available time window (start/end minutes from midnight) and a list of pets |
| `Scheduler` | Stateless engine that builds a `DailyPlan` from an `Owner` and optional target `Pet` |

---

## Core Algorithms

### 1. Task Sorting — Three-Key Comparator

Before scheduling, `Scheduler._sort_tasks()` sorts the candidate task list using a stable, deterministic three-key comparator:

1. **Priority descending** — `HIGH` (0) → `MEDIUM` (1) → `LOW` (2)
2. **Duration ascending** — among tasks of equal priority, shorter tasks go first to maximise the number of tasks that fit
3. **Title ascending** — alphabetical tiebreak ensures the output is identical across runs with the same input

```
sort key = (priority_rank, duration_min, title)
```

### 2. Due-Date Filtering

`Scheduler._is_due()` gates each task before it enters the scheduler:

| Frequency | Rule |
|---|---|
| `daily` | Always due |
| `as needed` | Always due |
| `weekly` | Due only on **Mondays** (`weekday() == 0`) |

Tasks not due on the requested date are immediately moved to the excluded list with a reason explaining their frequency.

### 3. Two-Pass Greedy Scheduler

`Scheduler.build_plan()` fills the owner's time window in two passes using a single running cursor (`current_min`):

**Pass 1 — Priority sweep:**
Tasks are processed in sorted order. If a task fits in the remaining window (`task.duration_min <= end_min - current_min`), it is placed at `current_min` and the cursor advances by `task.duration_min`. Tasks that do not fit are deferred to an overflow list.

**Pass 2 — Gap fill:**
After the high-priority tasks are placed, the scheduler revisits the overflow list and fills any remaining capacity with deferred tasks. This ensures that a large high-priority task does not wastefully block shorter low-priority tasks that would otherwise fit in the gap behind it.

Tasks that still cannot fit after both passes are moved to the excluded list with a message stating how many minutes were needed versus how many remained.

### 4. Conflict Detection

Two independent conflict detectors are provided:

- **`DailyPlan.detect_conflicts()`** — O(n²) sweep over all scheduled tasks within a single plan. Two tasks conflict when `a.start < b.end AND b.start < a.end` (strict overlap; back-to-back tasks with equal end/start times are not flagged).
- **`Scheduler.detect_conflicts(*plans)`** — accepts one or more `DailyPlan` objects and checks all pairs across the combined set. This is used to surface conflicts when separate plans are built for each pet and those plans are then compared (both pets start their independent schedules at `available_start_min`, so their first tasks will overlap).

The greedy scheduler itself never produces conflicts because it places tasks sequentially; the detectors serve as a safety net for manually constructed plans and for cross-pet comparisons.

### 5. Task Recurrence

`Pet.complete_task()` marks the task complete and immediately calls `task.next_occurrence()`. For `daily` and `weekly` frequencies a new, independent, pending `Task` with identical attributes is appended to the pet's task list. For `as needed` tasks `next_occurrence()` returns `None` and no new task is created. This means `get_pending_tasks()` always reflects the current queue without any external bookkeeping.

---

## Features

### Owner & Pet Configuration

- Enter an owner name and define an availability window with start and end time pickers (validated — the start time must precede the end time).
- Enter a pet name, species, and age. Multi-pet households can be modelled by scheduling each pet independently.

### Task Management

- **Add tasks** with a title, duration (minutes), priority level, and frequency (`daily`, `weekly`, `as needed`).
- **Duplicate prevention** — adding a task whose title already exists on the same pet raises an error; the UI surfaces this as a warning.
- **Priority filter** — a multiselect widget filters the task table by priority level without modifying the underlying task list.
- **Task table** — displayed in scheduling order (priority → duration → title) with colour-coded priority icons.
- **Persistent storage** — the task list is serialised to `pawpal_tasks.json` on every add or clear, and is reloaded on next launch.
- **Clear all tasks** — resets the task list and invalidates any cached plan.

### Schedule Generation

- Pick a target date from a date picker.
- Click **Generate schedule** to run the two-pass greedy scheduler against the current owner window and task list.
- The plan is cached in session state; editing tasks invalidates the cache.

### Schedule Display

- **Metrics bar** — shows total available minutes, minutes used, and utilisation percentage.
- **Utilisation status** — green (≤ 75 %), yellow (≤ 95 %), red (> 95 %) status banners guide the owner at a glance.
- **Conflict alert** — any time-window overlaps in the generated plan are displayed as warnings with the conflicting task names and time ranges.
- **Scheduled task list** — tasks displayed chronologically (sorted by start time) with start/end times, priority icon, frequency badge (shown when not `daily`), and a plain-English scheduling reason.
- **Excluded task list** — tasks that could not be scheduled are listed with the specific reason (not due today, or how many minutes were needed vs. remaining).
- **Full plan summary** — a collapsible expander shows the complete text summary produced by `DailyPlan.summary()`.

---

## Running Tests

```bash
pytest tests/test_pawpal.py -v
```

The test suite covers:

- Task validation (`is_valid`, priority type enforcement)
- Task completion and recurrence for all three frequency types
- Pet task management (add, remove, duplicate prevention, pending filter)
- Owner time-window validation (inverted and equal windows both raise)
- Scheduler sort correctness (priority order, duration tiebreak, alphabetical tiebreak, determinism)
- Due-date filtering (`daily`, `weekly` on Monday vs. non-Monday, `as needed`)
- Greedy scheduling (fits, excludes, exact fit, two-pass overflow rescue, cross-pet isolation)
- `DailyPlan` helpers (utilisation, `scheduled_by_time`, chronological ordering)
- Conflict detection (no overlap, partial overlap, back-to-back, same start, multiple overlaps, greedy plan always conflict-free, cross-plan detection)
- `Scheduler.filter_tasks` (by priority, by completion, combined, empty list, no filters)

---

## File Reference

| File | Purpose |
|---|---|
| `app.py` | Streamlit UI — owner/pet/task inputs, schedule display |
| `pawpal_system.py` | All domain classes and scheduling logic |
| `tests/test_pawpal.py` | pytest test suite |
| `pawpal_tasks.json` | Persisted task list (auto-created at runtime) |
| `uml_design.mmd` | Mermaid UML class diagram |
| `requirements.txt` | Python dependencies |
