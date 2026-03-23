# ADR-002: EventBridge Over Step Functions for Scheduling

## Status

Accepted

## Context

Posts need to be scheduled at specific times throughout the day. We evaluated three options: Step Functions Wait states, CloudWatch Events rules, and EventBridge Scheduler rules.

Step Functions Wait states would keep a state machine execution running (and billable) while waiting. CloudWatch Events works but is being superseded by EventBridge. EventBridge provides a modern, cost-effective scheduling mechanism.

## Decision

Use Amazon EventBridge cron rules for scheduling post execution. Each scheduled post gets its own EventBridge rule that triggers the orchestrator Lambda at the designated time.

Rules are created programmatically when the schedule is configured and cleaned up after execution or expiration.

## Consequences

**Pros:**
- First 14 million events per month are free, making this effectively zero-cost at our volume.
- One rule per post provides clean separation of scheduling from execution logic.
- No long-running executions consuming resources while waiting.
- EventBridge is the AWS-recommended path forward over CloudWatch Events.
- Rules can be enabled/disabled independently without affecting other schedules.

**Cons:**
- Minimum scheduling granularity is one minute.
- Managing many individual rules requires cleanup discipline to avoid rule sprawl.
- No built-in dependency chain between scheduled posts; each fires independently.
