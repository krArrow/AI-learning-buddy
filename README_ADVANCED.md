# AI Learning Buddy Advanced 🚀

An enterprise-grade GenAI learning platform built with LangGraph, LangChain, and RAG capabilities.

## 🎯 Project Overview

This is an advanced version of the AI Learning Buddy that demonstrates production-ready GenAI platform engineering using:

- **LangGraph**: Multi-agent orchestration and state management
- **LangChain**: LLM abstraction and tool integration
- **RAG**: Vector search for personalized resource recommendations
- **SQLAlchemy ORM**: Robust database layer with relationships
- **Agentic Architecture**: Specialized agents for different learning tasks

---

## 📅 Development Progress

### ✅ Day 1: Project Setup & Database Foundation (COMPLETED)

**Deliverables:**
- ✓ Complete directory structure
- ✓ Dependencies configured (requirements.txt)
- ✓ SQLAlchemy ORM models (6 tables)
- ✓ Database manager with singleton pattern
- ✓ Configuration management (Pydantic)
- ✓ Structured logging system
- ✓ CRUD operations

**Database Schema:**
- `learning_goals`: User learning goals with preferences
- `roadmaps`: Generated learning roadmaps
- `tasks`: Daily learning tasks with resources
- `progress`: Daily progress tracking
- `conversations`: AI conversation history
- `assessments`: Knowledge gap assessments

### 🔜 Day 2: LangGraph Core Setup (UPCOMING)
- State management
- Graph definition
- Node implementations
- Basic workflow

### 🔜 Day 3: Agent Implementation (UPCOMING)
- Goal clarification agent
- Content curation agent
- Assessment agent
- Adaptation agent

### 🔜 Day 4: RAG & Tools (UPCOMING)
- Vector store setup
- Resource search
- Tool integrations
- Analytics engine

### 🔜 Day 5: UI & Integration (UPCOMING)
- Streamlit interface
- End-to-end workflow
- Testing
- Documentation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│       Streamlit UI Layer            │
│   (Interactive Learning Interface)  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      LangGraph Orchestration        │
│  ┌─────────────────────────────┐   │
│  │   State Management          │   │
│  │   ┌──────┐  ┌──────┐       │   │
│  │   │Node 1│→ │Node 2│ → ... │   │
│  │   └──────┘  └──────┘       │   │
│  └─────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
     ┌─────────┼─────────┐
     ▼         ▼         ▼
┌─────────┐┌─────────┐┌─────────┐
│ Agents  ││  Tools  ││ Memory  │
│         ││         ││         │
└────┬────┘└────┬────┘└────┬────┘
     │          │          │
     └──────────┼──────────┘
                ▼
     ┌─────────────────────┐
     │   LLM Service       │
     │   (OpenAI API)      │
     └──────────┬──────────┘
                │
     ┌──────────┼──────────┐
     ▼          ▼          ▼
┌─────────┐┌─────────┐┌─────────┐
│Database ││Vector   ││External │
│SQLite   ││Store    ││APIs     │
└─────────┘└─────────┘└─────────┘
```

---

## 🗂️ Project Structure

```
ai-learning-buddy-advanced/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── README_ADVANCED.md         # This file
│
├── src/
│   ├── core/                  # LangGraph core
│   │   ├── graph.py          # Graph definition
│   │   ├── state.py          # State management
│   │   └── nodes/            # Graph nodes
│   │
│   ├── agents/               # Specialized agents
│   │   ├── goal_clarifier.py
│   │   ├── content_curator.py
│   │   ├── assessment_agent.py
│   │   └── adaptation_agent.py
│   │
│   ├── tools/                # LangChain tools
│   │   ├── course_search.py
│   │   ├── difficulty_scorer.py
│   │   └── analytics_engine.py
│   │
│   ├── memory/               # Memory management
│   │   ├── conversation_memory.py
│   │   ├── learning_memory.py
│   │   └── vector_store.py
│   │
│   ├── database/             # Database layer
│   │   ├── models.py         # SQLAlchemy models ✓
│   │   ├── db.py            # DB manager ✓
│   │   └── crud.py          # CRUD operations ✓
│   │
│   ├── llm/                  # LLM configuration
│   │   ├── config.py
│   │   ├── prompts.py
│   │   └── callbacks.py
│   │
│   └── utils/               # Utilities
│       ├── config.py        # Settings ✓
│       ├── logger.py        # Logging ✓
│       └── validators.py
│
├── tests/                   # Unit tests
├── data/                    # Runtime data
└── docs/                    # Documentation
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
cd d:\GENAI\AI-learning-buddy\
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

