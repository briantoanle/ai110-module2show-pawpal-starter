from pawpal_system import Owner, Pet, Task, Priority, Scheduler

# Create owner (available 7:00 AM to 9:00 AM = 420 to 540 min)
owner = Owner(name="Alex", available_start_min=7 * 60, available_end_min=9 * 60)

# Create two pets
buddy = Pet(name="Buddy", species="Dog", age_years=3)
whiskers = Pet(name="Whiskers", species="Cat", age_years=5)

# Add tasks to Buddy (dog)
buddy.add_task(Task("Morning Walk",       duration_min=30, priority=Priority.HIGH,   frequency="daily"))
buddy.add_task(Task("Feed Breakfast",     duration_min=10, priority=Priority.HIGH,   frequency="daily"))
buddy.add_task(Task("Brush Fur",          duration_min=15, priority=Priority.MEDIUM, frequency="weekly"))

# Add tasks to Whiskers (cat)
whiskers.add_task(Task("Clean Litter Box", duration_min=10, priority=Priority.HIGH,   frequency="daily"))
whiskers.add_task(Task("Feed Breakfast",   duration_min=5,  priority=Priority.HIGH,   frequency="daily"))
whiskers.add_task(Task("Playtime",         duration_min=20, priority=Priority.LOW,    frequency="daily"))

# Register pets with owner
owner.add_pet(buddy)
owner.add_pet(whiskers)

# Build schedules
scheduler = Scheduler()
today = "2026-03-29"
plan_buddy    = scheduler.build_plan(owner, date=today, pet=buddy)
plan_whiskers = scheduler.build_plan(owner, date=today, pet=whiskers)

# Print Today's Schedule
print("=" * 50)
print("         PAWPAL+ — TODAY'S SCHEDULE")
print("=" * 50)
print(plan_buddy.summary())
print()
print("-" * 50)
print()
print(plan_whiskers.summary())
print("=" * 50)
