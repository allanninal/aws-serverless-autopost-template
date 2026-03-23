# Architecture

## Overview

This project uses a **4-Lambda orchestrator pattern** to automate Facebook image posts. An EventBridge cron rule triggers the Post Scheduler, which synchronously invokes three downstream Lambdas in sequence:

```
EventBridge Cron
    |
    v
Post Scheduler (orchestrator)
    |
    +--> 1. Content Generator   (LLM -> caption + image prompt)
    |
    +--> 2. Image Generator     (OpenAI DALL-E / Unsplash + Pillow overlay -> S3)
    |
    +--> 3. Facebook Poster     (Graph API upload + DynamoDB dedup record)
```

## Why 4 Separate Functions?

A monolithic Lambda could do all of this in one function. Splitting into four provides concrete benefits:

- **Independent deployability.** Change a prompt template without redeploying the image pipeline. Update the Facebook client without touching content generation.
- **Granular IAM permissions.** The Content Generator only accesses OpenRouter secrets. The Image Generator only accesses OpenAI/Unsplash secrets and the S3 bucket. The Facebook Poster only accesses the Facebook secret, S3 (read-only), and DynamoDB. No function has more access than it needs.
- **Targeted debugging.** CloudWatch logs are separated per function. When image generation fails, you look at one log group -- not a 500-line monolith log.
- **Independent scaling and memory tuning.** The Image Generator needs 512 MB for Pillow operations. The Content Generator and Facebook Poster only need 256 MB. A monolith would require the highest memory setting for every invocation.
- **Failure isolation.** If the Facebook API is down, the Content Generator and Image Generator still succeed. On retry, only the Facebook Poster runs again (via the DynamoDB idempotency check).

## How the Orchestrator Pattern Works

The Post Scheduler acts as a lightweight orchestrator:

1. **EventBridge** fires a cron rule with `{post_number, post_type}` in the event payload.
2. The **Post Scheduler** checks DynamoDB for an existing `post_key` (date + post number + type). If found, it short-circuits (idempotency guard).
3. It invokes the **Content Generator** synchronously (`RequestResponse`), receiving a caption, image text, and image prompt.
4. It invokes the **Image Generator** with the content output. The image is saved to S3 and the S3 key is returned.
5. It invokes the **Facebook Poster** with the caption and S3 key. The poster uploads via Graph API and writes a DynamoDB record to prevent duplicate posts.
6. If any step fails, the Lambda error propagates to the **SQS Dead Letter Queue**, and a **CloudWatch alarm** triggers an email via SNS.

## Comparison with Alternatives

| Approach | Pros | Cons |
|---|---|---|
| **4-Lambda orchestrator** (this project) | Simple, cheap, easy to debug, fine-grained IAM | Manual retry logic, sequential execution |
| **Step Functions** | Built-in retry/catch, parallel branches, visual workflow | Higher cost ($25/million transitions), more infrastructure to manage |
| **Single Lambda** | Fewest moving parts, simplest deployment | Hardest to debug, coarse IAM, wasteful memory allocation, tight coupling |
| **ECS / Fargate** | Full container flexibility, long-running tasks | Overkill for 3-second batch jobs, higher baseline cost, more ops overhead |

The orchestrator pattern hits the sweet spot: it is almost free at low volume, keeps each concern isolated, and avoids the operational complexity of Step Functions or containers.

## Scaling Characteristics

| Daily posts | EventBridge rules | Lambda invocations/day | Estimated Lambda cost/month |
|---|---|---|---|
| 3 | 3 | 12 (3 x 4 functions) | $0.00 (free tier) |
| 10 | 10 | 40 | $0.00 (free tier) |
| 20 | 20 | 80 | $0.00 (free tier) |
| 50 | 50 | 200 | ~$0.01 |

Lambda free tier includes 1 million requests and 400,000 GB-seconds per month. Even at 50 posts/day, you use roughly 6,000 invocations/month -- well within the free tier. The real cost driver at scale is the OpenAI image generation API, not AWS infrastructure.

## Failure Isolation in Practice

Each Lambda failing has a limited blast radius:

- **Content Generator fails:** No image is generated, no post is published. Retry produces the same result since no side effects occurred.
- **Image Generator fails:** Content was generated but discarded (stateless). Retry regenerates content and tries image generation again.
- **Facebook Poster fails:** The image exists in S3 but no post was published. The DynamoDB record was not written, so a retry will attempt to post again.
- **Post Scheduler fails:** The DLQ captures the event. The next scheduled run will succeed if the issue was transient (the idempotency check prevents double-posting).

This isolation means transient failures in one API (Facebook, OpenAI, etc.) do not corrupt state in other parts of the pipeline.
