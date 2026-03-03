#!/usr/bin/env bash
set -u

# 用法:
#   bash scripts/run_with_restart.sh
#   MAX_RETRIES=0 RESTART_DELAY=10 bash scripts/run_with_restart.sh
#   RUN_CMD="uv run main.py" bash scripts/run_with_restart.sh

MAX_RETRIES="${MAX_RETRIES:-0}"      # 0 表示无限重试
RESTART_DELAY="${RESTART_DELAY:-5}"  # 失败后等待秒数
RUN_CMD="${RUN_CMD:-uv run main.py}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}" || exit 1

attempt=1
while true; do
  start_time="$(date '+%Y-%m-%d %H:%M:%S')"
  echo "[$start_time] Attempt #${attempt}: ${RUN_CMD}"

  bash -lc "${RUN_CMD}"
  exit_code=$?

  if [[ ${exit_code} -eq 0 ]]; then
    end_time="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[$end_time] Program exited successfully. No restart needed."
    exit 0
  fi

  fail_time="$(date '+%Y-%m-%d %H:%M:%S')"
  echo "[$fail_time] Program crashed with exit code: ${exit_code}"

  if [[ "${MAX_RETRIES}" -gt 0 && "${attempt}" -ge "${MAX_RETRIES}" ]]; then
    echo "Reached MAX_RETRIES=${MAX_RETRIES}. Stop restarting."
    exit ${exit_code}
  fi

  echo "Restarting in ${RESTART_DELAY}s..."
  sleep "${RESTART_DELAY}"
  attempt=$((attempt + 1))
done
