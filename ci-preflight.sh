#!/bin/bash
set -e

echo "🔍 1. Linting GitHub Actions workflows with yamllint..."
yamllint .github/workflows/

echo "📄 2. Validating .env file for required variables..."
if [ -f .env ]; then
  echo "✅ .env validation passed."
else
  echo "❌ .env file missing."
  exit 1
fi

echo "🧪 3. Testing GitHub Actions CI workflow with act (if installed)..."
if command -v act >/dev/null 2>&1; then
  if [[ -f .secrets ]]; then
    echo "📁 Found .secrets file. Using it with act..."
    act --secret-file .secrets --dryrun
  elif [[ -n "$GITHUB_TOKEN" ]]; then
    echo "🔐 Found GITHUB_TOKEN in environment. Using it with act..."
    act -s GITHUB_TOKEN="$GITHUB_TOKEN" --dryrun
  else
    echo "⚠️  No .secrets file or GITHUB_TOKEN found. Skipping GitHub Actions dry-run."
  fi
else
  echo "⚠️  act not installed. Skipping GitHub Actions dry-run."
fi

echo "🐳 4. Running docker build dry-run for all services..."

SERVICES=(
  watcher
  metadata
  splitter
  packager
  organizer
  status-api
  maintenance
  telegram_youtube_bot
)

for service in "${SERVICES[@]}"; do
  echo "🚧 Building: $service"

  # Determine if target 'final' exists
  DOCKERFILE="./$service/Dockerfile"
  if grep -q "FROM .* as final" "$DOCKERFILE"; then
    TARGET_ARG="--target final"
  else
    TARGET_ARG=""
  fi

  # Build the image
  docker buildx build \
    --load \
    --progress=plain \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    -f "$DOCKERFILE" \
    $TARGET_ARG \
    "./$service"
done

echo "✅ CI Preflight Check Complete"
