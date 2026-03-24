from datetime import date, timedelta

from pawpal_system import Owner, Pet, Plan, Task


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


def test_generate_daily_schedule_sorts_by_shortest_time_by_default() -> None:
	owner = Owner(owner_id="o1", name="Alex", daily_available_minutes=60)
	pet = Pet(pet_id="p1", name="Milo", species="dog", age_years=3)
	owner.add_pet(pet)

	pet.add_task(Task(task_id="t1", description="Long task", time_minutes=40, frequency="daily", priority="high"))
	pet.add_task(Task(task_id="t2", description="Short task", time_minutes=10, frequency="daily", priority="low"))
	pet.add_task(Task(task_id="t3", description="Medium task", time_minutes=20, frequency="daily", priority="medium"))

	plan = Plan(plan_id="plan-1", plan_date="2026-03-23", total_minutes=0)
	schedule = plan.generate_daily_schedule(owner, pet)

	assert [item["task_id"] for item in schedule] == ["t2", "t3"]


def test_generate_daily_schedule_supports_longest_first_time_sort() -> None:
	owner = Owner(
		owner_id="o1",
		name="Alex",
		daily_available_minutes=100,
		preferences={"time_sort": "longest_first"},
	)
	pet = Pet(pet_id="p1", name="Milo", species="dog", age_years=3)
	owner.add_pet(pet)

	pet.add_task(Task(task_id="t1", description="Long task", time_minutes=40, frequency="daily", priority="high"))
	pet.add_task(Task(task_id="t2", description="Short task", time_minutes=10, frequency="daily", priority="low"))
	pet.add_task(Task(task_id="t3", description="Medium task", time_minutes=20, frequency="daily", priority="medium"))

	plan = Plan(plan_id="plan-1", plan_date="2026-03-23", total_minutes=0)
	schedule = plan.generate_daily_schedule(owner, pet)

	assert [item["task_id"] for item in schedule] == ["t1", "t3", "t2"]


def test_filter_tasks_by_completion_status() -> None:
	owner = Owner(owner_id="o1", name="Alex", daily_available_minutes=60)
	pet = Pet(pet_id="p1", name="Milo", species="dog", age_years=3)
	owner.add_pet(pet)

	completed_task = Task(task_id="t1", description="Walk", time_minutes=20, frequency="daily")
	completed_task.mark_complete()
	incomplete_task = Task(task_id="t2", description="Feed", time_minutes=10, frequency="daily")
	pet.add_task(completed_task)
	pet.add_task(incomplete_task)

	plan = Plan(plan_id="plan-1", plan_date="2026-03-23", total_minutes=0)
	completed_only = plan.filter_tasks(owner, completed=True)

	assert [item["task_id"] for item in completed_only] == ["t1"]
	assert completed_only[0]["completed"] is True


def test_filter_tasks_by_pet_name() -> None:
	owner = Owner(owner_id="o1", name="Alex", daily_available_minutes=60)
	dog = Pet(pet_id="p1", name="Milo", species="dog", age_years=3)
	cat = Pet(pet_id="p2", name="Luna", species="cat", age_years=2)
	owner.add_pet(dog)
	owner.add_pet(cat)

	dog.add_task(Task(task_id="t1", description="Walk", time_minutes=20, frequency="daily"))
	cat.add_task(Task(task_id="t2", description="Litter", time_minutes=15, frequency="daily"))

	plan = Plan(plan_id="plan-1", plan_date="2026-03-23", total_minutes=0)
	luna_tasks = plan.filter_tasks(owner, pet_name="luna")

	assert [item["task_id"] for item in luna_tasks] == ["t2"]
	assert all(item["pet_name"] == "Luna" for item in luna_tasks)


def test_mark_complete_daily_creates_next_occurrence() -> None:
	task = Task(task_id="t1", description="Walk", time_minutes=20, frequency="daily")

	next_task = task.mark_complete()

	assert task.completed is True
	assert next_task is not None
	assert next_task.frequency == "daily"
	assert next_task.completed is False
	assert next_task.due_date == date.today() + timedelta(days=1)


def test_plan_complete_task_weekly_adds_next_occurrence() -> None:
	owner = Owner(owner_id="o1", name="Alex", daily_available_minutes=60)
	pet = Pet(pet_id="p1", name="Milo", species="dog", age_years=3)
	owner.add_pet(pet)
	pet.add_task(Task(task_id="t1", description="Training", time_minutes=30, frequency="weekly"))

	plan = Plan(plan_id="plan-1", plan_date="2026-03-23", total_minutes=0)
	next_task = plan.complete_task(pet, "t1")

	assert next_task is not None
	assert next_task.due_date == date.today() + timedelta(weeks=1)
	assert len(pet.tasks) == 2
	assert pet.tasks[0].completed is True
	assert pet.tasks[1].task_id == next_task.task_id


def test_detect_conflicts_warns_for_same_pet_overlap() -> None:
	plan = Plan(plan_id="plan-1", plan_date="2026-03-23", total_minutes=0)
	items = [
		{
			"pet_id": "p1",
			"task_id": "t1",
			"preferred_start": "09:00",
			"preferred_end": "09:30",
		},
		{
			"pet_id": "p1",
			"task_id": "t2",
			"preferred_start": "09:15",
			"preferred_end": "09:45",
		},
	]

	warnings = plan.detect_conflicts(items)

	assert len(warnings) == 1
	assert "same pet" in warnings[0]


def test_detect_conflicts_warns_for_different_pet_overlap() -> None:
	plan = Plan(plan_id="plan-1", plan_date="2026-03-23", total_minutes=0)
	items = [
		{
			"pet_id": "p1",
			"task_id": "t1",
			"preferred_start": "10:00",
			"preferred_end": "10:30",
		},
		{
			"pet_id": "p2",
			"task_id": "t2",
			"preferred_start": "10:00",
			"preferred_end": "10:20",
		},
	]

	warnings = plan.detect_conflicts(items)

	assert len(warnings) == 1
	assert "different pets" in warnings[0]
