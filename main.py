from pawpal_system import Owner, Pet, Task, Plan


def build_sample_data() -> tuple[Owner, list[Pet]]:
	owner = Owner(
		owner_id="owner-001",
		name="James",
		daily_available_minutes=60,
		preferences={"preferred_frequency": "daily"},
	)

	dog = Pet(pet_id="pet-001", name="Milo", species="Dog", age_years=4)
	cat = Pet(pet_id="pet-002", name="Luna", species="Cat", age_years=2)

	owner.add_pet(dog)
	owner.add_pet(cat)

	# At least three tasks with different time lengths.
	dog.add_task(Task(task_id="task-001", description="Morning walk", time_minutes=25, frequency="daily", priority="high"))
	dog.add_task(Task(task_id="task-002", description="Feed breakfast", time_minutes=10, frequency="daily", priority="critical"))
	cat.add_task(Task(task_id="task-003", description="Litter cleaning", time_minutes=15, frequency="daily", priority="high"))
	cat.add_task(Task(task_id="task-004", description="Play session", time_minutes=20, frequency="daily", priority="medium"))

	return owner, [dog, cat]


def print_todays_schedule(owner: Owner, pets: list[Pet]) -> None:
	print("Today's Schedule")
	print("=" * 50)

	for pet in pets:
		plan = Plan(plan_id=f"plan-{pet.pet_id}", plan_date="today", total_minutes=0)
		schedule = plan.generate_daily_schedule(owner, pet)

		print(f"\nPet: {pet.name} ({pet.species})")
		if not schedule:
			print("  No tasks scheduled.")
			continue

		for item in schedule:
			print(
				f"  {item['order']}. {item['description']} "
				f"({item['time_minutes']} min)"
			)
		print(f"  Total for {pet.name}: {plan.total_minutes} min")


if __name__ == "__main__":
	owner_data, pet_list = build_sample_data()
	print_todays_schedule(owner_data, pet_list)


