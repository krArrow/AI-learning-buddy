# AI Learning Buddy 📚

A GenAI-powered learning companion that creates personalized learning plans and adapts them based on your progress.

## 🎯 What This Demonstrates

This project showcases **3 months of GenAI engineering experience** through:

1. **Prompt Engineering & Chaining**
   - Structured 3-prompt chain with clear data flow
   - Deterministic outputs through explicit formatting
   - Context management across prompts

2. **System Architecture**
   - Clean separation of concerns (LLM, Storage, Business Logic, UI)
   - Singleton pattern for resource management
   - Abstracted LLM service for easy model swapping

3. **Production-Ready Practices**
   - SQLite for structured persistence (ACID compliance)
   - Error handling and validation
   - Explicit parsing of LLM outputs
   - Session state management

4. **Practical AI Application**
   - Solves a real problem (learning path guidance)
   - Adapts based on user behavior
   - Explainable outputs (every task has a "why")

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                 Streamlit UI                    │
│  (Welcome Screen, Plan Display, Task Tracking)  │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│           Learning Manager (Core Logic)         │
│  • Orchestrates 3-prompt chain                  │
│  • Manages state transitions                    │
│  • Parses LLM outputs                           │
└─────────┬──────────────────────┬────────────────┘
          │                      │
          ▼                      ▼
┌──────────────────┐    ┌──────────────────┐
│   LLM Service    │    │ Storage Manager  │
│  • OpenAI API    │    │  • SQLite        │
│  • Prompt exec   │    │  • CRUD ops      │
└──────────────────┘    └──────────────────┘
```

---

## 🔄 How It Works: The 3-Prompt Chain

### Prompt 1: Goal → Learning Roadmap
**Input:** User's learning goal, level, available time  
**Output:** Structured learning roadmap with 3-5 modules  
**Purpose:** Create the big-picture plan

```
User: "Learn Python for data analysis"
        ↓
AI generates:
  MODULE 1: Python Fundamentals (2 weeks)
  MODULE 2: Data Structures (2 weeks)
  MODULE 3: Pandas & NumPy (3 weeks)
  ...
```

### Prompt 2: Roadmap → Daily Tasks
**Input:** The roadmap from Prompt 1  
**Output:** 7 specific daily tasks for the first module  
**Purpose:** Break down modules into actionable steps

```
Roadmap (Module 1)
        ↓
AI generates:
  DAY 1: Install Python and write "Hello World"
  DAY 2: Learn variables and data types
  ...
```

### Prompt 3: Progress → Adapted Tasks
**Input:** Completed tasks, incomplete tasks, original roadmap  
**Output:** Next 7 tasks adapted to user's progress  
**Purpose:** Personalize based on actual performance

```
Progress: 5/7 tasks completed, 2 skipped
        ↓
AI adapts:
  - If struggling: Easier tasks, more review
  - If excelling: More challenging tasks
  - Fills gaps from incomplete tasks
```

---

## 📁 Project Structure

```
ai_learning_buddy/
│
├── app.py                    # Streamlit UI (main entry point)
├── requirements.txt          # Dependencies
├── README.md                 # This file
├── .env.example              # API key template
│
├── src/                      # Core application logic
│   ├── __init__.py
│   ├── prompts.py            # All prompt templates
│   ├── llm_service.py        # OpenAI API abstraction
│   ├── storage.py            # SQLite persistence
│   └── learning_manager.py   # Business logic orchestration
│
└── data/                     # Generated at runtime
    └── learning_buddy.db     # SQLite database
```

---

## 🗄️ Database Schema

### Tables

**learning_goals**
- Stores user learning goals and preferences
- One active goal at a time

**roadmaps**
- Stores generated learning roadmaps
- Linked to goals via foreign key

**tasks**
- Stores daily tasks with completion status
- Tracks progress over time

```sql
CREATE TABLE learning_goals (
    id INTEGER PRIMARY KEY,
    goal TEXT NOT NULL,
    level TEXT NOT NULL,
    daily_minutes INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1
);

CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    goal_id INTEGER,
    day_number INTEGER,
    task_text TEXT,
    why_text TEXT,
    estimated_minutes INTEGER,
    is_completed BOOLEAN DEFAULT 0,
    completed_at TIMESTAMP
);
```

---

## 🚀 How to Run

### Prerequisites
- Python 3.8+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone/download this project**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up API key**

**Windows:**
```bash
set OPENAI_API_KEY=your-api-key-here
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=your-api-key-here
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Open your browser**
The app will automatically open at `http://localhost:8501`

