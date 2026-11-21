#!/usr/bin/env bash
# Prepare a checkout for local development or CI on Linux/macOS.
set -euo pipefail

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$1" >&2
    exit 1
  fi
}

require_command git
require_command uv
require_command node
require_command npm
require_command make

node_major=$(node --version | sed -E 's/^v([0-9]+).*/\1/')
if [ "$node_major" -lt 22 ]; then
  printf 'Node.js 22 or newer is required; found %s\n' "$(node --version)" >&2
  exit 1
fi

uv sync --locked
npm ci
make check
