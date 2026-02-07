# Whedifaqaui - Documentation

This directory contains all planning, design, implementation, and testing documentation for the Whedifaqaui Video Knowledge Management System.

---

## Documentation Structure

```
docs/
├── README.md                # This file - overview of documentation structure
├── requirements/            # WHAT to build (user stories, phases)
├── design/                  # HOW to build it (technical architecture)
├── implementation/          # Step-by-step implementation plans
├── testing/                 # Test specifications per phase
└── reference/               # Detailed specs referenced from design docs
```

---

## Autonomous Agentic Development Process

This project follows a structured, agent-assisted development workflow with distinct phases:

### Phase 1: Requirements Definition

**Location**: `docs/requirements/`

**Process**: Iterative discussion between human creator and planning agent

**Outputs**:
- User stories organized by epic
- Implementation phases (MVP → full feature set)
- UI mockups and wireframes
- Phase-stories matrix (which stories belong to which phase)

**Entry Point**: [requirements/README.md](requirements/README.md)

**Goal**: Define **what** the system must do from a user perspective

---

### Phase 2: Technical Design

**Location**: `docs/design/`

**Process**: Iterative discussion between human creator and design agent

**Outputs**:
- System architecture and component diagrams
- Technology stack with pinned versions
- Data models (database schemas, search indices)
- Processing pipelines and query flows
- Integration patterns (e.g., Claude wrapper module)
- Deployment configuration

**Entry Point**: [design/README.md](design/README.md)

**Goal**: Define **how** to build the system - the technical source of truth

**Key Principle**: Design documents describe system behavior rather than abstract categories. Each document answers "how does X work?" rather than "what is the theory of X?"

---

### Phase 3: Implementation Planning

**Location**: `docs/implementation/`

**Process**: Generated from design specs, broken down into implementable tasks

**Outputs**:
- Phase-by-phase implementation plans
- Task breakdowns with file-level specifications
- Dependency ordering (what must be built first)
- Verification criteria for each task

**Structure**: One implementation plan per phase (e.g., `phase1.md`, `phase2.md`)

**Goal**: Translate design into actionable development tasks

---

### Phase 4: Test Specification

**Location**: `docs/testing/`

**Process**: Generated alongside implementation plans

**Outputs**:
- Test specifications per phase
- Acceptance criteria verification steps
- Regression test packs
- Quality gates for phase completion

**Structure**: One test spec per phase (e.g., `phase1-test-specification.md`)

**Goal**: Define how to verify each phase is complete and correct

---

### Phase 5: Development Execution

**Location**: `docs/development/`

**Process**: Coordinator agent dispatches tasks to autonomous coding agents working in Docker-based development environments

**Workflow**:
1. Bootstrap task creates features for the phase
2. Coordinator assigns "Plan tasks" to planning agents
3. Planning agents break features into atomic implementation tasks
4. Coordinator assigns implementation tasks sequentially to coding agents
5. Coding agents: start services, edit code, run tests, commit, close tasks
6. Final E2E verification per feature
7. Regression testing gates phase completion

**Key Components**:
- **Orchestration**: Two-tier agent system (coordinator + coding agents)
- **Docker development mode**: Dependencies in containers, code volume-mapped for hot reload
- **Beads issue tracking**: Task hierarchy and dependency management
- **Agent protocols**: Standardized workflows for autonomous development
- **Verification loop**: Never close tasks with failing tests

**Entry Point**: [development/README.md](development/README.md)

**Goal**: Execute implementation plans autonomously while maintaining quality through fast iteration and continuous verification

---

## How to Use This Documentation

### As a Human Creator

1. **Start with requirements** - `requirements/README.md`
   - Understand the problem and user needs
   - Review user stories and phases

2. **Review the design** - `design/README.md`
   - Understand the technical architecture
   - See how components fit together
   - Identify key design decisions

3. **Check implementation progress** - `implementation/`
   - See what phase is currently being built
   - Understand task dependencies
   - Review completed vs remaining work

4. **Verify quality** - `testing/`
   - Review test specifications
   - Ensure acceptance criteria are met

### As a Planning Agent

1. **For requirements work**: Read existing user stories in `requirements/`, discuss with creator, update or create new requirement docs

2. **For design work**: Read existing design docs in `design/`, discuss technical decisions with creator, update or create new design docs

3. **For implementation planning**: Read design docs, break down into tasks, create implementation plans in `implementation/`

### As a Coding Agent

1. **Before starting**: Read relevant design docs and implementation plan for your assigned task
2. **During work**: Follow implementation plan, verify against design specs
3. **Before closing**: Run tests specified in testing docs, verify acceptance criteria

---

## Documentation Principles

### 1. Single Source of Truth

- **Requirements** define what users need
- **Design** defines technical decisions
- **Implementation** defines build order
- **Testing** defines verification

Each layer builds on the previous. Don't duplicate - reference.

### 2. Behavior Over Abstraction

Design documents focus on "how things work" rather than abstract theory:
- ✅ "processing-pipeline.md" - describes the 6-stage ingestion flow
- ❌ "architecture.md" - abstract architectural patterns

