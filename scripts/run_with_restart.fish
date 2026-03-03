#!/usr/bin/env fish

# 用法:
#   fish scripts/run_with_restart.fish
#   env MAX_RETRIES=0 RESTART_DELAY=10 fish scripts/run_with_restart.fish
#   env RUN_CMD="uv run main.py" fish scripts/run_with_restart.fish

set -q MAX_RETRIES; or set MAX_RETRIES 0
set -q RESTART_DELAY; or set RESTART_DELAY 5
set -q RUN_CMD; or set RUN_CMD "uv run main.py"

set SCRIPT_DIR (cd (dirname (status --current-filename)); pwd)
set PROJECT_ROOT (cd "$SCRIPT_DIR/.."; pwd)
cd "$PROJECT_ROOT"; or exit 1

set attempt 1
while true
    set start_time (date "+%Y-%m-%d %H:%M:%S")
    echo "[$start_time] Attempt #$attempt: $RUN_CMD"

    bash -lc "$RUN_CMD"
    set exit_code $status

    if test $exit_code -eq 0
        set end_time (date "+%Y-%m-%d %H:%M:%S")
        echo "[$end_time] Program exited successfully. No restart needed."
        exit 0
    end

    set fail_time (date "+%Y-%m-%d %H:%M:%S")
    echo "[$fail_time] Program crashed with exit code: $exit_code"

    if test "$MAX_RETRIES" -gt 0; and test "$attempt" -ge "$MAX_RETRIES"
        echo "Reached MAX_RETRIES=$MAX_RETRIES. Stop restarting."
        exit $exit_code
    end

    echo "Restarting in $RESTART_DELAY s..."
    sleep "$RESTART_DELAY"
    set attempt (math "$attempt + 1")
end
