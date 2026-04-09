#!/usr/bin/env bash
# Wrapper for barcode-validator CLI — intended for AI agent invocation.
# Usage: ./scripts/validate.sh <file> [--expected <value>]
set -euo pipefail
exec uv run barcode-validator "$@" --json
