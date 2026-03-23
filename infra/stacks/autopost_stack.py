"""AWS CDK stack for the serverless autopost pipeline.

Creates the following infrastructure:
    - 4 Lambda functions (scheduler, content gen, image gen, poster)
    - N EventBridge cron rules (one per scheduled post)
    - S3 bucket for generated images (7-day auto-delete)
    - DynamoDB table for dedup tracking (TTL-based cleanup)
    - Secrets Manager references (Facebook, OpenAI, LLM, Unsplash)
    - SQS Dead Letter Queue (14-day retention)
    - SNS alarm topic with email notifications
    - CloudWatch dashboard + alarms for all functions

Architecture:
    EventBridge cron -> Post Scheduler -> Content Generator
                                       -> Image Generator -> S3
                                       -> Facebook Poster -> DynamoDB
"""

import os
import shutil
import subprocess
import sys

import jsii
from aws_cdk import (
    BundlingOptions,
    CfnOutput,
    Duration,
    ILocalBundling,
    RemovalPolicy,
    Stack,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_dynamodb as dynamodb,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_secretsmanager as secretsmanager,
    aws_sns as sns,
    aws_sns_subscriptions as sns_subs,
    aws_sqs as sqs,
)
from constructs import Construct

# ============================================================================
# CUSTOMIZE: Update these values to match your project
# ============================================================================

PROJECT_PREFIX = "YOUR_PROJECT_NAME"  # Used in resource names (e.g., "my-autopost")
ALARM_EMAIL = "YOUR_EMAIL@example.com"  # Error notification email
TIMEZONE_OFFSET_HOURS = "0"  # UTC offset (e.g., "8" for PHT, "-5" for EST)
OVERLAY_STYLE = "panel"  # "panel" (1080x1080) or "gradient" (1080x1350)
WATERMARK_TEXT = "YOUR_WATERMARK_TEXT"  # e.g., "FB: @YourPageName"

# Secret names in AWS Secrets Manager (create these before deploying)
FACEBOOK_SECRET_NAME = "YOUR_PROJECT/facebook"
OPENAI_SECRET_NAME = "YOUR_PROJECT/openai"
OPENROUTER_SECRET_NAME = "YOUR_PROJECT/openrouter"
UNSPLASH_SECRET_NAME = "YOUR_PROJECT/unsplash"

# Post schedule: define your EventBridge cron rules
# cron(minute hour day month day-of-week year) — all times in UTC
# Convert from your timezone: local_hour - TIMEZONE_OFFSET = UTC_hour
POST_SCHEDULE = [
    {
        "post_number": 1,
        "post_type": "YOUR_POST_TYPE_1",
        "local_time": "6:00 AM",
        # Example: 6:00 AM at UTC+8 = 22:00 UTC previous day
        "cron": events.Schedule.cron(minute="0", hour="22"),
    },
    {
        "post_number": 2,
        "post_type": "YOUR_POST_TYPE_2",
        "local_time": "12:00 PM",
        # Example: 12:00 PM at UTC+8 = 04:00 UTC
        "cron": events.Schedule.cron(minute="0", hour="4"),
    },
    {
        "post_number": 3,
        "post_type": "YOUR_POST_TYPE_3",
        "local_time": "6:00 PM",
        # Example: 6:00 PM at UTC+8 = 10:00 UTC
        "cron": events.Schedule.cron(minute="0", hour="10"),
    },
]

# ============================================================================


