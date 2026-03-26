# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

- Design:
    - Data layer: stores all details and information about the owner, pet, and task
    - Constraint layer: defines any constraints like time and priorities
    - Planning layer: ranks tasks, selects what fits, and orders them
    - Output layer: produces the final scheduled items, records why tasks were selected or skipped
- Classes: Owner, Pet, Tasks, Plan
    - Owner: add pets, set constraints
    - Pet: add tasks, add pets constraints
    - Tasks: set time window, set priorities
    - Plan: add tasks, plan date and time, show reasons

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

- Added relationships to my classes
- Added Plan->tasks relationships for easier tracking in the future

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

- My scheduler consider: time, priority, and preferences constraints
- I decided that priority constraints matter most based on real life scenarios, e.g. if your pet is sick, you should prioritize taking it to the vet before walking another pet.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

- Refactor the generate_schedule function, more helper functions means more readability, cleaner code, easier debugging. Trade-offs: little performance improvement
- Since the algorithms for soring and iterating are already optimized, improved readability helps with debugging and reasoning.
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

- Brainstorming feautures, building new features, and debugging
- The debugging prompts are the most helpful since they identify the bugs really fast and suggest viable solutions.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

- I didn't accept the way that the AI was displaying the tasks, it used task_id instead of clearer ways like name and the pet associated.
- I use tests, read the codes, and testing the app features myself.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

- Basically every logic, from sorting, filtering, to identifying conflicts and completing tasks.
- The tests are important because it's the fastest and most reliable way to test the application before rolling out features.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

- Mostly confident, there might be some edge test case that I couldn't think of.
- I couldn't think of one right now, but maybe with more time to test out my application, I might come up with more edge cases.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

- Able to build an app in a limited amount of time, testing out AI features.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

- Use another tech stack rather than just Streamlit and Python. Less writing, more coding.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

- AI makes mistakes, that's why testing is crucial when developing an application.