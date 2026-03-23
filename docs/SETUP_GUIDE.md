# Setup Guide (Step-by-Step)

This guide walks you through setting up the autopost template from scratch. No prior AWS or serverless experience is required -- just follow each step in order.

**Estimated time:** 45-60 minutes for first-time setup.

---

## Table of Contents

1. [Install Required Tools](#1-install-required-tools)
2. [Get Your API Keys](#2-get-your-api-keys)
3. [Clone and Install the Project](#3-clone-and-install-the-project)
4. [Configure Your Project](#4-configure-your-project)
5. [Store Your Secrets in AWS](#5-store-your-secrets-in-aws)
6. [Customize Your Content](#6-customize-your-content)
7. [Test Locally](#7-test-locally)
8. [Deploy to AWS](#8-deploy-to-aws)
9. [Verify It Works](#9-verify-it-works)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Install Required Tools

You need 4 tools installed on your computer. If you already have any of these, skip to the next one.

### Python 3.11+

Python is the programming language this project uses.

**Check if you have it:**
```bash
python3 --version
# Should show Python 3.11 or higher
```

**Install if missing:**
- **Mac:** `brew install python@3.11` (install [Homebrew](https://brew.sh) first if you don't have it)
- **Windows:** Download from [python.org/downloads](https://www.python.org/downloads/) -- check "Add Python to PATH" during install
- **Linux:** `sudo apt install python3.11 python3.11-venv` (Ubuntu/Debian)

### Node.js (for AWS CDK CLI)

Node.js is needed to run the AWS CDK command-line tool.

**Check if you have it:**
```bash
node --version
# Should show v18 or higher
```

**Install if missing:**
- Download from [nodejs.org](https://nodejs.org/) (choose the LTS version)
- Or Mac: `brew install node`

### AWS CLI

The AWS Command Line Interface lets you interact with your AWS account from the terminal.

**Check if you have it:**
```bash
aws --version
# Should show aws-cli/2.x.x
```

**Install if missing:**
- Follow the official guide: [docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- Or Mac: `brew install awscli`

**Configure it (one-time setup):**
```bash
aws configure
# It will ask for:
#   AWS Access Key ID:     (from your AWS account, see below)
#   AWS Secret Access Key: (from your AWS account, see below)
#   Default region name:   ap-southeast-1  (or your preferred region)
#   Default output format: json
```

> **Where to get AWS credentials:**
> 1. Log in to [console.aws.amazon.com](https://console.aws.amazon.com)
> 2. Click your username (top right) -> "Security credentials"
> 3. Under "Access keys", click "Create access key"
> 4. Copy the Access Key ID and Secret Access Key
>
> **If you don't have an AWS account yet:**
> 1. Go to [aws.amazon.com](https://aws.amazon.com) and click "Create an AWS Account"
> 2. You'll need a credit card, but the free tier covers almost all costs for this project
> 3. First 12 months include generous free tier for Lambda, DynamoDB, S3, etc.

### AWS CDK CLI

CDK (Cloud Development Kit) is the tool that deploys your infrastructure to AWS.

**Install it:**
```bash
npm install -g aws-cdk
```

**Verify:**
```bash
cdk --version
# Should show 2.x.x
```

---

## 2. Get Your API Keys

You need API keys from 3-4 services. This is the most time-consuming part of setup.

### Facebook Page Access Token (required)

This lets the app post to your Facebook Page.

1. **Create a Facebook Page** (if you don't have one):
   - Go to [facebook.com/pages/create](https://www.facebook.com/pages/create)
   - Choose a category and fill in the details

2. **Create a Facebook Developer App:**
   - Go to [developers.facebook.com](https://developers.facebook.com)
   - Click "My Apps" -> "Create App"
   - Choose "Business" type
   - Give it a name (e.g., "My Autopost Bot")

3. **Get a Page Access Token:**
   - In your app dashboard, go to "Tools" -> [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
   - Select your app from the dropdown
   - Click "Generate Access Token"
   - Under "Permissions", add these:
     - `pages_manage_posts`
     - `pages_read_engagement`
     - `pages_show_list`
   - Click "Generate Access Token" and authorize
   - Select your Page from the "Page" dropdown
   - Copy the token

4. **Extend the token to long-lived (60+ days):**
   - Go to [developers.facebook.com/tools/debug/accesstoken](https://developers.facebook.com/tools/debug/accesstoken/)
   - Paste your token and click "Debug"
   - Click "Extend Access Token" at the bottom
   - Copy the new long-lived token

> **Important:** Long-lived Page Access Tokens last about 60 days. Set a reminder to renew before it expires. When it expires, posts will fail and you'll get an email alert (that's what the SNS alarm is for).

### OpenAI API Key (required for AI images)

This generates the images for your posts using DALL-E.

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (you won't see it again)
5. Add billing: Go to [platform.openai.com/settings/organization/billing](https://platform.openai.com/settings/organization/billing) and add a payment method
   - Image generation costs about $0.04-0.08 per image

### OpenRouter API Key (required for AI content)

OpenRouter gives you access to many AI language models through one API. This project uses it to generate your post captions.

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up and add credits (start with $5 -- this lasts weeks)
3. Go to [openrouter.ai/keys](https://openrouter.ai/keys)
4. Click "Create Key"
5. Copy the key

> **Why OpenRouter instead of OpenAI directly?** OpenRouter gives you access to cheaper models (GPT-4.1-mini costs ~$0.40/million tokens) and lets you switch models without code changes.

### Unsplash API Key (optional -- for free stock photos)

Unsplash provides free stock photos. Use this instead of (or alongside) OpenAI to reduce image generation costs.

1. Go to [unsplash.com/developers](https://unsplash.com/developers)
2. Click "Register as a developer"
3. Click "New Application"
4. Accept the guidelines and create the app
5. Copy the "Access Key" (not the Secret Key)

> **Tip:** Unsplash is free for up to 50 requests/hour. If some of your posts use Unsplash and others use OpenAI, you save money while still getting unique AI images where they matter most.

---

## 3. Clone and Install the Project

Open your terminal and run these commands:

```bash
# Download the project
git clone https://github.com/YOUR_USERNAME/aws-serverless-autopost-template.git
cd aws-serverless-autopost-template

# Install Python dependencies
pip install -r requirements-dev.txt
# If 'pip' doesn't work, try 'pip3' instead

# Install AWS CDK dependencies
cd infra && pip install -r requirements.txt && cd ..

# Verify everything installed correctly
make test
```

**Expected output for `make test`:**
```
tests/test_content_generator.py::TestStripMarkdown::test_removes_bold PASSED
tests/test_content_generator.py::TestStripMarkdown::test_removes_italic PASSED
...
============================== 34 passed in 1.08s ==============================
```

If all tests pass, your environment is set up correctly.

---

## 4. Configure Your Project

### Copy the example config:

```bash
cp .env.example .env
```

### Edit `.env` with your actual values:

Open `.env` in any text editor (VS Code, Notepad, nano, vim) and replace the placeholder values:

```bash
# === Facebook Graph API ===
FB_PAGE_ACCESS_TOKEN=EAAxxxxxxx     # Paste your long-lived token from Step 2
FB_APP_SECRET=abc123def456          # From your Facebook App dashboard -> Settings -> Basic
FB_GRAPH_API_VERSION=v23.0          # Leave as-is

# === Content Generation (LLM via OpenRouter) ===
OPENROUTER_API_KEY=sk-or-v1-xxxx   # From Step 2
OPENROUTER_MODEL=openai/gpt-4.1-mini  # Leave as-is (good balance of quality/cost)

# === Image Generation ===
OPENAI_API_KEY=sk-xxxx              # From Step 2
UNSPLASH_ACCESS_KEY=xxxx            # From Step 2 (leave as YOUR_... if not using Unsplash)

# === AWS Configuration ===
AWS_REGION=ap-southeast-1           # Change to your preferred region
AWS_PROFILE=default                 # Or your named profile from 'aws configure'

# === Project Configuration ===
PROJECT_NAME=my-autopost            # Short name, lowercase, hyphens only
TIMEZONE_OFFSET_HOURS=8             # Your UTC offset (e.g., 8 for PHT, -5 for EST, 0 for UTC)
OVERLAY_STYLE=panel                 # "panel" (square 1080x1080) or "gradient" (portrait 1080x1350)
WATERMARK_TEXT=FB: @YourPageName    # Small text in corner of images
SNS_ALARM_EMAIL=you@email.com       # Where to send error alerts
```

### Update the CDK stack config:

Open `infra/stacks/autopost_stack.py` and update the configuration section at the top:

```python
PROJECT_PREFIX = "my-autopost"              # Same as PROJECT_NAME above
ALARM_EMAIL = "you@email.com"              # Same as SNS_ALARM_EMAIL above
TIMEZONE_OFFSET_HOURS = "8"                # Same as above
OVERLAY_STYLE = "panel"                    # Same as above
WATERMARK_TEXT = "FB: @YourPageName"       # Same as above

FACEBOOK_SECRET_NAME = "my-autopost/facebook"
OPENAI_SECRET_NAME = "my-autopost/openai"
OPENROUTER_SECRET_NAME = "my-autopost/openrouter"
UNSPLASH_SECRET_NAME = "my-autopost/unsplash"
```

Also update `infra/app.py`:
```python
env=cdk.Environment(
    region="ap-southeast-1",  # Your AWS region
),
tags={
    "Project": "my-autopost",
    "Owner": "YourName",
    ...
}
```

---

## 5. Store Your Secrets in AWS

API keys must be stored securely in AWS Secrets Manager (not in your code).

### Option A: Use the setup script (recommended)

```bash
bash scripts/setup_secrets.sh --profile default
```

The script will ask you to enter each secret in JSON format. Here are the exact formats:

**Facebook secret:**
```json
{"page_access_token":"EAAxxxxxxx"}
```

**OpenAI secret:**
```json
{"api_key":"sk-xxxx"}
```

**OpenRouter secret:**
```json
{"api_key":"sk-or-v1-xxxx"}
```

**Unsplash secret:**
```json
{"access_key":"xxxx"}
```

### Option B: Create secrets manually in AWS Console

1. Go to [console.aws.amazon.com/secretsmanager](https://console.aws.amazon.com/secretsmanager/)
2. Make sure you're in the correct region (top-right dropdown)
3. Click "Store a new secret"
4. Choose "Other type of secret"
5. Enter key-value pairs:
   - For Facebook: key = `page_access_token`, value = your token
   - For OpenAI: key = `api_key`, value = your key
6. Name the secret exactly as configured in `autopost_stack.py` (e.g., `my-autopost/facebook`)
7. Click through the remaining steps and "Store"
8. Repeat for all 4 secrets

---

## 6. Customize Your Content

This is where you make it YOUR page. You need to edit 3 files.

### Step 6a: Define your posting schedule

Open `lambda/post_scheduler/config.py`:

```python
POST_SCHEDULE = [
    {
        "post_number": 1,
        "post_type": "morning-motivation",      # Unique slug (lowercase, hyphens)
        "local_time": "7:00 AM",                # Display only (for your reference)
        "display_name": "Morning Motivation",    # Human-readable name
        "image_source": "openai",               # "openai" or "unsplash"
    },
    {
        "post_number": 2,
        "post_type": "midday-tip",
        "local_time": "12:00 PM",
        "display_name": "Midday Tip",
        "image_source": "unsplash",             # Free stock photos
    },
    # Add more entries as needed...
]
```

> **Tip:** Start with 2-3 posts per day. You can always add more later.

### Step 6b: Write your content prompts

Open `lambda/content_generator/prompts.py`:

This is the most important file -- it tells the AI what to write. Replace the `YOUR_*` placeholders with your actual brand details.

For each post type in your schedule, add a matching entry to `CONTENT_PROMPTS` and `IMAGE_TEXT_MAP`.

**Example for a fitness page:**

```python
CONTENT_PROMPTS = {
    "morning-motivation": {
        "system": (
            "You are the social media voice for FitLife Manila.\n\n"
            "Tone: Energetic but not aggressive. Like a supportive gym buddy.\n"
            "Audience: Filipino young professionals (25-35) trying to stay fit.\n\n"
            "FACEBOOK RULES:\n"
            "- First line must be < 125 characters (before 'See More' cutoff)\n"
            "- 100-180 words total\n"
            "- Maximum 2 hashtags at the end\n"
            "- End with a call-to-action\n\n"
            "Respond with ONLY the post text."
        ),
        "user": (
            "Write a motivational morning fitness post for {date}.\n"
            "Include a practical tip they can do today."
        ),
    },
    # ... more post types
}
```

### Step 6c: Set your image styles

Open `lambda/image_generator/image_prompts.py`:

For each post type, add image generation prompts:

```python
BASE_PROMPTS = {
    "morning-motivation": [
        "Energetic gym scene, early morning sunlight, person doing stretches, "
        "vibrant colors, motivational mood. No text, no watermarks.",
        # Add 2-3 variants for variety
    ],
}
```

Also update `UNSPLASH_QUERIES` in `lambda/image_generator/unsplash_client.py` for post types that use Unsplash:

```python
UNSPLASH_QUERIES = {
    "midday-tip": [
        "healthy meal prep",
        "fitness workout",
        "yoga meditation",
    ],
}
```

### Step 6d: Match the schedule in CDK

Open `infra/stacks/autopost_stack.py` and update the `POST_SCHEDULE` to match your config from Step 6a:

```python
POST_SCHEDULE = [
    {
        "post_number": 1,
        "post_type": "morning-motivation",
        "local_time": "7:00 AM",
        # 7:00 AM at UTC+8 = 23:00 UTC previous day
        "cron": events.Schedule.cron(minute="0", hour="23"),
    },
    # ... match all entries from config.py
]
```

> **How to calculate UTC time:** Subtract your timezone offset from local time.
> - PHT (UTC+8): 7:00 AM - 8 = 23:00 UTC (previous day)
> - EST (UTC-5): 7:00 AM + 5 = 12:00 UTC
> - UTC: 7:00 AM = 07:00 UTC

---

## 7. Test Locally

Before deploying, test that your content generation works:

```bash
# Generate a sample image (no API keys needed -- uses placeholder image)
python scripts/generate_sample.py

# Test with real API keys (generates content + image, doesn't post to Facebook)
python scripts/test_post_local.py --post-number 1

# Preview output
open samples/  # Opens the samples folder to view generated images
```

If the sample looks good, you're ready to deploy.

---

## 8. Deploy to AWS

This single command creates all AWS resources and starts your posting schedule:

```bash
cd infra && cdk deploy --profile default
```

**First time only:** CDK will ask you to bootstrap your AWS account:
```bash
cdk bootstrap --profile default
# Then run cdk deploy again
```

**What happens during deploy:**
- CDK creates a CloudFormation stack in your AWS account
- It provisions all resources (Lambda functions, EventBridge rules, DynamoDB table, etc.)
- EventBridge starts triggering posts on your schedule

**Expected output:**
```
 ✅  AutopostStack

Outputs:
AutopostStack.ImageBucketName = my-autopost-autopost-images-123456789
AutopostStack.PostedTableName = my-autopost-posted-content
AutopostStack.AlarmTopicArn = arn:aws:sns:...

Stack ARN: arn:aws:cloudformation:...
```

> **Important:** After the first deploy, check your email for an SNS subscription confirmation. Click "Confirm subscription" to receive error alerts.

---

## 9. Verify It Works

### Check the CloudWatch Dashboard

1. Go to [console.aws.amazon.com/cloudwatch](https://console.aws.amazon.com/cloudwatch/)
2. Click "Dashboards" in the left sidebar
3. Open the dashboard named `{your-project}-Autopost`
4. You should see invocation and error graphs for all 4 Lambda functions

### Check DynamoDB for posted records

1. Go to [console.aws.amazon.com/dynamodb](https://console.aws.amazon.com/dynamodb/)
2. Click "Tables" -> your table (e.g., `my-autopost-posted-content`)
3. Click "Explore table items"
4. After a post runs, you should see a record with `post_key`, `post_id`, and `date`

### Check your Facebook Page

Visit your Facebook Page -- you should see your first automated post appear at the next scheduled time.

---

## 10. Troubleshooting

### "No module named X" when running tests

Make sure you installed dependencies:
```bash
pip install -r requirements-dev.txt
```

If `pip` doesn't work, try `pip3`.

### "cdk: command not found"

Install the CDK CLI:
```bash
npm install -g aws-cdk
```

### "Unable to resolve AWS account" during deploy

Make sure your AWS CLI is configured:
```bash
aws sts get-caller-identity
# Should show your AWS account ID
```

If it fails, re-run `aws configure` with your credentials.

### Posts are not appearing on Facebook

1. **Check CloudWatch Logs:** Go to CloudWatch -> Log Groups -> search for your Lambda function names. Look at the latest log stream for errors.

2. **Check the Dead Letter Queue:** Go to SQS -> your DLQ. If there are messages, something failed.

3. **Common errors:**
   - `"Page access token expired (error 190)"` -- Your Facebook token expired. Generate a new one (see Step 2) and update the secret in Secrets Manager.
   - `"Duplicate post detected (error 506)"` -- Facebook blocked a duplicate post. This is normal and safe to ignore.
   - `"Rate limited"` -- The system automatically retries. If it persists, reduce posting frequency.

4. **Check the timezone:** Make sure your cron expressions in `autopost_stack.py` are correct. A common mistake is forgetting to convert from local time to UTC.

### "ResourceNotFoundException" for DynamoDB

The CDK stack hasn't been deployed yet, or the table name doesn't match. Run `cdk deploy` first.

### Images look wrong or have no text

- Make sure you have font files (`.ttf`) in the `fonts/` directory
- For panel style: use landscape source images (3:2 ratio works best)
- For gradient style: use portrait source images (2:3 ratio works best)
- If using default fonts (no TTF files), text will appear in a basic system font

### How to update after making changes

After editing prompts, image styles, or schedule:
```bash
cd infra && cdk deploy --profile default
```

Only the changed resources are updated -- existing data in DynamoDB is preserved.

### How to stop the autoposter

To temporarily stop all posts:
```bash
# Disable all EventBridge rules (posts stop, resources remain)
aws events list-rules --name-prefix "my-autopost" --query 'Rules[].Name' --output text | \
  xargs -I {} aws events disable-rule --name {}
```

To re-enable:
```bash
aws events list-rules --name-prefix "my-autopost" --query 'Rules[].Name' --output text | \
  xargs -I {} aws events enable-rule --name {}
```

To permanently remove everything:
```bash
cd infra && cdk destroy --profile default
```

---

## What's Next?

- **Monitor:** Check your CloudWatch dashboard weekly for errors
- **Rotate tokens:** Set a reminder to renew your Facebook Page Access Token every 50 days
- **Iterate on prompts:** Read your posts, see what gets engagement, refine your prompts
- **Scale up:** Add more post types by following [the customization guide](CUSTOMIZATION_GUIDE.md)
- **Set up CI/CD:** Push to GitHub and configure the GitHub Actions workflows for automatic deploys (see `.github/workflows/`)
