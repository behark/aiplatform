#!/usr/bin/env bash
# Build and run tests inside Docker to avoid local dependency/build issues.
set -euo pipefail

IMAGE_NAME=aiplatform-ci

docker build -f Dockerfile.ci -t ${IMAGE_NAME} .

docker run --rm ${IMAGE_NAME}