### 3. Actionable and Testable

Every implementation task should:
- Reference specific files to create/modify
- Include verification steps
- Map to test specifications

### 4. Evolving Documentation

Documentation is updated as:
- Requirements change during discovery
- Design decisions are made or revised
- Implementation reveals better approaches
- Testing uncovers gaps

---

## Current Status

| Phase | Status | Location |
|-------|--------|----------|
| Requirements Definition | ✅ Complete | `requirements/` |
| Technical Design | ✅ Complete | `design/` |
| Implementation Planning | ✅ Complete (Phase 0-3) | `implementation/` |
| Test Specification | ✅ Complete (Phase 1-2) | `testing/` |
| Development Execution | ✅ Documented | `development/` *(see `.beads/` for task tracking)* |

---

## Development Process (Generic Pattern)

The `development/` directory contains a **reusable pattern for autonomous agentic development** that can be applied to any software project:

### Core Concept

**Dependencies in containers, source code volume-mapped from host for immediate reflection of changes.**

This enables:
- Fast iteration without rebuilds (code changes reflect in ~seconds)
- Isolated, reproducible environments for both agents and humans
- Continuous verification through containerized test execution
- Stateless agents that can pick up any task with fresh context

### Pattern Components

1. **Docker Workflow** ([development/docker-workflow.md](development/docker-workflow.md))
   - Development mode (volume mounts, hot reload)
   - Production mode (baked-in code, requires rebuild)
   - When to use which mode

2. **Agent Protocols** ([development/agent-protocols.md](development/agent-protocols.md))
   - How agents initialize, develop, test, commit, and close tasks
   - Decision trees for common scenarios
   - Anti-patterns to avoid

3. **Task Management** ([development/task-management.md](development/task-management.md))
   - Beads issue tracking workflow
   - Task lifecycle and dependencies
   - Progress monitoring

4. **Verification** ([development/verification.md](development/verification.md))
   - Testing strategies and quality gates
   - Never close tasks with failing tests
   - Manual verification procedures

5. **Troubleshooting** ([development/troubleshooting.md](development/troubleshooting.md))
   - Common issues and solutions
   - Debugging strategies
   - Quick reference

### Version Pinning for Docker Dependencies

**Pin exact Docker image versions** to prevent agents from triggering large image downloads (OpenSearch = 826MB).

**Key practices:**
- Use patch versions: `postgres:16.1-alpine` NOT `postgres:16-alpine` or `:latest`
- Document all versions in `technology-stack.md` in the `Docker Images` section, this enforced as invariant in the coding agent instructions

**Example:**
```markdown
⚠️ VERSIONS FROZEN | Service | Docker Image |
| PostgreSQL | postgres:16.1-alpine |
| OpenSearch | opensearchproject/opensearch:2.11.1 |
```

See [technology-stack.md](design/technology-stack.md) for full implementation.

---

**This pattern is project-agnostic and can be adapted to any language/framework by customizing docker-compose files and test commands.**

---

## Quick Navigation

### I want to understand...

- **What the system does** → [requirements/README.md](requirements/README.md)
- **How it's architected** → [design/README.md](design/README.md)
- **What gets built when** → [requirements/implementation-phases.md](requirements/implementation-phases.md)
- **How to implement Phase X** → [implementation/phaseX.md](implementation/)
- **How to verify Phase X** → [testing/phaseX-test-specification.md](testing/)
- **How to develop (Docker, agents, testing)** → [development/README.md](development/README.md)
- **Technology choices** → [design/technology-stack.md](design/technology-stack.md)
- **How to deploy** → [design/deployment.md](design/deployment.md)

### I need to work on...

- **User stories** → [requirements/](requirements/)
- **Architecture decisions** → [design/decisions.md](design/decisions.md)
- **Database schema** → [design/data-model.md](design/data-model.md)
- **Video processing** → [design/processing-pipeline.md](design/processing-pipeline.md)
- **Search functionality** → [design/query-flow.md](design/query-flow.md)
- **API endpoints** → [design/search-api.md](design/search-api.md)
- **Claude integration** → [design/claude-integration.md](design/claude-integration.md)
- **Docker development setup** → [development/docker-workflow.md](development/docker-workflow.md)
- **Agent development protocols** → [development/agent-protocols.md](development/agent-protocols.md)
- **Task tracking** → [development/task-management.md](development/task-management.md)
- **Testing and verification** → [development/verification.md](development/verification.md)

---

## Contributing to Documentation

When updating documentation:

1. **Keep it current** - Update docs when code or decisions change
2. **Link, don't duplicate** - Reference other docs rather than repeating information
3. **Be specific** - Use concrete examples, file paths, and commands
4. **Think ahead** - Consider both human readers and AI agents as your audience
5. **Stay focused** - Each document should have a clear, narrow scope

---

## Questions or Issues?

If documentation is unclear, outdated, or missing:
1. Check if information exists in a linked document
2. Review git history to understand context
3. Ask the human creator for clarification
4. Update documentation after gaining understanding
