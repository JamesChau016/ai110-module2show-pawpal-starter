from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _hhmm_to_minutes(value: str) -> int:
	"""Convert HH:MM into minutes after midnight."""
	hour_str, minute_str = value.split(":")
	hour = int(hour_str)
	minute = int(minute_str)
	if not (0 <= hour <= 23 and 0 <= minute <= 59):
		raise ValueError("Time must be in 24h HH:MM format")
	return hour * 60 + minute


@dataclass
class Owner:
	owner_id: str
	name: str
	daily_available_minutes: int
	preferences: dict[str, str] = field(default_factory=dict)
	pets: list[Pet] = field(default_factory=list)

	def add_pet(self, pet: Pet) -> None:
		"""Attach a pet to this owner and set its owner reference."""
		if any(existing.pet_id == pet.pet_id for existing in self.pets):
			raise ValueError(f"Pet with id {pet.pet_id} already exists")
		pet.owner = self
		self.pets.append(pet)

	def set_daily_available_minutes(self, minutes: int) -> None:
		"""Update the owner's daily available time in minutes."""
		if minutes < 0:
			raise ValueError("daily_available_minutes cannot be negative")
		self.daily_available_minutes = minutes

	def set_preference(self, key: str, value: str) -> None:
		"""Set or overwrite a named owner preference."""
		if not key:
			raise ValueError("Preference key cannot be empty")
		self.preferences[key] = value

	def get_constraints(self) -> dict[str, Any]:
		"""Return owner constraints used for scheduling decisions."""
		return {
			"daily_available_minutes": self.daily_available_minutes,
			"preferences": dict(self.preferences),
			"pet_count": len(self.pets),
		}

	def get_all_tasks(self) -> list[Task]:
		"""Collect and return tasks across all pets owned by this owner."""
		all_tasks: list[Task] = []
		for pet in self.pets:
			all_tasks.extend(pet.tasks)
		return all_tasks


@dataclass
class Pet:
	pet_id: str
	name: str
	species: str
	age_years: int
	owner: Owner | None = None
	special_needs: list[str] = field(default_factory=list)
	tasks: list[Task] = field(default_factory=list)

	def add_task(self, task: Task) -> None:
		"""Add a task to this pet, enforcing unique task IDs."""
		if any(existing.task_id == task.task_id for existing in self.tasks):
			raise ValueError(f"Task with id {task.task_id} already exists for pet {self.pet_id}")
		self.tasks.append(task)

	def edit_task(self, task_id: str, duration_minutes: int, priority: str) -> None:
		"""Update duration and priority for an existing task by ID."""
		for task in self.tasks:
			if task.task_id == task_id:
				task.set_duration(duration_minutes)
				task.set_priority(priority)
				return
		raise KeyError(f"Task {task_id} not found")

	def remove_task(self, task_id: str) -> None:
		"""Remove a task from this pet by task ID."""
		for index, task in enumerate(self.tasks):
			if task.task_id == task_id:
				del self.tasks[index]
				return
		raise KeyError(f"Task {task_id} not found")

	def get_tasks(self) -> list[Task]:
		"""Return a shallow copy of this pet's task list."""
		return list(self.tasks)


@dataclass
class Task:
	task_id: str
	description: str
	time_minutes: int
	frequency: str
	completed: bool = False
	priority: str = "medium"
	preferred_start: str = ""
	preferred_end: str = ""

	def set_duration(self, minutes: int) -> None:
		"""Set the task duration in minutes, validating it is positive."""
		if minutes <= 0:
			raise ValueError("Task duration must be greater than 0")
		self.time_minutes = minutes

	def set_priority(self, priority: str) -> None:
		"""Set normalized task priority from the allowed priority levels."""
		normalized = priority.lower()
		allowed = {"low", "medium", "high", "critical"}
		if normalized not in allowed:
			raise ValueError(f"Priority must be one of: {sorted(allowed)}")
		self.priority = normalized

	def set_time_window(self, start: str, end: str) -> None:
		"""Set a preferred time window, requiring start to precede end."""
		if _hhmm_to_minutes(start) >= _hhmm_to_minutes(end):
			raise ValueError("Start time must be earlier than end time")
		self.preferred_start = start
		self.preferred_end = end

	def mark_complete(self) -> None:
		"""Mark this task as completed."""
		self.completed = True

	def is_valid(self) -> bool:
		"""Return whether the task has valid content and scheduling fields."""
		if not self.description.strip():
			return False
		if self.time_minutes <= 0:
			return False
		if self.frequency.lower() not in {"daily", "weekly", "monthly", "once"}:
			return False
		if self.preferred_start and self.preferred_end:
			return _hhmm_to_minutes(self.preferred_start) < _hhmm_to_minutes(self.preferred_end)
		return True


