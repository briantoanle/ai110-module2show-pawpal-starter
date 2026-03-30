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
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
    - 
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
