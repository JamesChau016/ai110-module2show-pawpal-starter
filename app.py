import streamlit as st
from datetime import date, datetime, time, timedelta
from pawpal_system import Owner, Pet, Task, Plan

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown("Welcome to the PawPal+ scheduler demo.")
st.caption("Create tasks with date + start time + duration, then generate a conflict-aware schedule.")


def get_priority_indicator(priority: str) -> str:
    color_by_priority = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }
    normalized = (priority or "").lower()
    return color_by_priority.get(normalized, "⚪")

st.divider()

st.subheader("Owner + Pet Setup")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
age_years = st.number_input("Pet age (years)", min_value=0, max_value=40, value=2)
daily_minutes = st.number_input("Daily available minutes", min_value=0, max_value=600, value=60)
col_energy_1, col_energy_2, col_energy_3 = st.columns(3)
with col_energy_1:
    preferred_energy_bank_morning = st.number_input(
        "Morning energy bank",
        min_value=0,
        max_value=100,
        value=5,
    )
with col_energy_2:
    preferred_energy_bank_afternoon = st.number_input(
        "Afternoon energy bank",
        min_value=0,
        max_value=100,
        value=5,
    )
with col_energy_3:
    preferred_energy_bank_evening = st.number_input(
        "Evening energy bank",
        min_value=0,
        max_value=100,
        value=5,
    )

# Load from JSON if not already in session state
if "owner" not in st.session_state:
    loaded_owner = Owner.load_from_json("data.json")
    if loaded_owner:
        st.session_state.owner = loaded_owner
        st.session_state.pet = loaded_owner.pets[0] if loaded_owner.pets else None
        st.success("Data loaded from data.json")
    else:
        st.session_state.owner = Owner(
            owner_id="owner-1",
            name=owner_name,
            daily_available_minutes=int(daily_minutes),
        )
        st.session_state.pet = None

if "pet" not in st.session_state or st.session_state.pet is None:
    st.session_state.pet = Pet(
        pet_id="pet-1",
        name=pet_name,
        species=species,
        age_years=int(age_years),
    )
    if st.session_state.pet not in st.session_state.owner.pets:
        st.session_state.owner.add_pet(st.session_state.pet)

if "task_counter" not in st.session_state:
    st.session_state.task_counter = 0

if "last_plan_date" not in st.session_state:
    st.session_state.last_plan_date = date.today()

if "schedule_generated" not in st.session_state:
    st.session_state.schedule_generated = False

owner = st.session_state.owner
pet = st.session_state.pet

owner.name = owner_name
owner.set_daily_available_minutes(int(daily_minutes))
owner.set_preference("preferred_energy_bank_morning", str(int(preferred_energy_bank_morning)))
owner.set_preference("preferred_energy_bank_afternoon", str(int(preferred_energy_bank_afternoon)))
owner.set_preference("preferred_energy_bank_evening", str(int(preferred_energy_bank_evening)))
pet.name = pet_name
pet.species = species
pet.age_years = int(age_years)

# Add save button in the Owner + Pet Setup section
col_save1, col_save2 = st.columns([3, 1])
with col_save2:
    if st.button("💾 Save Data", key="save_data_button", use_container_width=True):
        owner.save_to_json("data.json")
        st.success("✓ Data saved to data.json")

st.divider()

st.subheader("Add Task")
st.caption("Create task objects and add them to your pet using pawpal_system methods.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high", "critical"], index=2)

col4, col5, col6 = st.columns(3)
with col4:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly", "once"], index=0)
with col5:
    task_due_date = st.date_input("Task date", value=date.today())
with col6:
    preferred_start = st.time_input("Start time", value=time(9, 0))

energy_cost = st.number_input("Energy cost", min_value=1, max_value=20, value=2)

if st.button("Add task"):
    try:
        st.session_state.task_counter += 1
        task_id = f"task-{st.session_state.task_counter}"
        task = Task(
            task_id=task_id,
            description=task_title,
            time_minutes=int(duration),
            frequency=frequency,
            energy_cost=int(energy_cost),
            priority=priority,
            due_date=task_due_date,
        )
        task.set_priority(priority)
        task.set_energy_cost(int(energy_cost))

        # Use start + duration as the task window so conflict detection works without manual end input.
        start_dt = datetime.combine(task_due_date, preferred_start)
        end_dt = start_dt + timedelta(minutes=int(duration))
        task.set_time_window(
            start_dt.strftime("%H:%M"),
            end_dt.strftime("%H:%M"),
        )

        pet.add_task(task)
        st.success(f"Added task: {task.description}")
    except (ValueError, KeyError) as exc:
        st.error(str(exc))

