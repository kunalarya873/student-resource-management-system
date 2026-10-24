# Agentic AI Harness System Architecture & Agent Matrix

> **Project:** CRM Integration & Agentic AI Platform  
> **Orchestration Framework:** Corex Engine  
> **Backend & State Layer:** Convex (BaaS, Reactive DB, MCP Server Hub)  
> **Document Status:** Living System Specification (`.agents/AGENTS.md`)

---

## 1. Executive System Overview

The **Agentic AI Harness System** is an autonomous multi-agent engineering ecosystem designed to build, test, review, and deploy production-grade software. The platform separates high-level cognitive tasks (**planning, judging, routing**) from low-level execution (**researching, coding, testing, PR actions**).

```
                     ┌─────────────────────────────────────────┐
                     │          COREX ORCHESTRATOR             │
                     │  (Plans • Thinks • Delegates • Judges)  │
                     └────────────────────┬────────────────────┘
                                          │
       ┌──────────────────┬───────────────┴───────────────┬──────────────────┐
       ▼                  ▼                               ▼                  ▼
┌──────────────┐   ┌──────────────┐                ┌──────────────┐   ┌──────────────┐
│ Architecture │   │   Feature    │                │   Testing    │   │ Code Review  │
│    Agents    │   │ Orchestrator │                │    Agents    │   │    Agents    │
└──────┬───────┘   └──────┬───────┘                └──────┬───────┘   └──────┬───────┘
       │                  │                               │                  │
       └──────────────────┴───────────────┬───────────────┴──────────────────┘
                                          ▼
                             ┌─────────────────────────┐
                             │    DEPLOYMENT AGENT     │
                             │ (Release & Verification)│
                             └─────────────────────────┘
                                          │
                             ┌────────────▼────────────┐
                             │      CONVEX BaaS        │
                             │ (DB, Queues, Real-time) │
                             └─────────────────────────┘
```

---

## 2. The Master Orchestrator: Corex Engine

The **Corex Orchestrator** is the top-level supervisor operating above all specialized sub-agents. It does not write line-by-line boilerplate; instead, it enforces cognitive integrity, maintains system state, and routes subtasks.

### Core Cognitive Pillars
1. **Plans:** Deconstructs user requirements into a Directed Acyclic Graph (DAG) of executable milestones.
2. **Thinks:** Chooses the optimal execution path, evaluates trade-offs, and balances technical debt against velocity.
3. **Delegates:** Dispatches bounded subtasks with strict context budgets to domain-specific sub-agents.
4. **Judges:** Validates outputs of each sub-agent against acceptance criteria and architectural contracts before approving progression.
5. **Researches:** Assesses high-level architectural fit and compatibility across library ecosystems.
6. **Orchestrates:** Governs the end-to-end pipeline: Prompt $\rightarrow$ Architecture $\rightarrow$ Code $\rightarrow$ Test $\rightarrow$ Review $\rightarrow$ Deploy.

---

## 3. Detailed Agent Breakdown & Matrix

### Tier 1: Architecture Agents
Responsible for system boundaries, data governance, and scalable structural foundations.

#### 1.a. Domain Model Agent
* **Core Responsibilities:**
  * Designs relational schemas, document schemas, and Entity Relationship Diagrams (ERDs).
  * Establishes data integrity rules, foreign keys, cascade policies, and indexing strategies.
  * **GDPR & Privacy Compliance:** Enforces PII data segregation, consent tracking schemas, and Right-to-be-Forgotten erasure cascades.
  * **Security & Access:** Designs Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) schemas. Defines field-level and row-level encryption requirements (at-rest & in-transit).
* **When to Use:**
  * Whenever a new entity, relationship, or data flow is introduced.
  * During security audits of stored user data and compliance reviews.
* **Recommended Model:** **Claude 3.7 / 3.5 Sonnet (Extended Thinking)** or **Claude Opus** (for nuanced regulatory logic, entity cardinality, and zero-defect data modeling).

#### 1.b. Codebase Design Agent
* **Core Responsibilities:**
  * Generates zero-downtime database migration files.
  * Defines architectural patterns (Clean Architecture, Hexagonal, DDD, CQRS).
  * Structures business logic layers, service boundaries, and dependency injection containers.
  * Optimizes query performance, connection pooling, and indexing.
  * Implements asynchronous processing: message queues (BullMQ, Celery, Convex scheduled functions), background workers, and retry backoffs.
  * Implements enterprise-grade authentication (OAuth2, OIDC, JWT revocation, session stores) with GDPR-compliant audit trails.
* **When to Use:**
  * Setting up new modules, writing database migrations, or adding background workers.
  * Refactoring query bottlenecks and implementing caching strategies (Redis / Convex reactive queries).
