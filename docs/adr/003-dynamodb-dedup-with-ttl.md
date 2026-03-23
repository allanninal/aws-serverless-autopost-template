# ADR-003: DynamoDB for Deduplication with TTL

## Status

Accepted

## Context

The system must avoid posting duplicate content when retries or overlapping schedules cause the same post to be triggered more than once. We considered in-memory tracking, S3 marker files, and DynamoDB.

In-memory state is lost between Lambda invocations. S3 marker files work but have eventual consistency concerns and require manual cleanup. DynamoDB provides atomic conditional writes ideal for deduplication.

## Decision

Use a DynamoDB table for deduplication with the following design:

- **Composite primary key:** `date-number-type` (e.g., `2026-03-24-1-motivational`).
- **TTL attribute:** Set to 90 days after creation for automatic cleanup.
- **Billing mode:** PAY_PER_REQUEST (on-demand) to avoid provisioning capacity.

Before posting, the orchestrator performs a conditional `PutItem` that fails if the key already exists, preventing duplicate posts atomically.

## Consequences

**Pros:**
- Atomic conditional writes guarantee exactly-once deduplication.
- TTL handles cleanup automatically with no cron jobs or maintenance.
- PAY_PER_REQUEST billing means near-zero cost at low volume (a few requests/day).
- Survives Lambda cold starts and concurrent executions.

**Cons:**
- TTL deletion is not instant; items may persist up to 48 hours past expiry.
- Adds a DynamoDB dependency to the critical path of every post.
- Requires IAM permissions for the orchestrator Lambda to access the table.
