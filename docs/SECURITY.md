# Security

## Principles

This project follows AWS security best practices for serverless applications. The guiding principle is **least privilege**: every component only has access to the specific resources it needs.

## IAM Least-Privilege Permissions

Each Lambda function has a scoped-down IAM role. The CDK stack uses `grant_*` methods to assign only the required permissions:

| Lambda | Secrets Manager | S3 | DynamoDB | Lambda Invoke |
|---|---|---|---|---|
| **Post Scheduler** | None | None | Read/Write | Invoke 3 downstream functions |
| **Content Generator** | OpenRouter (read) | None | None | None |
| **Image Generator** | OpenAI + Unsplash (read) | Read/Write | None | None |
| **Facebook Poster** | Facebook (read) | Read only | Read/Write | None |

No function has admin access, wildcard permissions, or cross-service access beyond what is listed above.

## Secrets Management

All API keys and tokens are stored in **AWS Secrets Manager** -- never in environment variables, code, or config files.

- `facebook` -- Page Access Token and Page ID
- `openai` -- API key for DALL-E image generation
- `openrouter` -- API key for LLM content generation
- `unsplash` -- Access key for stock photo search

Secrets are referenced by ARN in Lambda environment variables. At runtime, each function fetches only its own secrets via the Secrets Manager API.

### Token Rotation

- **Facebook Page Token:** Long-lived tokens last ~60 days. Set a calendar reminder to rotate, or use the Facebook API to exchange for a new token before expiry.
- **OpenAI / OpenRouter / Unsplash:** These keys do not expire but should be rotated periodically. Generate a new key in the provider dashboard, update Secrets Manager, and revoke the old key.
- **Rotation process:** Update the secret value in the AWS Console or via CLI (`aws secretsmanager put-secret-value`). No redeployment needed -- Lambdas fetch secrets at runtime.

## S3 Bucket Security

- The image bucket is **not publicly accessible**. There is no bucket policy granting public read.
- Only the Image Generator (read/write) and Facebook Poster (read-only) have access.
- A **7-day lifecycle rule** automatically deletes old images, limiting the window of exposure for any stored data.
- `RemovalPolicy.DESTROY` with `auto_delete_objects=True` ensures the bucket is fully cleaned up if the stack is deleted.

## DynamoDB Encryption

- DynamoDB tables are **encrypted at rest by default** using AWS-managed keys (no additional configuration required).
- A **TTL attribute** automatically deletes old dedup records, minimizing stored data.

## Network Security

- No VPC is required. All external communication uses **HTTPS**:
  - OpenAI API (`api.openai.com`)
  - OpenRouter API (`openrouter.ai`)
  - Unsplash API (`api.unsplash.com`)
  - Facebook Graph API (`graph.facebook.com`)
  - AWS service endpoints (S3, DynamoDB, Secrets Manager, Lambda)
- No inbound ports are open. Lambda functions are invoked only by EventBridge and other Lambda functions.

## Source Code Protection

- `.gitignore` excludes `.env` files, virtual environments, and CDK build artifacts.
- No secrets, tokens, or credentials exist in the repository.
- The CDK stack uses placeholder values (`YOUR_PROJECT_NAME`, `YOUR_EMAIL@example.com`) that must be replaced before deployment.
