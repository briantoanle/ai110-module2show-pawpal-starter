# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
  - I created a UML diagram that includes the following classes: Priority, Task, ScheduledTask, ExcludedTask, DailyPlan, Pet, Owner, and Scheduler.
- What classes did you include, and what responsibilities did you assign to each?
  - Priority: An enumeration of task priority levels.
  - Task: A pet-care task with a title, duration, and priority.
  - ScheduledTask: A Task that has been placed at a specific start time in the day.
  - ExcludedTask: A Task that could not be scheduled, along with the reason why.
  - DailyPlan: The full schedule for a single day, including scheduled and excluded tasks.
  - Pet: Represents a pet owned by an Owner.
  - Owner: Represents the pet owner with their available time window and list of pets.
  - Scheduler: Builds a DailyPlan by scheduling tasks within an owner's available window.

**b. Design changes**

- Did your design change during implementation?
  - Yes, the design did evolve during implementation.
- If yes, describe at least one change and why you made it.
  - In the initial UML design, `DailyPlan` did not store `owner_name` or `pet_name`. During implementation, I added these fields so that each plan retains context about who it was built for. This made the `summary()` output much more informative and allowed the UI to display plan details without needing to pass extra parameters around.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
  - The scheduler considers three main constraints: the owner's available time window (start and end minutes from midnight), task priority , and task frequency (daily, weekly, as needed). Tasks are only placed in the schedule if they fit within the remaining available time and are due on the given date.
- How did you decide which constraints mattered most?
  - Time availability is the hard constraint, if a task does not fit, it simply cannot be scheduled. Priority determines ordering, since higher-priority tasks are placed first to ensure they are least likely to be excluded. Frequency is a filter applied before scheduling, so tasks that are not due on a given day are excluded early rather than competing for time slots unnecessarily.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
  - The scheduler uses a greedy, priority-first approach: it sorts all tasks by priority descending and then packs them sequentially into the time window. Tasks that do not fit on the first pass are collected into an overflow list and retried at the end.
- Why is that tradeoff reasonable for this scenario?
  - For a daily pet-care context, ensuring that high-priority tasks (e.g., feeding, medication) are always scheduled before lower-priority ones (e.g., play time) is more important than finding a globally optimal packing. The greedy approach is simple, predictable, and fast, which suits an application where the owner manually reviews and adjusts the plan.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
  - It did everything, I just followed the guidelines provided on course page.
- What kinds of prompts or questions were most helpful?
  - I used the prompt "Generate a UML diagram for a pet care planning system" to generate the initial UML diagram.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
  - I found a bug when I would change the pet name but it would modify the previous pet name as well.
- How did you evaluate or verify what the AI suggested?
  - I would run the app and check if the pet name was updated correctly.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
  - Adding pets, changing pet name, adding tasks, changing task priority, generating schedule, detecting conflicts.
- Why were these tests important?
  - It would ensure that the functions work as expected. The edge cases are the best because if one person doesn't find the bug, another person will.

**b. Confidence**

- How confident are you that your scheduler works correctly?
  - I am reasonably confident that the core scheduling logic works correctly for typical use cases. The greedy algorithm is straightforward, and the `detect_conflicts` method provides a useful safety net to catch any overlapping tasks that might be introduced through manual plan modifications.
- What edge cases would you test next if you had more time?
  - I would test scenarios where the owner's available window is exactly equal to the total duration of all tasks, to verify that the boundary condition is handled correctly. I would also test scheduling with an owner who has no pets, a pet with no tasks, and a mix of weekly tasks on both weekday and weekend dates to confirm frequency-based filtering behaves as expected.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
  - I am most satisfied with how cleanly the class responsibilities ended up being separated. Each class has a single, well-defined purpose — `Task` knows nothing about scheduling, `DailyPlan` knows nothing about the owner's constraints, and `Scheduler` acts purely as an orchestrator. This separation made debugging and testing significantly easier.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
  - I would redesign the scheduling algorithm to support multi-day planning. Currently, overflow tasks that cannot fit into a single day are simply excluded with a reason message. A more robust system would automatically carry them forward to the next available day and notify the owner rather than silently dropping them from the plan.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
  - The most important thing I learned is that AI tools are most effective when you treat their output as a first draft rather than a final answer.
