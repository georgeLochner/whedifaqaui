# Development Process

This directory documents the **autonomous agentic development workflow** - a generic approach for executing implementation plans using AI agents in containerized environments.

---

## Overview

The development process bridges planning (requirements, design, implementation plans) and execution. It defines how autonomous coding agents work within Docker-based development environments to execute implementation tasks.

**Key Principle**: Code is developed in volume-mapped containers where dependencies run in isolation, but source code remains on the host filesystem for immediate reflection of changes.

---

## Process Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PLANNING PHASE                                   │
│  (Human + Agent collaboration produces implementation plans)         │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│               ENVIRONMENT SCAFFOLDING PHASE                          │
│                                                                      │
│  Sets up the development environment so that implementation          │
│  agents can start coding immediately without infrastructure work.    │
│                                                                      │
│  Deliverables:                                                       │
│  • Docker Compose with all services running and healthy              │
│  • Dockerfiles with development stages (volume mounts, hot reload)  │
│  • Backend/frontend project skeletons (entry points, config, deps)  │
│  • Database migrations tooling configured                            │
│  • Test frameworks wired up and runnable                             │
│  • Dependency manifests committed (requirements.txt, package.json)  │
│                                                                      │
│  Exit criteria: `docker compose up` starts all services,             │
│  code edits reflect immediately, tests can execute in containers.    │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│              IMPLEMENTATION PHASES (1, 2, 3, ...)                    │
│                                                                      │
│  Each phase follows the agent execution loop:                        │
│                                                                      │
│  1. Agent reads implementation plan from docs/implementation/       │
│  2. Agent modifies source code on host filesystem                   │
│  3. Changes immediately reflect in running containers               │
│  4. Agent runs tests/verification inside containers                 │
│  5. Agent commits changes when verification passes                  │
│  6. Agent closes task and picks up next one                         │
│                                                                      │
│  Agents focus purely on application logic — no Docker setup,         │
│  no infrastructure configuration, no build system changes.           │
└─────────────────────────────────────────────────────────────────────┘
```

**Why a separate scaffolding phase?** In theory, infrastructure can be set up incrementally alongside feature work. In practice, environment setup often involves escalated privileges (e.g., `sudo sysctl` for OpenSearch), missing system dependencies that require debugging, Docker build failures, and port/network issues — all of which require human intervention. By front-loading this work into a dedicated phase where a human can monitor and resolve issues, the implementation phases can run with extended autonomy. The goal is that by the time an implementation agent starts, the only thing it needs to do is edit code, install packages, and run tests.

---

## Core Components

### 0. Orchestration Layer

**Purpose**: Coordinate work across multiple autonomous agents

**Architecture**: Two-tier agent system
- **Coordinator Agent**: Monitors task queue, dispatches work, handles failures
- **Coding Agents**: Execute individual tasks (planning or implementation)

**Task Hierarchy**:
```
Scaffolding Phase → Implementation Phases (1, 2, 3, ...)
                        └→ Features → Plan tasks → Implementation tasks → E2E verification
