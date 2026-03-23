# ADR-006: SQS Dead Letter Queue Over Lambda Destinations

## Status

Accepted

## Context

When a Lambda function fails, the failure event and its payload must be captured for debugging and potential replay. We evaluated two AWS-native options: Lambda Destinations and SQS Dead Letter Queues (DLQ).

Lambda Destinations only work for asynchronous invocations and do not capture all failure modes. Specifically, they miss timeouts and out-of-memory crashes where the runtime cannot execute the destination routing logic.

## Decision

Attach an SQS Dead Letter Queue to each Lambda function in the pipeline. Failed invocations are automatically routed to the DLQ after the configured retry count is exhausted.

The DLQ retention period is set to 14 days, providing ample time to investigate and replay failed events.

## Consequences

**Pros:**
- Captures ALL failure modes: unhandled exceptions, timeouts, and out-of-memory kills.
- Works regardless of invocation type (synchronous, asynchronous, event-source).
- 14-day message retention gives sufficient time to investigate failures.
- Failed messages can be replayed by moving them back to the source queue or re-invoking the Lambda.
- SQS is effectively free at low volume (first 1M requests/month free).

**Cons:**
- DLQ messages contain raw event payloads, not structured error details.
- Requires monitoring/alerting setup to know when messages land in the DLQ.
- No built-in mechanism for automatic replay; replay must be scripted.
