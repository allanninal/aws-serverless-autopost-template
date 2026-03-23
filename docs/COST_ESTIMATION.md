# Cost Estimation

## Monthly AWS Cost Breakdown (3 posts/day)

| Service | Usage | Monthly Cost |
|---|---|---|
| **Lambda** | 12 invocations/day, ~3s avg duration, 256-512 MB | ~$0.00 (free tier) |
| **EventBridge** | 3 cron rules, 90 invocations/month | ~$0.00 (free tier) |
| **DynamoDB** | ~90 writes + 90 reads/month, on-demand billing | ~$0.00 (free tier) |
| **S3** | ~90 images/month, 7-day lifecycle auto-delete | ~$0.01 |
| **Secrets Manager** | 4 secrets (Facebook, OpenAI, OpenRouter, Unsplash) | ~$1.60 |
| **CloudWatch** | 1 dashboard + 5 alarms + logs | ~$1.00 |
| **SQS** (DLQ) | Minimal usage (only on failures) | ~$0.00 |
| **SNS** | Email notifications on alarm | ~$0.00 |
| **AWS subtotal** | | **~$2.61** |

## External API Costs

| Service | Usage | Monthly Cost |
|---|---|---|
| **OpenAI API** (DALL-E image generation) | ~90 images/month | ~$3-10 |
| **LLM API** (OpenRouter for content generation) | ~90 completions/month | ~$1-5 |
| **Unsplash** (stock photos, if used instead of DALL-E) | Free tier: 50 req/hr | $0.00 |

## Total Monthly Cost

| Component | Cost |
|---|---|
| AWS infrastructure | ~$3 |
| OpenAI API | ~$3-10 |
| LLM API (OpenRouter) | ~$1-5 |
| **Grand total** | **~$7-18/month** |

## Comparison with SaaS Alternatives

| Solution | Monthly Cost | Limitations |
|---|---|---|
| **This project** | $7-18 | Full control, AI-generated content + images |
| Buffer | $15+ | No AI content generation, no custom images |
| Make.com | $29+ | Limited AI integrations, per-operation pricing |
| Zapier | $49+ | Expensive at scale, limited image generation |
| Hootsuite | $99+ | Enterprise pricing, no AI image generation |

This project provides AI-generated content **and** images at a fraction of the cost of SaaS tools, with full customization control.

## Scaling Estimates

| Posts/day | Lambda | S3 | Secrets Manager | CloudWatch | OpenAI | LLM | **Total** |
|---|---|---|---|---|---|---|---|
| 3 | $0.00 | $0.01 | $1.60 | $1.00 | $3-10 | $1-5 | **$7-18** |
| 5 | $0.00 | $0.02 | $1.60 | $1.00 | $5-17 | $2-8 | **$10-28** |
| 10 | $0.00 | $0.03 | $1.60 | $1.00 | $10-33 | $3-17 | **$16-53** |
| 20 | $0.00 | $0.06 | $1.60 | $1.00 | $20-67 | $7-33 | **$30-103** |

**Note:** Lambda remains within the free tier even at 20 posts/day (~2,400 invocations/month). The primary cost driver at scale is OpenAI image generation. You can reduce this by using Unsplash stock photos for some post types (free) or by using a cheaper image model.

## Cost Optimization Tips

- **Use Unsplash for some post types.** Stock photos are free and work well for generic content. Reserve AI-generated images for posts that need unique visuals.
- **Choose smaller LLM models.** OpenRouter lets you pick cost-efficient models. A $0.10/M-token model costs a fraction of GPT-4.
- **S3 lifecycle is already optimized.** The 7-day auto-delete rule keeps storage costs near zero.
- **DynamoDB TTL cleans up old records.** No manual maintenance needed.