@dataclass
class Plan:
	plan_id: str
	plan_date: str
	total_minutes: int
	tasks: list[Task] = field(default_factory=list)
	scheduled_items: list[dict[str, Any]] = field(default_factory=list)
	selected_reasons: dict[str, str] = field(default_factory=dict)
	skipped_reasons: dict[str, str] = field(default_factory=dict)

	def rank_tasks(self, tasks: list[Task], preferences: dict[str, str]) -> list[Task]:
		"""Sort tasks by priority, frequency preference, and completion status."""
		priority_score = {"critical": 4, "high": 3, "medium": 2, "low": 1}
		preferred_frequency = preferences.get("preferred_frequency", "").lower()

		def score(task: Task) -> tuple[int, int, int]:
			priority_points = priority_score.get(task.priority.lower(), 0)
			frequency_bonus = 1 if preferred_frequency and task.frequency.lower() == preferred_frequency else 0
			completion_penalty = 0 if not task.completed else -5
			return (priority_points, frequency_bonus, completion_penalty)

		return sorted(tasks, key=score, reverse=True)

	def select_tasks(self, tasks: list[Task], available_minutes: int) -> list[Task]:
		"""Choose tasks that fit within the available time budget."""
		selected: list[Task] = []
		used_minutes = 0
		for task in tasks:
			if task.completed:
				continue
			if used_minutes + task.time_minutes <= available_minutes:
				selected.append(task)
				used_minutes += task.time_minutes
		return selected

	def generate_daily_schedule(self, owner: Owner, pet: Pet) -> list[dict[str, Any]]:
		"""Build a daily schedule for one pet based on ranking and time limits."""
		ranked_tasks = self.rank_tasks(pet.get_tasks(), owner.preferences)
		selected_tasks = self.select_tasks(ranked_tasks, owner.daily_available_minutes)

		self.tasks = selected_tasks
		self.total_minutes = sum(task.time_minutes for task in selected_tasks)
		self.scheduled_items = []
		self.selected_reasons = {}
		self.skipped_reasons = {}

		for order, task in enumerate(selected_tasks, start=1):
			self.scheduled_items.append(
				{
					"order": order,
					"pet_id": pet.pet_id,
					"task_id": task.task_id,
					"description": task.description,
					"time_minutes": task.time_minutes,
				}
			)
			self.selected_reasons[task.task_id] = "Fits time budget and ranked by priority"

		selected_ids = {task.task_id for task in selected_tasks}
		for task in ranked_tasks:
			if task.task_id not in selected_ids:
				if task.completed:
					self.skipped_reasons[task.task_id] = "Already completed"
				else:
					self.skipped_reasons[task.task_id] = "Insufficient remaining time"

		return list(self.scheduled_items)

	def explain_choices(self) -> str:
		"""Summarize selected and skipped task counts for this plan."""
		selected_count = len(self.selected_reasons)
		skipped_count = len(self.skipped_reasons)
		lines = [
			f"Plan {self.plan_id} for {self.plan_date}",
			f"Total planned minutes: {self.total_minutes}",
			f"Selected tasks: {selected_count}",
			f"Skipped tasks: {skipped_count}",
		]
		return "\n".join(lines)

	def get_schedule(self) -> list[dict[str, Any]]:
		"""Return a copy of the generated scheduled items."""
		return list(self.scheduled_items)