```

**Flow**:
1. Scaffolding phase sets up the development environment
2. For each implementation phase:
   a. Bootstrap task creates features
   b. Coordinator assigns "Plan tasks" for each feature
   c. Planning agent breaks feature into implementation tasks
   d. Coordinator assigns implementation tasks sequentially
   e. Final regression testing gates phase completion

**Detail**: [orchestration.md](orchestration.md)

---

### 1. Docker Environment Architecture

**Purpose**: Isolate dependencies while keeping code editable

**Structure**:
```
docker-compose.yml           # Base configuration (services, ports, health checks)
docker-compose.dev.yml       # Development overrides (volume mounts, hot reload)
```

**How it works**:
- Application code mounted as volumes: `./backend:/app`, `./frontend:/app`
- Hot reload enabled (server watches for file changes)
- No rebuild required when editing code
- Dependencies installed via `docker compose exec` (no rebuild for new packages either)
- Fast iteration cycle

**Detail**: [docker-workflow.md](docker-workflow.md)

---

### 2. Agent Development Protocol

**Purpose**: Define how autonomous agents work in this environment

**Key Behaviors**:
- Always start services in development mode
- Edit code on host filesystem (not inside containers)
- Run tests inside containers via `docker compose exec`
- Verify changes work before committing
- Handle handoffs when context limits reached

**Detail**: [agent-protocols.md](agent-protocols.md)

---

### 3. Task Management

**Purpose**: Track what needs to be built and coordinate multiple agents

**System**: Beads issue tracking (stored in `.beads/` directory)

**Workflow**:
- Implementation plans broken into atomic tasks
- Tasks have dependencies (what must be built first)
- Agents claim tasks, mark in-progress, and close when verified
- Progress visible across sessions and agents

**Detail**: [task-management.md](task-management.md)

---

### 4. Verification Loop

**Purpose**: Ensure code works before considering task complete

**Process**:
1. Agent implements feature/fix
2. Agent runs specified tests in container
3. If tests fail: fix and re-test
4. If tests pass: verify no regressions
5. Only then: commit and close task

**Principle**: Never close tasks with failing tests

**Detail**: [verification.md](verification.md)

---

## Why This Approach?

### For Agentic Development

✅ **Fast iteration**: No rebuild cycle slows down agent work
✅ **Isolated dependencies**: Agents don't need to install databases, search engines, etc.
✅ **Reproducible environment**: Same Docker setup across all agents and human developers
✅ **Verification built-in**: Tests run inside containers matching the target environment
✅ **Stateless agents**: Any agent can pick up any task with fresh context

### For Human Developers

✅ **Standard Docker workflow**: Familiar tools and commands
✅ **Code stays on host**: Use any IDE, no container editing
✅ **Easy debugging**: Logs, debuggers, profilers work normally
✅ **Hybrid work**: Humans and agents can work on same codebase

---

## Document Index

| Document | Purpose | Audience |
|----------|---------|----------|
| [orchestration.md](orchestration.md) | Coordinator/agent loop architecture | Project managers, coordinators |
| [docker-workflow.md](docker-workflow.md) | Docker development setup and usage | Agents, humans setting up environment |
| [agent-protocols.md](agent-protocols.md) | How agents should work in this environment | Autonomous coding agents |
| [task-management.md](task-management.md) | Task tracking and coordination with Beads | Agents, project managers |
| [verification.md](verification.md) | Testing and quality gates | Agents, QA engineers |
| [troubleshooting.md](troubleshooting.md) | Common issues and solutions | Everyone |

---

## Quick Start for Agents

1. **Read the implementation plan** for your assigned task (in `docs/implementation/`)
2. **Start development environment**:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```
3. **Edit code** on host filesystem (not inside containers)
4. **Test your changes**:
   ```bash
   docker compose exec <service> <test-command>
   ```
5. **Commit when tests pass**:
   ```bash
   git add <files> && git commit -m "..."
   ```
6. **Close the task**:
   ```bash
   bd close <task-id>
   ```

---

## Quick Start for Humans

1. **Set up environment**:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```
2. **Edit code** with your IDE (changes reflect immediately)
3. **View logs**:
   ```bash
   docker compose logs -f <service>
   ```
4. **Run tests**:
   ```bash
   docker compose exec backend pytest
   ```
5. **Stop environment**:
   ```bash
   docker compose down
   ```

---

## Related Documentation

- **Design docs** (`../design/`) - Technical architecture this development process implements
- **Implementation plans** (`../implementation/`) - What to build
- **Test specifications** (`../testing/`) - How to verify correctness
- **Agent prompts** (`/prompt/`) - Specific instructions for coding agents

---

## Extending This Process

This development process is designed to be generic and reusable across projects. To adapt for a new project:

1. **Create project-specific `docker-compose.yml` and `docker-compose.dev.yml`**
2. **Define project-specific agent protocols** (extend `agent-protocols.md`)
3. **Set up Beads issue tracking** for task management
4. **Create implementation plans** in `docs/implementation/`
5. **Point agents to this documentation** in their system prompts

The core pattern (dependencies in containers, code volume-mapped, hot reload) remains constant.
