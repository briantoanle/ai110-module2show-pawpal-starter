from pawpal_system import Task, Pet, Priority


def test_mark_complete_changes_status():
    """Task completion: mark_complete() should set completed to True."""
    task = Task("Morning Walk", duration_min=30, priority=Priority.HIGH)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Task addition: adding a task to a Pet should increase its task count by 1."""
    pet = Pet(name="Buddy", species="Dog", age_years=3)
    assert len(pet.tasks) == 0
    pet.add_task(Task("Feed Breakfast", duration_min=10, priority=Priority.MEDIUM))
    assert len(pet.tasks) == 1
