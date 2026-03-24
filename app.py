import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Plan

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown("Welcome to the PawPal+ scheduler demo.")

st.divider()

st.subheader("Owner + Pet Setup")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
age_years = st.number_input("Pet age (years)", min_value=0, max_value=40, value=2)
daily_minutes = st.number_input("Daily available minutes", min_value=0, max_value=600, value=60)

if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        owner_id="owner-1",
        name=owner_name,
        daily_available_minutes=int(daily_minutes),
    )

if "pet" not in st.session_state:
    st.session_state.pet = Pet(
        pet_id="pet-1",
        name=pet_name,
        species=species,
        age_years=int(age_years),
    )
    st.session_state.owner.add_pet(st.session_state.pet)

if "task_counter" not in st.session_state:
    st.session_state.task_counter = 0

owner = st.session_state.owner
pet = st.session_state.pet

owner.name = owner_name
owner.set_daily_available_minutes(int(daily_minutes))
pet.name = pet_name
pet.species = species
pet.age_years = int(age_years)

st.divider()

st.subheader("Add Task")
st.caption("Create task objects and add them to your pet using pawpal_system methods.")

col1, col2, col3, col4 = st.columns(4)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high", "critical"], index=2)
with col4:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "monthly", "once"], index=0)

if st.button("Add task"):
    try:
        st.session_state.task_counter += 1
        task_id = f"task-{st.session_state.task_counter}"
        task = Task(
            task_id=task_id,
            description=task_title,
            time_minutes=int(duration),
            frequency=frequency,
            priority=priority,
        )
        task.set_priority(priority)
        pet.add_task(task)
        st.success(f"Added task: {task.description}")
    except (ValueError, KeyError) as exc:
        st.error(str(exc))

current_tasks = [
    {
        "task_id": t.task_id,
        "description": t.description,
        "duration_minutes": t.time_minutes,
        "priority": t.priority,
        "frequency": t.frequency,
        "completed": t.completed,
    }
    for t in pet.get_tasks()
]

if current_tasks:
    st.write("Current tasks:")
    st.table(current_tasks)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate a plan using your Plan methods.")

if st.button("Generate schedule"):
    try:
        plan = Plan(
            plan_id=f"plan-{date.today().isoformat()}",
            plan_date=date.today().isoformat(),
            total_minutes=0,
        )
        plan.generate_daily_schedule(owner, pet)

        st.success("Schedule generated.")
        st.write("Schedule items:")
        st.table(plan.get_schedule())
        st.text(plan.explain_choices())

        if plan.skipped_reasons:
            st.write("Skipped reasons:")
            st.table(
                [
                    {"task_id": task_id, "reason": reason}
                    for task_id, reason in plan.skipped_reasons.items()
                ]
            )
    except (ValueError, KeyError) as exc:
        st.error(str(exc))
