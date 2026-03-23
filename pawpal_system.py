from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Owner:
	owner_id: str
	name: str
	daily_available_minutes: int
	preferences: dict[str, str] = field(default_factory=dict)
	pets: list[Pet] = field(default_factory=list)

	def add_pet(self, pet: Pet) -> None:
		pass

	def set_daily_available_minutes(self, minutes: int) -> None:
		pass

	def set_preference(self, key: str, value: str) -> None:
		pass

	def get_constraints(self) -> dict[str, Any]:
		pass


@dataclass
class Pet:
	pet_id: str
	name: str
	species: str
	age_years: int
	special_needs: list[str] = field(default_factory=list)
	tasks: list[Tasks] = field(default_factory=list)

	def add_task(self, task: Tasks) -> None:
		pass

	def edit_task(self, task_id: str, duration_minutes: int, priority: str) -> None:
		pass

	def remove_task(self, task_id: str) -> None:
		pass

	def get_tasks(self) -> list[Tasks]:
		pass


@dataclass
class Tasks:
	task_id: str
	title: str
	category: str
	duration_minutes: int
	priority: str
	preferred_start: str
	preferred_end: str
	mandatory: bool

	def set_duration(self, minutes: int) -> None:
		pass

	def set_priority(self, priority: str) -> None:
		pass

	def set_time_window(self, start: str, end: str) -> None:
		pass

	def is_valid(self) -> bool:
		pass


@dataclass
class Plan:
	plan_id: str
	plan_date: str
	total_minutes: int
	scheduled_items: list[dict[str, Any]] = field(default_factory=list)
	selected_reasons: dict[str, str] = field(default_factory=dict)
	skipped_reasons: dict[str, str] = field(default_factory=dict)

	def rank_tasks(self, tasks: list[Tasks], preferences: dict[str, str]) -> list[Tasks]:
		pass

	def select_tasks(self, tasks: list[Tasks], available_minutes: int) -> list[Tasks]:
		pass

	def generate_daily_schedule(self, owner: Owner, pet: Pet) -> list[dict[str, Any]]:
		pass

	def explain_choices(self) -> str:
		pass

	def get_schedule(self) -> list[dict[str, Any]]:
		pass