def _make_bundler(lambda_dir: str, extra_dirs: dict[str, str] | None = None):
    """Create a local bundler for Lambda deployment packages.

    Installs pip dependencies for the Lambda x86_64 architecture and copies
    source files + optional extra directories (like fonts/) into the bundle.

    This avoids Docker for faster CDK deploys.
    """

    @jsii.implements(ILocalBundling)
    class _LocalBundler:
        def try_bundle(
            self,
            output_dir: str,
            *,
            image,
            asset_hash=None,
            bundling_file_access=None,
            command=None,
            entrypoint=None,
            environment=None,
            local=None,
            network=None,
            output_type=None,
            platform=None,
            security_opt=None,
            user=None,
            volumes=None,
            volumes_from=None,
            working_directory=None,
        ) -> bool:
            source_dir = lambda_dir
            req_file = os.path.join(source_dir, "requirements.txt")

            # Install dependencies for Lambda runtime (Linux x86_64)
            if os.path.exists(req_file):
                subprocess.check_call(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "-r",
                        "requirements.txt",
                        "-t",
                        output_dir,
                        "--quiet",
                        "--platform",
                        "manylinux2014_x86_64",
                        "--implementation",
                        "cp",
                        "--python-version",
                        "3.11",
                        "--only-binary=:all:",
                    ],
                    cwd=source_dir,
                )

            # Copy source files
            for item in os.listdir(source_dir):
                src = os.path.join(source_dir, item)
                dst = os.path.join(output_dir, item)
                if os.path.isfile(src) and not item.startswith("."):
                    shutil.copy2(src, dst)

            # Copy extra directories (e.g., fonts/)
            if extra_dirs:
                for src_dir, dest_subdir in extra_dirs.items():
                    dest_path = os.path.join(output_dir, dest_subdir)
                    if os.path.exists(src_dir):
                        shutil.copytree(src_dir, dest_path, dirs_exist_ok=True)

            return True

    return _LocalBundler()


class AutopostStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # =====================================================================
        # Secrets Manager — reference existing secrets (create them manually
        # or via scripts/setup_secrets.sh before deploying)
        # =====================================================================

        facebook_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "FacebookSecret", FACEBOOK_SECRET_NAME
        )
        openai_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "OpenAISecret", OPENAI_SECRET_NAME
        )
        openrouter_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "OpenRouterSecret", OPENROUTER_SECRET_NAME
        )
        unsplash_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "UnsplashSecret", UNSPLASH_SECRET_NAME
        )

        # =====================================================================
        # S3 Bucket — stores generated images temporarily
        # 7-day lifecycle rule auto-deletes old images (cost optimization)
        # =====================================================================

        image_bucket = s3.Bucket(
            self,
            "ImageBucket",
            bucket_name=f"{PROJECT_PREFIX}-autopost-images-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(expiration=Duration.days(7)),
            ],
        )

        # =====================================================================
        # DynamoDB — tracks posted content for deduplication
        # PAY_PER_REQUEST = no cost at low volume, TTL auto-cleans old records
        # =====================================================================

        posted_table = dynamodb.Table(
            self,
            "PostedContent",
            table_name=f"{PROJECT_PREFIX}-posted-content",
            partition_key=dynamodb.Attribute(
                name="post_key", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            time_to_live_attribute="ttl",
        )

        # =====================================================================
        # SQS Dead Letter Queue — captures failed Lambda invocations
        # 14-day retention lets you inspect failures before messages expire
        # =====================================================================

        dlq = sqs.Queue(
            self,
            "AutopostDLQ",
            queue_name=f"{PROJECT_PREFIX}-autopost-dlq",
            retention_period=Duration.days(14),
        )

        # =====================================================================
        # SNS Alarm Topic — email notifications when things go wrong
        # =====================================================================

        alarm_topic = sns.Topic(
            self,
            "AlarmTopic",
            topic_name=f"{PROJECT_PREFIX}-autopost-alarms",
        )
        alarm_topic.add_subscription(sns_subs.EmailSubscription(ALARM_EMAIL))

        # =====================================================================
        # Lambda Functions — the 4-stage pipeline
        # =====================================================================

        lambda_base = os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
        fonts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "fonts")

        # --- Post Scheduler (orchestrator) ---
        post_scheduler = _lambda.Function(
            self,
            "PostScheduler",
            function_name=f"{PROJECT_PREFIX}-scheduler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset(
                os.path.join(lambda_base, "post_scheduler"),
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=["bash", "-c", "echo docker-fallback"],
                    local=_make_bundler(os.path.join(lambda_base, "post_scheduler")),
                ),
            ),
            timeout=Duration.minutes(5),
            memory_size=256,
            dead_letter_queue=dlq,
            environment={
                "CONTENT_GENERATOR_FUNCTION": f"{PROJECT_PREFIX}-content-generator",
                "IMAGE_GENERATOR_FUNCTION": f"{PROJECT_PREFIX}-image-generator",
                "FACEBOOK_POSTER_FUNCTION": f"{PROJECT_PREFIX}-facebook-poster",
                "DYNAMODB_TABLE_NAME": posted_table.table_name,
                "TIMEZONE_OFFSET_HOURS": TIMEZONE_OFFSET_HOURS,
            },
        )
        posted_table.grant_read_write_data(post_scheduler)

        # --- Content Generator ---
        content_generator = _lambda.Function(
            self,
            "ContentGenerator",
            function_name=f"{PROJECT_PREFIX}-content-generator",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset(
                os.path.join(lambda_base, "content_generator"),
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=["bash", "-c", "echo docker-fallback"],
                    local=_make_bundler(os.path.join(lambda_base, "content_generator")),
                ),
            ),
            timeout=Duration.minutes(3),
            memory_size=256,
            environment={
                "OPENROUTER_SECRET_ARN": openrouter_secret.secret_arn,
            },
        )
        openrouter_secret.grant_read(content_generator)

        # --- Image Generator (includes fonts in deployment package) ---
        image_generator = _lambda.Function(
            self,
            "ImageGenerator",
            function_name=f"{PROJECT_PREFIX}-image-generator",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset(
                os.path.join(lambda_base, "image_generator"),
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=["bash", "-c", "echo docker-fallback"],
                    local=_make_bundler(
                        os.path.join(lambda_base, "image_generator"),
                        extra_dirs={fonts_dir: "fonts"},
                    ),
                ),
            ),
            timeout=Duration.minutes(3),
            memory_size=512,
            environment={
                "OPENAI_SECRET_ARN": openai_secret.secret_arn,
                "UNSPLASH_SECRET_ARN": unsplash_secret.secret_arn,
                "IMAGE_BUCKET": image_bucket.bucket_name,
                "FONTS_DIR": "/var/task/fonts",
                "OVERLAY_STYLE": OVERLAY_STYLE,
                "WATERMARK_TEXT": WATERMARK_TEXT,
            },
        )
        openai_secret.grant_read(image_generator)
        unsplash_secret.grant_read(image_generator)
        image_bucket.grant_read_write(image_generator)

        # --- Facebook Poster ---
        facebook_poster = _lambda.Function(
            self,
            "FacebookPoster",
            function_name=f"{PROJECT_PREFIX}-facebook-poster",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset(
                os.path.join(lambda_base, "facebook_poster"),
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=["bash", "-c", "echo docker-fallback"],
                    local=_make_bundler(os.path.join(lambda_base, "facebook_poster")),
                ),
            ),
            timeout=Duration.seconds(60),
            memory_size=256,
            environment={
                "FACEBOOK_SECRET_ARN": facebook_secret.secret_arn,
                "IMAGE_BUCKET": image_bucket.bucket_name,
                "DYNAMODB_TABLE_NAME": posted_table.table_name,
            },
        )
        facebook_secret.grant_read(facebook_poster)
        image_bucket.grant_read(facebook_poster)
        posted_table.grant_read_write_data(facebook_poster)

        # =====================================================================
        # IAM — grant scheduler permission to invoke downstream Lambdas
        # (least-privilege: each function only gets what it needs)
        # =====================================================================

        content_generator.grant_invoke(post_scheduler)
        image_generator.grant_invoke(post_scheduler)
        facebook_poster.grant_invoke(post_scheduler)

        # =====================================================================
        # EventBridge Rules — N cron rules for N scheduled posts
        # Each rule passes {post_number, post_type} to the scheduler
        # =====================================================================

        for post in POST_SCHEDULE:
            rule = events.Rule(
                self,
                f"Schedule-{post['post_number']:02d}-{post['post_type']}",
                rule_name=f"{PROJECT_PREFIX}-{post['post_number']:02d}-{post['post_type']}",
                schedule=post["cron"],
                description=(
                    f"Post #{post['post_number']} ({post['post_type']}) "
                    f"at {post['local_time']} local"
                ),
            )
            rule.add_target(
                targets.LambdaFunction(
                    post_scheduler,
                    event=events.RuleTargetInput.from_object(
                        {
                            "post_number": post["post_number"],
                            "post_type": post["post_type"],
                        }
                    ),
                )
            )

        # =====================================================================
        # CloudWatch Alarms — alert on failures
        # =====================================================================

        # Alarm: messages landing in the Dead Letter Queue
        cloudwatch.Alarm(
            self,
            "DLQMessagesAlarm",
            metric=dlq.metric_approximate_number_of_messages_visible(),
            threshold=1,
            evaluation_periods=1,
            alarm_description="Messages in the autopost dead letter queue",
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        ).add_alarm_action(cw_actions.SnsAction(alarm_topic))

        # Alarm: per-Lambda error thresholds
        for fn_name, fn in [
            ("Scheduler", post_scheduler),
            ("ContentGen", content_generator),
            ("ImageGen", image_generator),
            ("Poster", facebook_poster),
        ]:
            cloudwatch.Alarm(
                self,
                f"{fn_name}ErrorsAlarm",
                metric=fn.metric_errors(),
                threshold=3,
                evaluation_periods=1,
                alarm_description=f"{fn_name} Lambda errors",
            ).add_alarm_action(cw_actions.SnsAction(alarm_topic))

        # =====================================================================
        # CloudWatch Dashboard — single-pane-of-glass monitoring
        # =====================================================================

        dashboard = cloudwatch.Dashboard(
            self,
            "AutopostDashboard",
            dashboard_name=f"{PROJECT_PREFIX}-Autopost",
        )
        dashboard.add_widgets(
            cloudwatch.Row(
                cloudwatch.GraphWidget(
                    title="Scheduler Invocations & Errors",
                    left=[post_scheduler.metric_invocations(period=Duration.hours(1))],
                    right=[post_scheduler.metric_errors(period=Duration.hours(1))],
                    width=12,
                ),
                cloudwatch.GraphWidget(
                    title="Facebook Poster Invocations & Errors",
                    left=[facebook_poster.metric_invocations(period=Duration.hours(1))],
                    right=[facebook_poster.metric_errors(period=Duration.hours(1))],
                    width=12,
                ),
            ),
            cloudwatch.Row(
                cloudwatch.GraphWidget(
                    title="Content & Image Generator",
                    left=[
                        content_generator.metric_invocations(period=Duration.hours(1)),
                        image_generator.metric_invocations(period=Duration.hours(1)),
                    ],
                    right=[
                        content_generator.metric_errors(period=Duration.hours(1)),
                        image_generator.metric_errors(period=Duration.hours(1)),
                    ],
                    width=12,
                ),
                cloudwatch.GraphWidget(
                    title="Lambda Duration",
                    left=[
                        post_scheduler.metric_duration(period=Duration.hours(1)),
                        content_generator.metric_duration(period=Duration.hours(1)),
                        image_generator.metric_duration(period=Duration.hours(1)),
                        facebook_poster.metric_duration(period=Duration.hours(1)),
                    ],
                    width=12,
                ),
            ),
        )

        # =====================================================================
        # Stack Outputs
        # =====================================================================

        CfnOutput(self, "ImageBucketName", value=image_bucket.bucket_name)
        CfnOutput(self, "PostedTableName", value=posted_table.table_name)
        CfnOutput(self, "AlarmTopicArn", value=alarm_topic.topic_arn)
