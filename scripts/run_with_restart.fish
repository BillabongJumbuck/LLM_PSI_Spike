#!/usr/bin/env fish

# 优先级：环境变量 > 自动检测 .venv/bin/python > 系统 python3
if not set -q RUN_CMD
    if test -f ".venv/bin/python"
        set -g RUN_CMD ".venv/bin/python main.py"
    else
        set -g RUN_CMD "python3 main.py"
    end
end

set -q MAX_RETRIES; or set MAX_RETRIES 0
set -q RESTART_DELAY; or set RESTART_DELAY 5

set SCRIPT_DIR (cd (dirname (status --current-filename)); pwd)
set PROJECT_ROOT (cd "$SCRIPT_DIR/.."; pwd)
cd "$PROJECT_ROOT"; or exit 1

set attempt 1
while true
    set start_time (date "+%Y-%m-%d %H:%M:%S")
    echo "[$start_time] Attempt #$attempt: $RUN_CMD"

    # 注意：这里直接执行命令，不再强制通过 bash -lc
    # 这样可以继承 fish 当前的 PATH 和变量
    eval $RUN_CMD
    set exit_code $status

    if test $exit_code -eq 0
        set end_time (date "+%Y-%m-%d %H:%M:%S")
        echo "[$end_time] Program exited successfully."
        exit 0
    end

    set fail_time (date "+%Y-%m-%d %H:%M:%S")
    echo "[$fail_time] Program crashed with exit code: $exit_code"

    # 如果 MAX_RETRIES 为 0，则代表无限重试
    if test "$MAX_RETRIES" -gt 0; and test "$attempt" -ge "$MAX_RETRIES"
        echo "Reached MAX_RETRIES=$MAX_RETRIES. Stop."
        exit $exit_code
    end

    echo "Restarting in $RESTART_DELAY s..."
    sleep "$RESTART_DELAY"
    set attempt (math "$attempt + 1")
end