current_tasks = [
    {
        "pet": f"{pet.name} ({pet.species})",
        "task": f"{get_priority_indicator(t.priority)} {t.get_task_type_emoji()} {t.description}",
        "date": t.due_date.isoformat() if t.due_date else "",
        "start": t.preferred_start,
        "duration_min": t.time_minutes,
        "priority": t.priority,
        "energy_cost": t.energy_cost,
        "status": t.get_status_indicator(),
        "frequency": t.frequency,
        "completed": t.completed,
    }
    for t in pet.get_tasks()
]

if current_tasks:
    st.write("Current tasks:")
    st.caption("Legend: priority ● (🔴 critical, 🟠 high, 🟡 medium, 🟢 low) | status (🟢 Completed, 🟡 Pending)")
    st.dataframe(current_tasks, use_container_width=True, hide_index=True)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate a plan using your Plan methods.")

plan_date_input = st.date_input("Schedule date", value=date.today(), key="schedule_date")
st.session_state.last_plan_date = plan_date_input


def build_schedule_rows(plan: Plan, pet: Pet, plan_date_value: date) -> tuple[list[dict[str, str | int]], list[dict[str, str]]]:
    full_schedule = plan.generate_daily_schedule(owner, pet)

    same_day_schedule = []
    for item in full_schedule:
        task_obj = next((t for t in pet.get_tasks() if t.task_id == item["task_id"]), None)
        if task_obj and task_obj.due_date and task_obj.due_date > plan_date_value:
            continue
        same_day_schedule.append(item)

    plan.scheduled_items = same_day_schedule
    plan.total_minutes = sum(item["time_minutes"] for item in same_day_schedule)
    plan.conflict_warnings = plan.calculate_warnings(owner, same_day_schedule)

    schedule_items: list[dict[str, str | int]] = []
    completion_rows: list[dict[str, str]] = []

    for item in plan.get_schedule():
        start_text = item.get("preferred_start", "")
        end_text = item.get("preferred_end", "")

        scheduled_start = f"{plan_date_value.isoformat()} {start_text}" if start_text else ""
        scheduled_end = f"{plan_date_value.isoformat()} {end_text}" if end_text else ""

        task_obj = next((t for t in pet.get_tasks() if t.task_id == item["task_id"]), None)
        priority_value = task_obj.priority if task_obj else ""

        schedule_items.append(
            {
                "pet": f"{pet.name} ({pet.species})",
                "task": f"{get_priority_indicator(priority_value)} {(task_obj.get_task_type_emoji() if task_obj else '📌')} {item['description']}",
                "date": plan_date_value.isoformat(),
                "start": scheduled_start,
                "end": scheduled_end,
                "duration_min": item["time_minutes"],
                "priority": priority_value,
                "energy_cost": item.get("energy_cost", 1),
                "status": task_obj.get_status_indicator() if task_obj else "🟡 Pending",
            }
        )

        completion_rows.append(
            {
                "task_id": item["task_id"],
                "task": f"{(task_obj.get_task_type_emoji() if task_obj else '📌')} {item['description']}",
                "start": start_text,
                "duration": f"{item['time_minutes']} min",
            }
        )

    return schedule_items, completion_rows


def get_priority_sort_value(priority: str) -> int:
    order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    return order.get((priority or "").lower(), 0)


def apply_schedule_filters_and_sort(
    rows: list[dict[str, str | int]],
    task_query: str,
    selected_priorities: list[str],
    sort_by: str,
    descending: bool,
) -> list[dict[str, str | int]]:
    filtered_rows = rows

    query = task_query.strip().lower()
    if query:
        filtered_rows = [row for row in filtered_rows if query in str(row.get("task", "")).lower()]

    if selected_priorities:
        normalized = {p.lower() for p in selected_priorities}
        filtered_rows = [
            row for row in filtered_rows if str(row.get("priority", "")).lower() in normalized
        ]

    if sort_by == "priority":
        key_fn = lambda row: get_priority_sort_value(str(row.get("priority", "")))
    elif sort_by == "duration_min":
        key_fn = lambda row: int(row.get("duration_min", 0))
    else:
        key_fn = lambda row: str(row.get(sort_by, ""))

    return sorted(filtered_rows, key=key_fn, reverse=descending)


if st.button("Generate schedule"):
    st.session_state.schedule_generated = True

