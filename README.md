![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![AWS CDK](https://img.shields.io/badge/AWS_CDK-v2-FF9900?logo=amazonaws&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Serverless](https://img.shields.io/badge/Serverless-100%25-FD5750?logo=serverless&logoColor=white)
![Facebook API](https://img.shields.io/badge/Facebook_Graph_API-v23.0-1877F2?logo=facebook&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white)
![IaC](https://img.shields.io/badge/IaC-AWS_CDK-FF9900)

# AWS Serverless Autopost Template

**Production-ready serverless template for automated Facebook image posting.**
Fork it. Configure your content. Deploy with one command. Walk away.

Built with **EventBridge + Lambda + DynamoDB + S3 + CDK** — fully Infrastructure as Code, zero servers to manage.

> Powering real Facebook pages: posts multiple times daily with zero manual intervention.

---

## Architecture

```
                         SERVERLESS FACEBOOK AUTOPOST PIPELINE
                         ======================================

    ┌──────────────────────────────────────────────────────────────────────────┐
    │                              AWS CLOUD                                   │
    │                                                                          │
    │   ┌─────────────┐     ┌──────────────┐     ┌──────────────┐             │
    │   │ EventBridge  │────▶│    Post       │────▶│   Content    │             │
    │   │  (N cron     │     │  Scheduler   │     │  Generator   │             │
    │   │   rules)     │     │  [Lambda]    │     │  [Lambda]    │             │
    │   └─────────────┘     └──────┬───────┘     └──────┬───────┘             │
    │                              │                     │                      │
    │                              │              ┌──────▼───────┐             │
    │                              │              │    Image      │             │
    │                              │              │  Generator    │             │
    │                              │              │  [Lambda]     │             │
    │                              │              └──────┬───────┘             │
    │                              │                     │                      │
    │                              │              ┌──────▼───────┐             │
    │                              └─────────────▶│   Facebook   │             │
    │                                             │    Poster    │             │
    │                                             │  [Lambda]    │             │
    │                                             └──────┬───────┘             │
    │                                                    │                      │
    │   ┌──────────┐  ┌──────────┐  ┌───────┐          │                      │
    │   │ DynamoDB  │  │    S3    │  │  SQS  │          │                      │
    │   │  (dedup)  │  │ (images) │  │ (DLQ) │          │                      │
    │   └──────────┘  └──────────┘  └───┬───┘          │                      │
    │                                   │               │                      │
    │                              ┌────▼────┐          │                      │
    │                              │   SNS   │          │                      │
    │                              │ (alerts)│          │                      │
    │                              └─────────┘          │                      │
    └───────────────────────────────────────────────────┼──────────────────────┘
                                                        │
                                                        ▼
                                              ┌──────────────────┐
                                              │   Facebook Page   │
                                              │  (Graph API v23)  │
                                              └──────────────────┘
```

---

## How It Works

Each scheduled post follows this pipeline:

```
    ╔══════════════╗
    ║  EventBridge  ║  cron(30 21 * * ? *)  ──  "Post #1 at 5:30 AM local"
    ╚══════╦═══════╝
           ║  { post_number: 1, post_type: "your-type" }
           ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                      POST SCHEDULER                         │
    │                                                             │
    │  1. DynamoDB dedup ─── Already posted? ─── YES ──▶ EXIT    │
    │  2. Invoke content_generator (sync)                         │
    │  3. Invoke image_generator (sync)                           │
    │  4. Invoke facebook_poster (sync)                           │
    └──────────┬──────────────────────────────────────────────────┘
               │
     ┌─────────┼──────────────────────┐
     ▼         ▼                      ▼
┌─────────┐ ┌──────────┐      ┌────────────┐
│ CONTENT │ │  IMAGE   │      │  FACEBOOK  │
│   GEN   │ │   GEN    │      │   POSTER   │
│         │ │          │      │            │
│ LLM API │ │ OpenAI / │      │ Graph API  │
│ call x3 │ │ Unsplash │      │   v23.0    │
│    ↓    │ │    ↓     │      │     ↓      │
│ caption │ │ Pillow   │      │  Upload    │
│ + image │ │ overlay  │      │  photo +   │
│  prompt │ │    ↓     │      │  caption   │
│         │ │ S3 upload│      │     ↓      │
└─────────┘ └──────────┘      │ DynamoDB   │
                              │  record    │
                              └────────────┘
```

---

## AWS Infrastructure

All resources are defined in CDK (Python) and deployed with a single command.

```
    ┌─────────────────────────────────────────────────────────────────────┐
    │                        AWS Account                                  │
    │                                                                     │
    │  ┌─── Compute ───────┐  ┌─── Storage ────────┐  ┌── Security ──┐  │
    │  │ Lambda x4          │  │ S3 (images)        │  │ Secrets Mgr  │  │
    │  │ - scheduler 256MB  │  │ - 7d lifecycle     │  │ - FB token   │  │
    │  │ - content   256MB  │  │                    │  │ - OpenAI key │  │
    │  │ - image     512MB  │  │ DynamoDB           │  │ - LLM key    │  │
    │  │ - poster    256MB  │  │ - PAY_PER_REQUEST  │  │ - Unsplash   │  │
    │  │ Python 3.11        │  │ - TTL 90d          │  │              │  │
    │  └────────────────────┘  └────────────────────┘  └──────────────┘  │
    │                                                                     │
    │  ┌─── Scheduling ────┐  ┌── Observability ───┐  ┌── Resilience ─┐ │
    │  │ EventBridge        │  │ CloudWatch         │  │ SQS DLQ       │ │
    │  │ - N cron rules     │  │ - Dashboard        │  │ - 14d retain  │ │
    │  │ - UTC expressions  │  │ - Alarms x5        │  │               │ │
    │  │                    │  │ SNS Topic           │  │               │ │
    │  │                    │  │ - Email alerts      │  │               │ │
    │  └────────────────────┘  └────────────────────┘  └───────────────┘ │
    └─────────────────────────────────────────────────────────────────────┘
```

| Resource | Purpose | Config |
|----------|---------|--------|
| **EventBridge** | Cron triggers | N rules, UTC times |
| **Lambda x4** | Pipeline stages | Python 3.11, 256-512 MB |
| **DynamoDB** | Dedup tracking | PAY_PER_REQUEST, TTL |
| **S3** | Image storage | 7-day auto-delete |
| **SQS** | Dead letter queue | 14-day retention |
| **SNS** | Failure alerts | Email subscription |
| **CloudWatch** | Dashboard + alarms | Per-Lambda metrics |
| **Secrets Manager** | API keys | Facebook, OpenAI, LLM, Unsplash |

---

## Error Handling

```
    Lambda Invocation
         │
         ├── SUCCESS ──▶ DynamoDB record ──▶ Done
         │
         └── FAILURE
              │
              ├── Facebook retry (exponential backoff: 10s, 20s, 40s)
              │    ├── Rate limit (codes 4,17,32,613) ── retryable
              │    ├── Token expired (code 190) ── fatal, alert
              │    └── Duplicate (code 506) ── skip
              │
              └── All retries exhausted
                   │
              ┌────▼─────┐    ┌─────────────┐    ┌──────────┐
              │  SQS DLQ │───▶│  CloudWatch  │───▶│   SNS    │
              │  14-day  │    │   Alarm      │    │  Email   │
              │ retention│    │  (>= 1 msg)  │    │  Alert   │
              └──────────┘    └─────────────┘    └──────────┘
```

---

## Image Generation

Two sources, one overlay pipeline:

```
    ┌─────────────────────────────────────────────────────────────┐
    │                    IMAGE GENERATION                          │
    │                                                             │
    │   Content-driven prompt                                     │
    │          │                                                  │
    │          ▼                                                  │
    │   ┌──────────────┐       ┌──────────────┐                  │
    │   │   OpenAI      │  OR   │   Unsplash   │                  │
    │   │  gpt-image-1  │       │  Stock API   │                  │
    │   │  (AI gen)     │       │  (free tier) │                  │
    │   └──────┬───────┘       └──────┬───────┘                  │
    │          │                      │                           │
    │          └──────────┬───────────┘                           │
    │                     ▼                                       │
    │          ┌──────────────────┐                               │
    │          │   Pillow Overlay  │                               │
    │          │                  │                               │
    │          │  Style A: Panel  │  Style B: Gradient            │
    │          │  1080x1080 (1:1) │  1080x1350 (4:5)             │
    │          │  Dark text panel │  Fade-to-black                │
    │          │  + headline      │  + text on gradient           │
    │          └────────┬─────────┘                               │
    │                   ▼                                         │
    │          ┌──────────────────┐                               │
    │          │    S3 Upload      │                               │
    │          │  images/{date}/   │                               │
    │          │  7-day lifecycle  │                               │
    │          └──────────────────┘                               │
    └─────────────────────────────────────────────────────────────┘
```

---

## Cost Estimate

| Service | Monthly Cost | Notes |
|---------|-------------|-------|
| Lambda | ~$0.00 | Within free tier |
| EventBridge | ~$0.00 | Free tier |
| DynamoDB | ~$0.00 | On-demand, minimal |
| S3 | ~$0.01 | 7-day lifecycle |
| Secrets Manager | ~$2.00 | $0.40/secret x 4-5 |
| CloudWatch | ~$1.00 | Dashboard + alarms |
| **Total AWS** | **~$3/month** | |
| OpenAI API | ~$3-10/month | Image generation |
| LLM API | ~$1-5/month | Content generation |
| **Grand Total** | **~$7-18/month** | **vs Zapier $49/mo** |

See [docs/COST_ESTIMATION.md](docs/COST_ESTIMATION.md) for detailed breakdown by post volume.

---

## Features

- **Fully serverless** — no servers, no containers, no cron jobs to manage
- **Infrastructure as Code** — entire stack defined in CDK (Python), deploy with one command
- **Dual image sources** — AI-generated (OpenAI gpt-image-1) or stock photos (Unsplash)
- **Two overlay styles** — 1:1 square panel or 4:5 portrait gradient
- **Idempotent** — DynamoDB dedup prevents double-posting on retries
- **Production error handling** — exponential backoff, DLQ, SNS alerts
- **Cost optimized** — ~$7-18/month for a fully automated page
- **CI/CD ready** — GitHub Actions for lint, test, security scan, and deploy
- **Fully tested** — pytest suite with moto AWS mocks
- **Customizable** — swap prompts, image styles, and schedule in config files

---

## Quick Start

> **First time?** See the [full step-by-step Setup Guide](docs/SETUP_GUIDE.md) -- it covers installing tools, getting API keys, and deploying from scratch with detailed explanations.

### Prerequisites

| Tool | What it's for | Install |
|------|--------------|---------|
| **Python 3.11+** | Lambda code & tests | [python.org/downloads](https://www.python.org/downloads/) or `brew install python@3.11` |
| **Node.js 18+** | AWS CDK CLI | [nodejs.org](https://nodejs.org/) or `brew install node` |
| **AWS CLI** | AWS access from terminal | [AWS CLI install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| **AWS CDK** | Deploy infrastructure | `npm install -g aws-cdk` |

### API Keys You'll Need

| Service | What it does | Where to get it |
|---------|-------------|-----------------|
| **Facebook Page Token** | Posts to your Page | [developers.facebook.com](https://developers.facebook.com) -> Graph API Explorer ([detailed steps](docs/SETUP_GUIDE.md#facebook-page-access-token-required)) |
| **OpenAI API Key** | Generates images (DALL-E) | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| **OpenRouter API Key** | Generates text content | [openrouter.ai/keys](https://openrouter.ai/keys) |
| **Unsplash Access Key** | Free stock photos (optional) | [unsplash.com/developers](https://unsplash.com/developers) |

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/aws-serverless-autopost-template.git
cd aws-serverless-autopost-template
pip install -r requirements-dev.txt
cd infra && pip install -r requirements.txt && cd ..

# Verify: should show "34 passed"
make test
```

### 2. Configure

```bash
cp .env.example .env
```

Open `.env` in any text editor and replace all `YOUR_*` values with your actual API keys and settings. See [Setup Guide Step 4](docs/SETUP_GUIDE.md#4-configure-your-project) for a filled-in example.

### 3. Store secrets in AWS

API keys are stored securely in AWS Secrets Manager (never in code):

```bash
bash scripts/setup_secrets.sh --profile your-aws-profile
```

The script prompts for each secret in JSON format. Example:
```
Enter value: {"page_access_token":"EAAxxxxxxx"}
Enter value: {"api_key":"sk-xxxx"}
```

Or create them manually in the [AWS Console](https://console.aws.amazon.com/secretsmanager/). See [Setup Guide Step 5](docs/SETUP_GUIDE.md#5-store-your-secrets-in-aws) for detailed instructions.

### 4. Customize your content

Edit these files (start with prompts -- that's where your brand voice lives):

| Order | File | What to change |
|-------|------|---------------|
| 1 | `lambda/content_generator/prompts.py` | **Your brand voice, audience, topics** |
| 2 | `lambda/post_scheduler/config.py` | Post schedule and image source per post |
| 3 | `lambda/image_generator/image_prompts.py` | Image art styles and themes |
| 4 | `infra/stacks/autopost_stack.py` | Project name, email, timezone, cron rules |

See [Customization Guide](docs/CUSTOMIZATION_GUIDE.md) for 3 worked examples (motivational quotes, local business, data-driven content).

### 5. Test locally, then deploy

```bash
# Preview a sample image (no API keys needed)
python scripts/generate_sample.py

# Test with real APIs (generates content + image, doesn't post)
python scripts/test_post_local.py --post-number 1

# Deploy to AWS (one command -- creates all infrastructure)
cd infra && cdk deploy --profile your-aws-profile
```

After deploying, check your email for an **SNS subscription confirmation** -- click "Confirm" to receive error alerts.

---

## Make It Yours

| File | What to change |
|------|---------------|
| `lambda/content_generator/prompts.py` | **Your brand voice, audience, and content topics** |
| `lambda/image_generator/image_prompts.py` | Your image art styles and visual themes |
| `lambda/post_scheduler/config.py` | Your posting schedule and image source per post |
| `infra/stacks/autopost_stack.py` | Project name, region, alarm email, cron times |
| `.env.example` | Your API keys and configuration |

See [docs/CUSTOMIZATION_GUIDE.md](docs/CUSTOMIZATION_GUIDE.md) for 3 example use cases:
1. Daily motivational quotes page
2. Local business promotions
3. News/data-driven content

---

## CI/CD Pipeline

```
    Developer              GitHub Actions            AWS
       │                        │                     │
       │  git push / PR         │                     │
       │───────────────────────▶│                     │
       │                   ┌────┤ ci.yml              │
       │                   │    │ 1. ruff lint        │
       │                   │    │ 2. pytest           │
       │                   │    │ 3. bandit scan      │
       │                   └────┤                     │
       │                        │                     │
       │  merge to main         │                     │
       │───────────────────────▶│                     │
       │                   ┌────┤ deploy.yml          │
       │                   │    │ 1. cdk synth        │
       │                   │    │ 2. cdk diff         │
       │                   │    │ 3. cdk deploy ─────▶│ CloudFormation
       │                   └────┤                     │ creates all
       │                        │                     │ resources
```

---

## Project Structure

```
aws-serverless-autopost-template/
├── infra/                          # CDK infrastructure (Python)
│   ├── app.py                      # CDK app entry point
│   └── stacks/
│       └── autopost_stack.py       # All AWS resources defined here
├── lambda/
│   ├── post_scheduler/             # Orchestrator Lambda
│   │   ├── handler.py              # EventBridge -> dedup -> chain Lambdas
│   │   └── config.py               # <-- YOUR SCHEDULE HERE
│   ├── content_generator/          # AI content pipeline
│   │   ├── handler.py              # 3 LLM calls: caption + headline + image prompt
│   │   └── prompts.py              # <-- YOUR CONTENT HERE
│   ├── image_generator/            # AI image + overlay
│   │   ├── handler.py              # OpenAI / Unsplash + Pillow overlay
│   │   ├── image_prompts.py        # <-- YOUR STYLES HERE
│   │   ├── overlay.py              # Panel (1:1) and gradient (4:5) styles
│   │   └── unsplash_client.py      # Stock photo client with API compliance
│   └── facebook_poster/            # Graph API publisher
│       ├── handler.py              # S3 download -> Facebook upload -> DynamoDB
│       └── facebook_client.py      # Retry with exponential backoff
├── tests/                          # pytest suite with moto AWS mocks
├── scripts/
│   ├── generate_sample.py          # Preview images locally (no API keys)
│   ├── test_post_local.py          # End-to-end test with real APIs
│   └── setup_secrets.sh            # Create AWS Secrets Manager entries
├── docs/
│   ├── SETUP_GUIDE.md              # Step-by-step setup for beginners
│   ├── ARCHITECTURE.md             # Deep dive on the 4-Lambda pattern
│   ├── COST_ESTIMATION.md          # Detailed monthly breakdown
│   ├── CUSTOMIZATION_GUIDE.md      # 3 example use cases
│   ├── SECURITY.md                 # IAM, secrets, access controls
│   └── adr/                        # Architecture Decision Records
├── .github/workflows/
│   ├── ci.yml                      # Lint + test + security on PR
│   └── deploy.yml                  # CDK deploy on merge to main
├── .env.example                    # Configuration template
├── Makefile                        # Common operations
└── README.md                       # You are here
```

---

## Engineering Decisions

| Decision | Why |
|----------|-----|
| **4 separate Lambdas** (not 1 monolith) | Independent scaling, isolated failures, granular IAM, targeted debugging |
| **Orchestrator pattern** (not Step Functions) | Simpler and cheaper for linear pipelines — no state machine overhead |
| **DynamoDB for dedup** | PAY_PER_REQUEST + TTL = near-zero cost, automatic cleanup |
| **S3 with 7-day lifecycle** | Images only needed for Facebook upload, then disposable |
| **SQS DLQ + SNS alerts** | Know immediately when posts fail, inspect payloads later |
| **Secrets Manager** (not env vars) | Encrypted at rest, rotate without redeploy, IAM-scoped |
| **CDK** (not SAM/Terraform) | Python-native IaC, type-safe, same language as Lambdas |
| **Pillow overlay** (not AI text) | Pixel-perfect typography — AI text in images is unreliable |
| **Local bundler** (not Docker) | 10x faster deploys, no Docker dependency for CI |

See [docs/adr/](docs/adr/) for detailed Architecture Decision Records.

---

## Testing

```bash
# Run full test suite
make test

# Lint
make lint

# Security scan
make security-scan

# Generate sample image locally (no API keys needed)
make sample

# End-to-end test with real APIs
python scripts/test_post_local.py --post-number 1

# With Facebook posting
python scripts/test_post_local.py --post-number 1 --post
```

---

## Live Examples

Pages powered by this architecture (different content, same pipeline):

- **Cebu Weather with Feelings** — 5 posts/day, weather updates + Filipino "hugot" lines
- **Daily Catholic Companion** — 13 posts/day, daily devotionals and prayers

Running 24/7 with zero manual intervention.

---

## Contributing

Contributions welcome. Please open an issue first to discuss changes.

1. Fork the repo
2. Create a feature branch
3. Add tests for new functionality
4. Submit a PR

---

## License

MIT — use it however you want. See [LICENSE](LICENSE).

---

## Author

**Allan Ninal** — AWS & DevOps Engineer | Automation Specialist

Building production serverless systems that run themselves.
