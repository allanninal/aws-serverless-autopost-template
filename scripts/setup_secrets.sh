#!/bin/bash
# ============================================================================
# Setup AWS Secrets Manager entries for the autopost pipeline.
#
# Run this ONCE before deploying the CDK stack.
# Requires: AWS CLI configured with appropriate permissions.
#
# Usage:
#   bash scripts/setup_secrets.sh
#   bash scripts/setup_secrets.sh --profile your-aws-profile
#   bash scripts/setup_secrets.sh --profile your-aws-profile --region ap-southeast-1
# ============================================================================

set -euo pipefail

# Parse arguments
PROFILE_FLAG=""
REGION="${AWS_REGION:-us-east-1}"

while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            PROFILE_FLAG="--profile $2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            echo "Usage: bash setup_secrets.sh [--profile PROFILE] [--region REGION]"
            exit 1
            ;;
    esac
done

echo ""
echo "============================================"
echo "  AWS Secrets Manager Setup"
echo "  Region: $REGION"
echo "============================================"
echo ""
echo "This script creates 4 secrets in AWS Secrets Manager."
echo "You will be prompted to enter each API key."
echo ""
echo "Before you start, make sure you have:"
echo "  1. Facebook Page Access Token (from developers.facebook.com)"
echo "  2. OpenAI API Key (from platform.openai.com/api-keys)"
echo "  3. OpenRouter API Key (from openrouter.ai/keys)"
echo "  4. Unsplash Access Key (from unsplash.com/developers) - optional"
echo ""
read -p "Press Enter to continue (or Ctrl+C to cancel)..."
echo ""

# Configurable secret prefix
read -p "Enter your project name (e.g., my-autopost): " PROJECT_PREFIX
echo ""

# Helper function
create_secret_interactive() {
    local name=$1
    local description=$2
    local key_name=$3
    local example=$4

    echo "-------------------------------------------"
    echo "Secret: $name"
    echo "  $description"
    echo ""
    echo "  Expected format:  {\"$key_name\":\"$example\"}"
    echo ""

    if aws secretsmanager describe-secret --secret-id "$name" --region "$REGION" $PROFILE_FLAG &>/dev/null; then
        echo "  -> Already exists! Skipping."
        echo "     (To update, use: aws secretsmanager put-secret-value --secret-id $name --secret-string '...')"
    else
        read -p "  Paste your $key_name: " key_value

        if [[ -z "$key_value" ]]; then
            echo "  -> Skipped (empty value). You can create this later."
        else
            # Build JSON automatically so user only pastes the raw key
            local json_value="{\"$key_name\":\"$key_value\"}"

            aws secretsmanager create-secret \
                --name "$name" \
                --description "$description" \
                --secret-string "$json_value" \
                --region "$REGION" \
                $PROFILE_FLAG \
                --output text --query 'ARN'

            echo "  -> Created successfully!"
        fi
    fi
    echo ""
}

create_secret_interactive "${PROJECT_PREFIX}/facebook" \
    "Facebook Page Access Token" \
    "page_access_token" \
    "EAAxxxxxxxxx..."

create_secret_interactive "${PROJECT_PREFIX}/openai" \
    "OpenAI API Key for image generation (DALL-E)" \
    "api_key" \
    "sk-xxxxxxxx..."

create_secret_interactive "${PROJECT_PREFIX}/openrouter" \
    "OpenRouter API Key for LLM content generation" \
    "api_key" \
    "sk-or-v1-xxxxxxxx..."

create_secret_interactive "${PROJECT_PREFIX}/unsplash" \
    "Unsplash Access Key for stock photos (optional)" \
    "access_key" \
    "xxxxxxxx..."

echo ""
echo "============================================"
echo "  Setup complete!"
echo ""
echo "  Your secrets are stored as:"
echo "    - ${PROJECT_PREFIX}/facebook"
echo "    - ${PROJECT_PREFIX}/openai"
echo "    - ${PROJECT_PREFIX}/openrouter"
echo "    - ${PROJECT_PREFIX}/unsplash"
echo ""
echo "  IMPORTANT: Make sure the secret names above"
echo "  match the values in infra/stacks/autopost_stack.py:"
echo ""
echo "    FACEBOOK_SECRET_NAME  = \"${PROJECT_PREFIX}/facebook\""
echo "    OPENAI_SECRET_NAME    = \"${PROJECT_PREFIX}/openai\""
echo "    OPENROUTER_SECRET_NAME = \"${PROJECT_PREFIX}/openrouter\""
echo "    UNSPLASH_SECRET_NAME  = \"${PROJECT_PREFIX}/unsplash\""
echo ""
echo "  Next step: cd infra && cdk deploy"
echo "============================================"