* **Recommended Model:** **Claude 3.7 / 3.5 Sonnet** (exceptional code organization and modular system design).

---

### Tier 2: Feature Orchestrator Agents
Translates high-level feature specs into clean, functioning implementations.

#### 2.a. Feature Researcher Agent
* **Core Responsibilities:**
  * Evaluates feature feasibility against existing codebase patterns and dependencies.
  * Identifies reusable utilities, shared types, and potential conflicts.
  * Gathers API documentation for third-party integrations (CRM providers, Stripe, etc.).
  * Produces an Implementation Plan detailing files to create, files to modify, and edge-case hazards.
* **When to Use:**
  * Step 1 of any feature ticket before code changes begin.
* **Recommended Model:** **Gemini 2.0 Pro / Flash** or **Claude 3.5 Sonnet** (fast context ingestion across large codebases).

#### 2.b. Feature Executor Agent
* **Core Responsibilities:**
  * Consumes the approved Implementation Plan and context bundles.
  * Writes modular, strongly-typed, production-ready code.
  * Connects API controllers, service handlers, DB queries, and UI components.
  * Adheres strictly to the style guides and rules defined in `.agents/rules/`.
* **When to Use:**
  * Step 2 of feature delivery: translating verified plans into code.
* **Recommended Model:** **GPT-4o** or **Claude 3.5 Sonnet** (high-speed, highly reliable code completion and syntax precision).

---

### Tier 3: Testing Agents
Ensures code correctness under both normal and adverse operational conditions.

#### 3.a. Edge Case Researcher Agent
* **Core Responsibilities:**
  * Discovers real-world operational failure modes (not just standard unit test boundary numbers).
  * Analyzes scenarios: distributed race conditions, partial network outages, webhook retries, duplicate idempotency keys, rate limit exhausts, corrupted payloads, timezone boundaries, and concurrent mutation conflicts.
  * Formulates edge-case test matrices.
* **When to Use:**
  * Before writing test suites for mission-critical business logic or transactional workflows.
* **Recommended Model:** **Claude 3.7 Sonnet (Thinking)** or **OpenAI o3 / o1** (adversarial thinking and multi-step causal reasoning).

#### 3.b. Test Executor Agent
* **Core Responsibilities:**
  * Implements automated test suites based on the Edge Case matrix:
    * **E2E Tests:** Playwright / Cypress for browser journeys.
    * **Integration Tests:** API contract validation, auth flows, and service integrations.
    * **Database Tests:** Migration rollback tests, seed verification, and transaction isolation tests.
    * **Mock Services:** Realistic HTTP/gRPC mocks for external CRM endpoints.
* **When to Use:**
  * Validating feature implementations and running continuous integration pipelines.
* **Recommended Model:** **Claude 3.5 Sonnet** or **GPT-4o** (scaffolding robust fixtures, assertion patterns, and test suites).

---

### Tier 4: Code Review Agents
Acts as the automated pull-request guardian ensuring quality and backward compatibility.

#### 4.a. Review Researcher Agent
* **Core Responsibilities:**
  * Verifies adherence to project standards, security practices (OWASP Top 10), and performance budgets.
  * Validates that API documentation (OpenAPI 3.1) matches code changes.
  * Performs regression risk analysis: checks if modified functions break existing callers or database contracts.
* **When to Use:**
  * Triggered automatically upon PR creation or prior to code merge.
* **Recommended Model:** **Claude 3.7 Sonnet (Thinking)** or **Claude Opus** (deep static analysis and semantic diff comprehension).

#### 4.b. Review Executor Agent
* **Core Responsibilities:**
  * Posts structured, actionable PR review comments on GitHub with inline code suggestions.
  * Assigns PR labels (`needs-work`, `security-flag`, `approved`).
  * If blockers are discovered, automatically opens linked GitHub Issues with reproduction steps and assigns them to the responsible agent.
* **When to Use:**
  * Generating PR feedback and synchronizing GitHub project boards.
* **Recommended Model:** **Claude 3.5 Sonnet** or **GPT-4o** (structured formatting, GitHub API interaction, and concise communication).

---

### Tier 5: Deployment & Release Agent
Guarantees reliable releases with zero downtime.

#### Deployment Agent
* **Core Responsibilities:**
  * Executes pre-deployment health checks: lint verification, type checking, test passes, and security vulnerability scans.
  * Performs database migration dry-runs and executes zero-downtime migration steps.
  * Deploys backend services, serverless workers, and Convex schemas.
  * Configures environment variables, secrets, and CORS origins.
  * Runs post-deployment smoke tests and monitors telemetry for error spikes or latency regressions.
  * Triggers automated rollbacks if canary health checks fail.
