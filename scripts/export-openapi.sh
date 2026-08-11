#!/usr/bin/env bash
# Export OpenAPI JSON for shared frontend types.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/api"
export PYTHONPATH="$ROOT/apps/api"
export APP_ENV="${APP_ENV:-development}"
mkdir -p "$ROOT/packages/shared-types"
python -c "
from app.main import app
import json
from pathlib import Path
out = Path('$ROOT/packages/shared-types/openapi.json')
out.write_text(json.dumps(app.openapi(), indent=2))
print('Wrote', out)
"
