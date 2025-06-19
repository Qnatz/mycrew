### Workflow Hierarchy and Data Flow

1.  **Main Workflow (TaskMaster & Orchestrators)**
    → 2. **Crew Agents & Lead Agents Workflow**
    → 3. **Lead Agents & Subagents Workflow**
    → 4. **Execution Layer (Error Handling, Final Assembler, Code Writer)**

### Key Components in the Hierarchy:

1.  **TaskMaster & Orchestrators**:
    *   Top-level workflow management
    *   Initial requirements processing
    *   Overall pipeline coordination

2.  **Crew Agents & Lead Agents**:
    *   Domain-specific planning (backend, web, mobile, DevOps)
    *   Task decomposition based on architecture
    *   Resource allocation

3.  **Lead Agents & Subagents**:
    *   Specialized implementation work
    *   API development, UI implementation, database design, etc.
    *   Quality assurance at component level

4.  **Execution Layer**:
    *   **Error Handler**: Validates component readiness
    *   **Final Assembler**: Creates integration plan
    *   **Code Writer**: Generates final integrated codebase

### Data Flow Through the System:

1.  User request → TaskMaster → Project brief
2.  Project brief → Idea-to-Architecture → Architecture doc
3.  Architecture doc → Crew Leads → Implementation plans
4.  Implementation plans → Subagents → Component implementations
5.  Components → Error Handler → Validation report
6.  Validated components → Final Assembler → Integration plan
7.  Integration plan → Code Writer → Final codebase

This structure maintains clear separation of concerns while ensuring seamless data flow between layers. Each workflow can be developed, tested, and scaled independently while fitting into the overall pipeline.