* **When to Use:**
  * Staging and production release phases.
* **Recommended Model:** **Claude 3.5 Sonnet** or **GPT-4o** (strict adherence to runbooks, shell command execution, and verification checklists).

---

## 4. Platform & Infrastructure Stack: Convex & Corex

### Convex: The Reactive Backend Foundation
Convex serves as the unified real-time backend platform for our agentic system:
1. **Schema Definition & Reactive Data:** Convex provides end-to-end TypeScript type safety with built-in reactive queries that update instantly when data mutates.
2. **Built-in Background Jobs:** Replaces heavy external Redis/Celery stacks with built-in scheduled functions and background actions.
3. **MCP Server Integration:** Each developer and agent workspace can spin up an MCP (Model Context Protocol) server directly connected to Convex, providing tools for live DB inspection, schema verification, and function execution.

### Corex: The Orchestration Harness
Corex is the central harness runtime bridging prompting, context management, and lifecycle events:
* **Context Budgeting:** Prevents prompt dilution by feeding each sub-agent only the minimal necessary context (via progressive disclosure).
* **Tool Calling & Guardrails:** Enforces typed JSON schemas for tool inputs and outputs.
* **Auditability:** Logs full agent reasoning trajectories, tool executions, and diffs for deterministic debugging.

---

## 5. Model Selection Strategy (Cognitive Affinity Routing)

Choosing the correct model for each specialized task maximizes performance while minimizing token latency and cost:

| Agent / Phase | Primary Model | Secondary / Fallback | Selection Rationale |
| :--- | :--- | :--- | :--- |
| **Corex Orchestrator (Planning / Thinking)** | **Claude 3.7 Sonnet (Thinking)** / **Claude Opus** | **o3 / o1** | Exceptional long-horizon reasoning, strategic planning, and structural decision-making. |
| **Domain Model (Schemas & GDPR)** | **Claude 3.7 Sonnet (Thinking)** | **Claude 3.5 Sonnet** | High precision in legal-technical compliance, data modeling, and entity relationships. |
| **Codebase Design (Migrations & Architecture)** | **Claude 3.5 Sonnet** | **GPT-4o** | Mastery of modern backend architecture, async queues, and refactoring patterns. |
| **Feature Researcher** | **Gemini 2.0 Pro / Flash** | **Claude 3.5 Sonnet** | Massive context window for scanning full repositories, API docs, and third-party specs. |
| **Feature Executor (Coding)** | **Claude 3.5 Sonnet** | **GPT-4o** | Fast, accurate, production-grade syntax generation and minimal hallucination. |
| **Edge Case Researcher (Adversarial)** | **Claude 3.7 Sonnet (Thinking)** | **o3-mini** | Uncovers subtle concurrency, network failure, and operational edge cases. |
| **Test Executor (Writing Tests)** | **Claude 3.5 Sonnet** | **GPT-4o** | High quality fixture creation and comprehensive assertions across E2E and unit suites. |
| **Code Review Researcher** | **Claude 3.7 Sonnet** | **Claude Opus** | Deep semantic code comprehension, spotting subtle anti-patterns and performance traps. |
| **Code Review Executor (GitHub Comments)** | **GPT-4o** | **Claude 3.5 Sonnet** | Crisp markdown generation, GitHub API integration, and structured issue creation. |
| **Deployment Agent** | **Claude 3.5 Sonnet** | **GPT-4o** | Strict obedience to deterministic release runbooks and automated verification. |

---

## 6. What We Must Learn While Coding Up the Agent Harness

When implementing this agentic AI harness in code, these are the core architectural engineering patterns you must master:

1. **Deterministic State Machine (The Agent Loop):**
   * Avoid infinite loops: Every agent interaction must have an explicit halting condition, maximum turn limit, and cost budget.
2. **Context Window Compaction & Handoffs:**
   * Do not pass the entire conversation history from Orchestrator to Sub-Agent. Instead, extract a clean **Task Handoff Artifact** containing only:
     - Goal & Acceptance Criteria
     - Relevant Schemas / Interfaces
     - Allowed Toolset
3. **Structured Tool Contracts (JSON Schema / Zod):**
   * All inter-agent communication and tool executions must validate inputs and outputs against strict schemas. A malformed tool call must trigger an automated retry with corrective feedback.
4. **Idempotency & Rollback Mechanisms:**
   * File edits, migrations, and deployments must be idempotent. If an Executor fails midway, the harness must be able to restore the workspace to the last clean git commit.
5. **Human-in-the-Loop (HITL) Checkpoints:**
   * Critical operations (database migration execution, production deployments, PR merges) must pause for human confirmation before firing.
