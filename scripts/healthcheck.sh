#!/usr/bin/env bash
set -u

require_docker=0
if [[ "${1:-}" == "--require-docker" ]]; then require_docker=1; fi

script_root="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
fixture="$script_root/healthcheck-fixture.json"

python_version="$(python --version 2>&1 || true)"
if [[ ! "$python_version" =~ ^Python\ 3\.12\. ]]; then
  echo "Python 3.12.x is required. Install it before running the health check." >&2
  exit 1
fi

if ! uv_version="$(uv --version 2>&1)"; then
  echo "uv is required. Install uv before running the health check." >&2
  exit 1
fi

if [[ ! -f "$fixture" ]]; then echo "Missing fixture: $fixture" >&2; exit 1; fi
python - "$fixture" <<'PY'
import json, sys
data = json.load(open(sys.argv[1], encoding="utf-8"))
assert data == {
    "tenant": "tenant-demo-a",
    "thread": "thread-demo-health",
    "mode": "offline",
    "database": "sqlite",
    "adapter": "mock",
}
PY

echo "PASS python=$python_version"
echo "PASS uv=$uv_version"

node_version="$(node --version 2>/dev/null || true)"
if [[ "$node_version" =~ ^v20\. ]]; then echo "PASS node=$node_version"; else echo "WARN Node.js 20 LTS is not available; continuing in offline mode."; fi

docker_version="$(docker --version 2>/dev/null || true)"
compose_version="$(docker compose version 2>/dev/null || true)"
if [[ -n "$docker_version" && -n "$compose_version" ]]; then
  echo "PASS docker=$docker_version"
  echo "PASS compose=$compose_version"
elif [[ "$require_docker" == 1 ]]; then
  echo "Docker Engine 24+ and Docker Compose v2 are required in strict mode." >&2
  exit 1
else
  echo "WARN Docker/Compose is not available; continuing with SQLite + Mock offline mode."
fi

echo "HEALTHCHECK_PASS mode=offline database=sqlite adapter=mock"