4. **Run the application**
```bash
streamlit run app.py
```

---

## 📊 Database Schema

### LearningGoal
- **Purpose**: Store user learning goals and preferences
- **Key Fields**: goal_text, level, daily_minutes, learning_style, pace
- **Relationships**: Has many roadmaps, tasks, progress records

### Roadmap
- **Purpose**: Store generated learning roadmaps
- **Key Fields**: roadmap_json, modules_count, estimated_weeks
- **Relationships**: Belongs to learning goal

### Task
- **Purpose**: Daily learning tasks with completion tracking
- **Key Fields**: task_text, why_text, resources_json, difficulty_score
- **Relationships**: Belongs to learning goal

### Progress
- **Purpose**: Track daily learning progress
- **Key Fields**: date, tasks_completed, completion_percentage
- **Relationships**: Belongs to learning goal

### Conversation
- **Purpose**: Store AI conversation history
- **Key Fields**: agent_type, user_message, ai_response
- **Relationships**: Belongs to learning goal

### Assessment
- **Purpose**: Knowledge gap detection and tracking
- **Key Fields**: question, user_answer, is_correct, gap_identified
- **Relationships**: Belongs to learning goal

---

## 🔧 Configuration

All configuration is managed through environment variables (see `.env.example`):

- **OpenAI**: API key, model selection, temperature
- **Database**: Connection URL, echo settings
- **Vector Store**: ChromaDB configuration
- **Application**: Debug mode, log level
- **LangGraph**: Max iterations, recursion limit
- **Agents**: Model selection per agent
- **Memory**: History size limits
- **Features**: Feature flags for modules

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_graph.py
```

---

## 📚 Key Technologies

- **LangGraph 0.0.10**: Multi-agent orchestration
- **LangChain 0.1.0**: LLM abstraction layer
- **SQLAlchemy 2.0.23**: ORM for database
- **Pydantic 2.5.0**: Data validation
- **ChromaDB 0.4.18**: Vector database
- **Streamlit 1.28.2**: Web interface
- **OpenAI GPT-4**: Language model

---

## 🎓 Learning Outcomes

This project demonstrates:

1. **Production-Ready Architecture**
   - Separation of concerns
   - Singleton patterns
   - Type safety with Pydantic
   - Comprehensive error handling

2. **Advanced LangGraph Usage**
   - State management
   - Multi-agent workflows
   - Conditional routing
   - Memory integration

3. **Database Best Practices**
   - ORM relationships
   - CRUD abstractions
   - Migration-ready schema
   - Connection pooling

4. **Modern Python Development**
   - Type hints throughout
   - Structured logging
   - Environment-based config
   - Comprehensive testing

---

## 🛠️ Development Roadmap

### Phase 1: Foundation ✅
- [x] Project structure
- [x] Database layer
- [x] Configuration management
- [x] Logging system

### Phase 2: Core (Day 2)
- [ ] LangGraph setup
- [ ] State management
- [ ] Node implementations
- [ ] Basic workflow

### Phase 3: Intelligence (Day 3)
- [ ] Agent implementations
- [ ] Tool integrations
- [ ] Memory management
- [ ] Conversation handling

### Phase 4: Enhancement (Day 4)
- [ ] Vector store setup
- [ ] RAG implementation
- [ ] Analytics engine
- [ ] Resource curation

### Phase 5: Polish (Day 5)
- [ ] Streamlit UI
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Documentation

---

## 📝 License

MIT License - Educational and portfolio use

---

## 🤝 Contributing

This is an educational project. Feel free to:
- Fork and experiment
- Suggest improvements
- Report issues
- Share learnings

---

## 📧 Contact

Built with ❤️ to showcase enterprise GenAI engineering skills.

**Current Status**: Day 1 Complete - Database Foundation Ready ✅
