#!/bin/bash
# Deploy DuberyMNL Chatbot to Google Cloud Run
# Usage: cd cloud-run && bash deploy.sh

set -e

PROJECT_ID="dubery"
SERVICE_NAME="duberymnl-chatbot"
REGION="asia-southeast1"

# Load env vars from parent .env (safe parsing -- handles special chars)
if [ ! -f "../.env" ]; then
    echo "ERROR: ../.env not found. Run from cloud-run/ directory."
    exit 1
fi

# Use Python to safely parse .env (handles special chars, quotes, blank lines)
eval "$(python -c "
from dotenv import dotenv_values
vals = dotenv_values('../.env')
for k, v in vals.items():
    # Shell-escape the value
    v = (v or '').replace(\"'\", \"'\\\"'\\\"'\")
    print(f\"export {k}='{v}'\")
")"

# Verify required vars
for var in META_ADS_ACCESS_TOKEN META_PAGE_ACCESS_TOKEN META_PAGE_ID; do
    if [ -z "${!var}" ]; then
        echo "ERROR: $var is not set in .env"
        exit 1
    fi
done

echo "Deploying $SERVICE_NAME to Cloud Run ($REGION)..."

gcloud run deploy "$SERVICE_NAME" \
    --source=. \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --set-env-vars="META_ADS_ACCESS_TOKEN=$META_ADS_ACCESS_TOKEN,META_PAGE_ACCESS_TOKEN=$META_PAGE_ACCESS_TOKEN,META_PAGE_ID=$META_PAGE_ID,MESSENGER_VERIFY_TOKEN=${MESSENGER_VERIFY_TOKEN:-duberymnl_verify},GMAIL_SENDER=$GMAIL_SENDER,GMAIL_APP_PASSWORD=$GMAIL_APP_PASSWORD,REVIEW_EMAIL_RECIPIENT=$REVIEW_EMAIL_RECIPIENT" \
    --no-cpu-throttling \
    --min-instances=1 \
    --max-instances=3 \
    --memory=512Mi \
    --cpu=1 \
    --timeout=60s \
    --concurrency=80 \
    --port=8080

# Print service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format='value(status.url)')

echo ""
echo "Deployed successfully!"
echo "Service URL: $SERVICE_URL"
echo ""
echo "Next steps:"
echo "  1. Test:  curl $SERVICE_URL/status"
echo "  2. Verify webhook: curl \"$SERVICE_URL/webhook?hub.mode=subscribe&hub.verify_token=duberymnl_verify&hub.challenge=test123\""
echo "  3. Configure Meta webhooks in App Dashboard:"
echo "     - Messenger: $SERVICE_URL/webhook"
echo "     - Feed:      $SERVICE_URL/comment-webhook"
echo "  4. Subscribe page:"
echo "     curl -X POST \"https://graph.facebook.com/v21.0/$META_PAGE_ID/subscribed_apps?subscribed_fields=messages,feed&access_token=$META_PAGE_ACCESS_TOKEN\""
