#!/usr/bin/env bash
set -euo pipefail

if [[ -n "$SITE_PATH" ]] && {
    [[ ! "$SITE_PATH" =~ ^[a-zA-Z0-9._-]+(/[a-zA-Z0-9._-]+)*$ ]] ||
    [[ "/$SITE_PATH/" == *"/../"* || "/$SITE_PATH/" == *"/./"* ]]
}; then
    echo "::error::Site path must contain relative path segments without '.' or '..'"
    exit 1
fi

if [[ ! -d "$SITE_SOURCE_DIR" ]]; then
    echo "::error::Source directory '$SITE_SOURCE_DIR' does not exist"
    exit 1
fi

VERSION="v$(date +%Y%m%d-%H%M%S)-${GITHUB_SHA::7}"
ARCHIVE="${VERSION}.tar.gz"
S3_PREFIX="sites/$SITE_DOMAIN/"
if [[ -n "$SITE_PATH" ]]; then
    S3_PREFIX+="$SITE_PATH/"
fi

echo "version=$VERSION" >> "$GITHUB_OUTPUT"
echo "archive=$ARCHIVE" >> "$GITHUB_OUTPUT"

echo "Creating archive from $SITE_SOURCE_DIR..."
tar -czf "$ARCHIVE" -C "$SITE_SOURCE_DIR" .

echo "Uploading $ARCHIVE..."
aws s3 cp "$ARCHIVE" \
    "s3://$SITE_BUCKET/$S3_PREFIX$ARCHIVE" \
    --endpoint-url "$SITE_ENDPOINT"

echo "Activating $VERSION..."
echo "$ARCHIVE" | aws s3 cp - \
    "s3://$SITE_BUCKET/${S3_PREFIX}CURRENT" \
    --endpoint-url "$SITE_ENDPOINT"

{
    echo "### Deployed $SITE_DOMAIN${SITE_PATH:+/$SITE_PATH}"
    echo ""
    echo "- **Version:** \`$VERSION\`"
    echo "- **S3 Path:** \`s3://$SITE_BUCKET/$S3_PREFIX\`"
} >> "$GITHUB_STEP_SUMMARY"

rm -f "$ARCHIVE"
