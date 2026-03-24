from pawpal_system import Pet, Task


def test_mark_complete_changes_task_status() -> None:
	task = Task(task_id="t1", description="Walk", time_minutes=20, frequency="daily")

	assert task.completed is False
	task.mark_complete()
	assert task.completed is True


def test_adding_task_increases_pet_task_count() -> None:
	pet = Pet(pet_id="p1", name="Milo", species="dog", age_years=3)
	task = Task(task_id="t2", description="Feed", time_minutes=10, frequency="daily")

	initial_count = len(pet.tasks)
	pet.add_task(task)

	assert len(pet.tasks) == initial_count + 1
