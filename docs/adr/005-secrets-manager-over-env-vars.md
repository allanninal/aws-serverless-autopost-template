# ADR-005: Secrets Manager Over Lambda Environment Variables

## Status

Accepted

## Context

The system requires several sensitive credentials: Facebook API tokens, OpenAI API keys, and other third-party service secrets. We needed a secure way to provide these to Lambda functions.

Lambda environment variables are convenient but have security concerns. They appear in plaintext in CloudFormation templates, are visible in the Lambda console, and can leak into CloudWatch logs if the runtime prints the environment.

## Decision

Store all sensitive credentials in AWS Secrets Manager. Lambda functions retrieve secrets at invocation time using the Secrets Manager SDK, with results cached for the lifetime of the execution environment to minimize API calls.

## Consequences

**Pros:**
- Encryption at rest using AWS KMS with customer-managed or AWS-managed keys.
- IAM-scoped access ensures only authorized Lambdas can read specific secrets.
- Built-in audit trail via CloudTrail for all secret access events.
- Supports automatic rotation for credentials that need periodic refresh.
- Secrets never appear in CloudFormation templates, console, or logs.

**Cons:**
- Adds latency on cold starts when secrets must be fetched (mitigated by caching).
- Costs $0.40/secret/month plus $0.05 per 10,000 API calls.
- Requires additional IAM policy configuration for each Lambda.
- Adds a runtime dependency on Secrets Manager availability.