---

## 💡 How to Use

### Step 1: Create Your Learning Plan
1. Navigate to "Get Started"
2. Enter your learning goal (e.g., "Learn React")
3. Select your current level
4. Set daily available time
5. Click "Generate My Learning Plan"

### Step 2: Follow Daily Tasks
1. Go to "My Learning Plan" → "Daily Tasks"
2. Each day, complete your assigned task
3. Check the box when done
4. Read the "Why" explanation to understand the purpose

### Step 3: Adapt Your Plan
1. After completing several tasks, click "Get Next Tasks"
2. The AI analyzes your progress
3. Generates adapted tasks based on:
   - Tasks you completed
   - Tasks you skipped
   - Your pace and performance

---

## 🎨 Key Features

### 1. Explainable AI
Every task includes a "Why" explanation, so you understand the purpose.

### 2. Progress Tracking
Visual progress bar and completion metrics.

### 3. Adaptive Learning
The plan adjusts based on what you actually complete.

### 4. Persistent Memory
Your progress is saved locally - come back anytime.

### 5. Structured Output
Deterministic LLM parsing ensures reliable task extraction.

---

## 🔧 Technical Decisions

### Why SQLite over JSON?
✅ **Structured queries** (get tasks by status, date)  
✅ **ACID compliance** for reliable progress updates  
✅ **Easy to extend** with indexes and relationships  
✅ **Still single-file** and zero-config

### Why OpenAI API?
✅ Industry standard for GenAI applications  
✅ Reliable structured outputs  
✅ Easy to swap models (GPT-4, GPT-3.5-turbo)

### Why Streamlit?
✅ Rapid prototyping  
✅ Built-in state management  
✅ Clean, simple UI without frontend complexity

---

## 🎓 What I Learned Building This

1. **Prompt chaining is powerful but requires careful data flow**
   - Each prompt's output becomes the next prompt's input
   - Context management is critical

2. **LLM outputs need explicit parsing**
   - Can't rely on raw text
   - Regex + structured prompts work well together

3. **State management matters**
   - Singletons help avoid recreation of expensive resources
   - SQLite provides reliable persistence

4. **Real-world AI apps need graceful degradation**
   - Handle API failures
   - Validate LLM outputs
   - Provide clear error messages

---

## 🛠️ Future Enhancements (Out of Scope)

These are intentionally NOT included to keep the project focused:

- ❌ Multi-user authentication
- ❌ Cloud deployment
- ❌ Advanced analytics
- ❌ Integration with learning platforms
- ❌ Multi-modal inputs (images, audio)

This is a **clean engineering showcase**, not a production startup.

---

## 📊 Example Flow

```
User Input:
  Goal: "Learn Python for data analysis"
  Level: Beginner
  Time: 30 min/day

↓ Prompt 1 (Goal → Roadmap)

Roadmap Generated:
  Module 1: Python Basics (2 weeks)
  Module 2: Pandas & NumPy (3 weeks)
  Module 3: Data Visualization (2 weeks)

↓ Prompt 2 (Roadmap → Tasks)

Initial Tasks:
  Day 1: Install Python, run "Hello World"
  Day 2: Learn variables and data types
  ...
  Day 7: Build a simple calculator

↓ User completes 5/7 tasks

↓ Prompt 3 (Progress → Adapt)

Adapted Tasks:
  Day 8: Review functions (missed earlier)
  Day 9: Start learning lists
  ...
```

---

## 🤝 Contributing

This is an educational showcase project. Feel free to:
- Fork and experiment
- Use as a template for similar projects
- Provide feedback on architecture decisions

---

## 📝 License

MIT License - feel free to use this for learning and showcasing your skills.

---

## 🙋 Questions?

This project demonstrates practical GenAI platform engineering. Key takeaways:

1. **Prompt chaining** creates powerful multi-step workflows
2. **Structured parsing** makes LLM outputs reliable
3. **Clean architecture** separates concerns effectively
4. **Persistence** enables stateful AI applications

Built with ❤️ to showcase real-world GenAI engineering skills.