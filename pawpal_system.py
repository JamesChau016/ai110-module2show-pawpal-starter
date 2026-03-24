from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
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
	due_date: date | None = None

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

	def mark_complete(self) -> Task | None:
		"""Mark completed and return the next recurring task when applicable."""
		if self.completed:
			return None

		self.completed = True
		normalized_frequency = self.frequency.lower()
		if normalized_frequency == "daily":
			next_due_date = date.today() + timedelta(days=1)
		elif normalized_frequency == "weekly":
			next_due_date = date.today() + timedelta(weeks=1)
		else:
			return None

		return Task(
			task_id=f"{self.task_id}-next-{next_due_date.isoformat()}",
			description=self.description,
			time_minutes=self.time_minutes,
			frequency=self.frequency,
			priority=self.priority,
			preferred_start=self.preferred_start,
			preferred_end=self.preferred_end,
			due_date=next_due_date,
		)

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
	conflict_warnings: list[str] = field(default_factory=list)

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

	def sort_tasks_by_time(self, tasks: list[Task], descending: bool = False) -> list[Task]:
		"""Return tasks sorted by duration (shortest first by default)."""
		return sorted(tasks, key=lambda task: task.time_minutes, reverse=descending)

	def _is_descending_time_sort(self, owner: Owner) -> bool:
		"""Return whether owner's time sort preference is descending."""
		time_sort_pref = owner.preferences.get("time_sort", "shortest_first").lower()
		return time_sort_pref in {"longest_first", "desc", "descending"}

	def _build_schedule_items(self, pet: Pet, selected_tasks: list[Task]) -> list[dict[str, Any]]:
		"""Build schedule rows from selected tasks."""
		return [
			{
				"order": order,
				"pet_id": pet.pet_id,
				"task_id": task.task_id,
				"description": task.description,
				"time_minutes": task.time_minutes,
				"preferred_start": task.preferred_start,
				"preferred_end": task.preferred_end,
			}
			for order, task in enumerate(selected_tasks, start=1)
		]

	def _build_selected_reasons(self, selected_tasks: list[Task]) -> dict[str, str]:
		"""Build reason text for all selected tasks."""
		return {
			task.task_id: "Fits time budget and ranked by priority"
			for task in selected_tasks
		}

	def _build_skipped_reasons(self, ranked_tasks: list[Task], selected_tasks: list[Task]) -> dict[str, str]:
		"""Build reason text for ranked tasks that were not selected."""
		selected_ids = {task.task_id for task in selected_tasks}
		return {
			task.task_id: "Already completed" if task.completed else "Insufficient remaining time"
			for task in ranked_tasks
			if task.task_id not in selected_ids
		}

	def generate_daily_schedule(self, owner: Owner, pet: Pet) -> list[dict[str, Any]]:
		"""Build a daily schedule for one pet based on ranking and time limits."""
		ranked_tasks = self.rank_tasks(pet.get_tasks(), owner.preferences)
		descending = self._is_descending_time_sort(owner)
		time_sorted_tasks = self.sort_tasks_by_time(ranked_tasks, descending=descending)
		selected_tasks = self.select_tasks(time_sorted_tasks, owner.daily_available_minutes)

		self.tasks = selected_tasks
		self.total_minutes = sum(task.time_minutes for task in selected_tasks)
		self.scheduled_items = self._build_schedule_items(pet, selected_tasks)
		self.selected_reasons = self._build_selected_reasons(selected_tasks)
		self.skipped_reasons = self._build_skipped_reasons(ranked_tasks, selected_tasks)
		self.conflict_warnings = []

		self.conflict_warnings = self.detect_conflicts()

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

	def detect_conflicts(self, scheduled_items: list[dict[str, Any]] | None = None) -> list[str]:
		"""Return warnings for overlapping task windows instead of raising errors."""
		items = scheduled_items if scheduled_items is not None else self.scheduled_items
		timed_items: list[tuple[int, int, dict[str, Any]]] = []

		for item in items:
			start = item.get("preferred_start", "")
			end = item.get("preferred_end", "")
			if not start or not end:
				continue
			try:
				start_minutes = _hhmm_to_minutes(start)
				end_minutes = _hhmm_to_minutes(end)
			except ValueError:
				continue
			if start_minutes >= end_minutes:
				continue
			timed_items.append((start_minutes, end_minutes, item))

		warnings: list[str] = []
		for index, (left_start, left_end, left_item) in enumerate(timed_items):
			for right_start, right_end, right_item in timed_items[index + 1 :]:
				overlaps = max(left_start, right_start) < min(left_end, right_end)
				if not overlaps:
					continue
				pet_relation = "same pet" if left_item.get("pet_id") == right_item.get("pet_id") else "different pets"
				warnings.append(
					f"Conflict: task {left_item.get('task_id')} ({left_item.get('pet_id')}) overlaps with "
					f"task {right_item.get('task_id')} ({right_item.get('pet_id')}) [{pet_relation}]"
				)

		return warnings

	def get_conflict_warnings(self) -> list[str]:
		"""Return recorded scheduling conflict warnings."""
		return list(self.conflict_warnings)

	def complete_task(self, pet: Pet, task_id: str) -> Task | None:
		"""Complete one task and append the next occurrence for recurring tasks."""
		for task in pet.tasks:
			if task.task_id == task_id:
				next_task = task.mark_complete()
				if next_task is not None:
					pet.add_task(next_task)
				return next_task
		raise KeyError(f"Task {task_id} not found")

	def filter_tasks(
		self,
		owner: Owner,
		completed: bool | None = None,
		pet_name: str | None = None,
	) -> list[dict[str, Any]]:
		"""Return owner tasks filtered by completion status and/or pet name."""
		normalized_pet_name = pet_name.strip().lower() if pet_name else None
		filtered: list[dict[str, Any]] = []

		for pet in owner.pets:
			if normalized_pet_name and pet.name.lower() != normalized_pet_name:
				continue

			for task in pet.tasks:
				if completed is not None and task.completed is not completed:
					continue

				filtered.append(
					{
						"pet_id": pet.pet_id,
						"pet_name": pet.name,
						"task_id": task.task_id,
						"description": task.description,
						"time_minutes": task.time_minutes,
						"frequency": task.frequency,
						"priority": task.priority,
						"completed": task.completed,
					}
				)

		return filtered
