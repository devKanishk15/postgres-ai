# Enhancement: Structured Analysis Reports

To improve the clarity and actionable nature of the AI agent's findings, we have implemented a mandatory structured report template for all database health analyses.

## Objective
Provide a consistent, easy-to-scan, and data-driven report format for DBA-level diagnostics.

## Report Template

The agent is now instructed to follow this mandatory structure:

```markdown
# 🔍 Database Health Report: [Short Insightful Title]
*Report Status: [STABLE | WARNING | CRITICAL]*

### 📊 Quick Snapshot
- **Connections**: [OK / ALERT] — [Active / Max], trend [Stable / Rising / Falling]
- **Cache Efficiency**: [OK / ALERT] — Hit ratio [Value%], trend [Stable / Falling]
- **Disk I/O**: [OK / ALERT] — [IOPS / Latency], trend [Stable / High]
- **CPU / Load**: [OK / ALERT] — [CPU% / Load Avg], trend [Stable / High]
- **Transaction Age**: [OK / ALERT] — Oldest XID [Value], status [Safe / Risk]

### 🧠 Analysis (Scan & Correlate)
- **Findings**: [Key anomalies or deviations identified during SCAN]
- **Correlation**: [How metrics influence each other (e.g., higher CPU correlating with index scans)]

### 🛠️ Recommendations (Actionable)
- **[Action Title]**: `[SQL / CLI Command]`
  - *Rationale*: [Why this helps]

### 📝 Bottom Line
[One-line final diagnosis and immediate next step]
```

## Implementation Details
- **Location**: `chatbot/agent.py`
- **Logic**: Enforced via `SYSTEM_PROMPT` to ensure the LLM prioritizes structure and specific data points retrieved from tool calls.
- **Benefits**:
  - Consistent layout for monitoring.
  - Clear separation between observation (Snapshot), reasoning (Analysis), and action (Recommendations).
  - Immediate visibility into system status.
