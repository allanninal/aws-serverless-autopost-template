# ADR-001: Lambda Orchestrator Pattern

## Status

Accepted

## Context

The posting pipeline follows a strict linear sequence: generate content, generate image, post to Facebook. We needed to decide between AWS Step Functions and a single orchestrator Lambda that chains these steps via direct invocation.

Step Functions adds a managed state machine with built-in retry and error handling, but charges per state transition ($0.025 per 1,000 transitions). For a simple linear pipeline that runs a few times per day, this overhead is unnecessary.

## Decision

Use a single orchestrator Lambda that invokes content-generator, image-generator, and poster Lambdas sequentially via boto3 `lambda.invoke()`.

The orchestrator controls the flow with straightforward Python try/except blocks. Each downstream Lambda returns its result synchronously, and the orchestrator passes outputs from one step as inputs to the next.

## Consequences

**Pros:**
- Simpler architecture with fewer moving parts.
- No per-transition cost; only Lambda execution time is billed.
- Easier to debug locally since the logic is plain Python.
- Full control over retry logic and error handling in code.

**Cons:**
- Subject to Lambda's 15-minute maximum timeout for the entire pipeline.
- No built-in visual execution history like Step Functions provides.
- Retry and error-handling logic must be implemented manually.
- If the pipeline grows beyond 3-4 steps or adds branching, Step Functions would be more appropriate.