if st.session_state.schedule_generated:
    try:
        plan = Plan(
            plan_id=f"plan-{st.session_state.last_plan_date.isoformat()}",
            plan_date=st.session_state.last_plan_date.isoformat(),
            total_minutes=0,
        )

        schedule_items, completion_rows = build_schedule_rows(plan, pet, st.session_state.last_plan_date)

        st.success("✔️ Schedule generated successfully.")
        
        # Display key metrics
        col_metric1, col_metric2, col_metric3 = st.columns(3)
        with col_metric1:
            st.metric("Total Scheduled", len(schedule_items), help="Number of tasks included in schedule")
        with col_metric2:
            st.metric("Total Duration", f"{plan.total_minutes} min", help="Combined duration of all scheduled tasks")
        with col_metric3:
            st.metric("Skipped Tasks", len(plan.skipped_reasons), help="Number of tasks that couldn't fit")
        
        st.divider()

        # Filters and sorting section
        st.subheader("Filters & Sorting")
        col_filter_1, col_filter_2, col_filter_3, col_filter_4 = st.columns(4)
        with col_filter_1:
            schedule_task_query = st.text_input("Task contains", value="", key="schedule_task_query", placeholder="Search by name...")
        with col_filter_2:
            schedule_priority_filter = st.multiselect(
                "Priority filter",
                ["critical", "high", "medium", "low"],
                default=[],
                key="schedule_priority_filter",
            )
        with col_filter_3:
            schedule_sort_by = st.selectbox(
                "Sort by",
                ["start", "task", "priority", "duration_min", "date"],
                index=0,
                key="schedule_sort_by",
            )
        with col_filter_4:
            schedule_sort_desc = st.checkbox("Descending", value=False, key="schedule_sort_desc")

        displayed_schedule = apply_schedule_filters_and_sort(
            schedule_items,
            task_query=schedule_task_query,
            selected_priorities=schedule_priority_filter,
            sort_by=schedule_sort_by,
            descending=schedule_sort_desc,
        )

        # Display schedule
        st.subheader("📋 Schedule Items")
        if displayed_schedule:
            st.info(f"Showing {len(displayed_schedule)} of {len(schedule_items)} tasks", icon="ℹ️")
            st.caption("Task names include priority and task-type indicators for quick scanning.")
            st.dataframe(displayed_schedule, use_container_width=True, hide_index=True)
        else:
            st.warning("No tasks match the current filters.", icon="⚠️")
        
        st.divider()
        
        # Display plan summary
        with st.expander("📊 Plan Summary", expanded=True):
            st.text(plan.explain_choices())

        if completion_rows:
            st.divider()
            st.subheader("✅ Mark Tasks Complete")
            for row in completion_rows:
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.write(f"**{row['task']}** | {row['start']} | {row['duration']}")
                with col_b:
                    if st.button("Complete", key=f"complete-{row['task_id']}", use_container_width=True):
                        next_task = plan.complete_task(pet, row["task_id"])
                        if next_task is not None:
                            st.success(
                                f"✓ Completed '{row['task']}'. Next occurrence: {next_task.due_date.isoformat()}",
                                icon="✓"
                            )
                        else:
                            st.success(f"✓ Completed '{row['task']}'.", icon="✓")
                        st.rerun()

        st.divider()
        
        # Conflict warnings section
        warnings = plan.get_conflict_warnings()
        if warnings:
            st.subheader("⚠️ Scheduling Conflicts")
            st.warning(f"Found {len(warnings)} potential scheduling conflict(s):", icon="⚠️")
            for warning in warnings:
                st.error(f"• {warning}", icon="❌")
        elif schedule_items:
            st.subheader("✔️ Scheduling Status")
            st.success("No scheduling conflicts detected! Schedule is conflict-free.")

        # Skipped reasons section
        if plan.skipped_reasons:
            st.divider()
            st.subheader("⏭️ Skipped Tasks")
            col_skip_1, col_skip_2 = st.columns([3, 1])
            with col_skip_1:
                st.info(f"{len(plan.skipped_reasons)} task(s) could not be scheduled", icon="ℹ️")
            with col_skip_2:
                pass
            
            skipped_rows = []
            for task_id, reason in plan.skipped_reasons.items():
                task_obj = next((t for t in pet.get_tasks() if t.task_id == task_id), None)
                if task_obj:
                    skipped_rows.append({
                        "pet": f"{pet.name} ({pet.species})",
                        "task": f"{get_priority_indicator(task_obj.priority)} {task_obj.get_task_type_emoji()} {task_obj.description}",
                        "priority": task_obj.priority,
                        "status": "🔴 Skipped",
                        "reason": reason
                    })
                else:
                    skipped_rows.append({
                        "pet": f"{pet.name} ({pet.species})",
                        "task": f"⚪ {task_id}",
                        "priority": "unknown",
                        "status": "🔴 Skipped",
                        "reason": reason
                    })
            st.dataframe(skipped_rows, use_container_width=True, hide_index=True)
    except (ValueError, KeyError) as exc:
        st.error(str(exc))
