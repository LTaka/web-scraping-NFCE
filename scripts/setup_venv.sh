#!/usr/bin/env bash
set -euo pipefail

DIR_ATUAL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR_ATUAL/install_linux.sh"
