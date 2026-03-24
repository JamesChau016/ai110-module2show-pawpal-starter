# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

New features include:

- Time Sorting
  - Tasks can be ordered by duration using owner preference `time_sort`.
  - Supported values:
    - `shortest_first` (default)
    - `longest_first` (also supports `desc` and `descending`)

- Task filtering utilities
  - Filter by completion status (`completed=True` or `False`)
  - Filter by pet name (case-insensitive)
  - Useful for focused views such as "show only unfinished tasks for Luna"

- Recurring task rollover on completion
  - When a `daily` task is marked complete, a new task instance is automatically created for the next day.
  - When a `weekly` task is marked complete, a new task instance is automatically created for the next week.
  - New due dates are calculated with `timedelta` for accurate date math.

- Lightweight conflict detection
  - Scheduling no longer crashes on overlapping time windows.
  - The system records conflict warnings when two scheduled tasks overlap:
    - for the same pet
    - or across different pets
  - Warnings are available through `get_conflict_warnings()` and can be shown in CLI/UI.

- Readability-focused scheduling refactor
  - Daily schedule generation was split into smaller helper steps.
  - This improves readability and maintainability while preserving scheduling behavior.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
