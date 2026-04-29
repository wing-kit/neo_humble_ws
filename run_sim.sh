#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default DISPLAY for Docker headless; on a normal PC keep whatever is already set.
if [[ -f /.dockerenv ]]; then
    export DISPLAY=${DISPLAY:-:10}
fi

# Use home dir for pid/log so the script works on any host.
# When invoked with sudo, fall back to the original user's home.
if [[ -n "${SUDO_USER:-}" ]] && [[ -d "/home/${SUDO_USER}" ]]; then
    RUNDIR="/home/${SUDO_USER}/.neo_sim"
elif [[ -n "${SUDO_USER:-}" ]] && [[ "${HOME}" == "/root" ]]; then
    RUNDIR="/root/.neo_sim"
else
    RUNDIR="${HOME}/.neo_sim"
fi
mkdir -p "$RUNDIR"
PIDFILE="$RUNDIR/neo_simulation.pid"
LOGFILE="$RUNDIR/neo_simulation.log"

usage() {
    cat <<EOF
Usage: $(basename "$0") {start|stop|kill|status|logs}

  start      Launch neo_workshop simulation backend (mpo_700, headless)
  stop       Gracefully stop the simulation
  kill       Force kill the simulation
  gui        Launch Gazebo GUI client (connects to running simulation)
  stop-gui   Stop the Gazebo GUI client only
  status     Check if simulation is running
  logs       Tail the simulation log
EOF
}

start_sim() {
    if [[ -f "$PIDFILE" ]] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "Simulation already running (PID $(cat "$PIDFILE"))"
        exit 0
    fi

    echo "=> Starting neo_workshop simulation..."
    : > "$LOGFILE"

    # Start in background, redirecting to log.
    # We avoid 'set -u' inside the subshell because gazebo setup scripts
    # reference potentially-unset variables.
    bash <<LAUNCHER_EOF >> "$LOGFILE" 2>&1 &
set +u
export DISPLAY="$DISPLAY"
source /usr/share/gazebo/setup.sh
source /opt/ros/humble/setup.bash
source "$SCRIPT_DIR/install/setup.bash"
exec ros2 launch neo_simulation2 simulation.launch.py my_robot:=mpo_700 world:=neo_workshop
LAUNCHER_EOF

    local bpid=$!
    sleep 3

    # Find the actual ros2 launch python process.
    local ros2_pid
    ros2_pid=$(pgrep -P "$bpid" -f "ros2 launch neo_simulation2" | head -n1 || true)
    if [[ -z "$ros2_pid" ]]; then
        ros2_pid=$(pgrep -f "ros2 launch neo_simulation2 simulation.launch.py" | head -n1 || true)
    fi

    if [[ -z "$ros2_pid" ]]; then
        echo "WARNING: Could not detect ros2 launch PID. Background PID=$bpid"
        echo "$bpid" > "$PIDFILE"
    else
        echo "$ros2_pid" > "$PIDFILE"
        echo "=> Simulation started (PID $ros2_pid). Log: $LOGFILE"
    fi
}

get_pgid() {
    local pid=$1
    ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' '
}

stop_sim() {
    if [[ ! -f "$PIDFILE" ]]; then
        echo "No PID file found ($PIDFILE)."
        cleanup_stale
        return
    fi

    local pid
    pid=$(cat "$PIDFILE")

    if ! kill -0 "$pid" 2>/dev/null; then
        echo "PID $pid is not running. Cleaning up..."
        rm -f "$PIDFILE"
        cleanup_stale
        return
    fi

    local pgid
    pgid=$(get_pgid "$pid")
    [[ -z "$pgid" ]] && pgid="$pid"

    echo "=> Gracefully stopping simulation (PID $pid)..."

    # SIGINT lets ros2 launch shut down its nodes cleanly.
    kill -INT "$pid" 2>/dev/null || true

    local waited=0
    while kill -0 "$pid" 2>/dev/null && [[ $waited -lt 15 ]]; do
        sleep 1
        waited=$((waited + 1))
    done

    if kill -0 "$pid" 2>/dev/null; then
        echo "=> Sending SIGTERM..."
        kill -TERM "$pid" 2>/dev/null || true
        sleep 3
    fi

    if kill -0 "$pid" 2>/dev/null; then
        echo "=> Force killing (SIGKILL)..."
        kill -KILL "$pid" 2>/dev/null || true
        sleep 1
    fi

    rm -f "$PIDFILE"
    cleanup_stale
    echo "=> Simulation stopped."
}

force_kill_sim() {
    if [[ -f "$PIDFILE" ]]; then
        local pid pgid
        pid=$(cat "$PIDFILE")
        pgid=$(get_pgid "$pid")
        [[ -n "$pgid" ]] && kill -KILL -- "-$pgid" 2>/dev/null || true
        kill -KILL "$pid" 2>/dev/null || true
        rm -f "$PIDFILE"
    fi
    cleanup_stale
    echo "=> Simulation force-killed."
}

cleanup_stale() {
    # Kill any remaining gazebo / ros2 / robot_state_publisher processes
    # tied to this specific simulation workspace.
    local pids
    pids=$(pgrep -f "gzserver.*neo_workshop|gzclient|ros2 launch neo_simulation2|spawn_entity.*mpo_700|robot_state_publisher|xterm.*teleop|teleop_twist_keyboard" || true)
    if [[ -n "$pids" ]]; then
        echo "=> Cleaning up stale processes..."
        echo "$pids" | xargs -r kill -KILL 2>/dev/null || true
        sleep 1
    fi
}

show_status() {
    if [[ -f "$PIDFILE" ]]; then
        local pid
        pid=$(cat "$PIDFILE")
        if kill -0 "$pid" 2>/dev/null; then
            local pgid
            pgid=$(get_pgid "$pid")
            echo "Simulation is RUNNING (PID $pid, PGID ${pgid:-?})"
            echo "  Log file: $LOGFILE"
            ps -p "$pid" -o pid,ppid,etime,comm 2>/dev/null || true
        else
            echo "PID file exists but process is DEAD (PID $pid)"
        fi
    else
        echo "Simulation is NOT running (no PID file)"
    fi

    local procs
    procs=$(pgrep -a -f "gzserver|gzclient|ros2 launch neo_simulation2|spawn_entity|robot_state_publisher" 2>/dev/null || true)
    if [[ -n "$procs" ]]; then
        echo "--- Related processes ---"
        echo "$procs"
    fi
}

tail_logs() {
    if [[ -f "$LOGFILE" ]]; then
        tail -f "$LOGFILE"
    else
        echo "No log file at $LOGFILE"
    fi
}

start_gui() {
    if pgrep -x "gzclient" >/dev/null 2>&1; then
        echo "Gazebo client (gzclient) is already running."
        exit 0
    fi

    if ! pgrep -x "gzserver" >/dev/null 2>&1; then
        echo "WARNING: gzserver is not running. Start the simulation first with: ./run_sim.sh start"
        exit 1
    fi

    echo "=> Starting Gazebo GUI (gzclient)..."
    # Default to :10 only in Docker; otherwise trust the host DISPLAY.
    if [[ -f /.dockerenv ]]; then
        export DISPLAY=${DISPLAY:-:10}
    else
        export DISPLAY=${DISPLAY:-:0}
    fi
    export XAUTHORITY=${XAUTHORITY:-$HOME/.Xauthority}

    # Write a small launcher script to avoid heredoc background quirks
    local launcher="$RUNDIR/start_gzclient.sh"
    cat > "$launcher" <<'GZL_EOF'
#!/usr/bin/env bash
set +u
export DISPLAY="$1"
export XAUTHORITY="$2"
source /usr/share/gazebo/setup.sh
source /opt/ros/humble/setup.bash
source "$3/install/setup.bash"
# Use ros2 launch so gzclient gets the same environment as the original launch.
exec ros2 launch gazebo_ros gzclient.launch.py gui_required:=false
GZL_EOF
    chmod +x "$launcher"

    nohup "$launcher" "$DISPLAY" "$XAUTHORITY" "$SCRIPT_DIR" >> "$RUNDIR/gzclient.log" 2>&1 &

    local bpid=$!
    sleep 3

    local gzc_pid
    gzc_pid=$(pgrep -P "$bpid" -x "gzclient" | head -n1 || true)
    if [[ -z "$gzc_pid" ]]; then
        gzc_pid=$(pgrep -x "gzclient" | head -n1 || true)
    fi

    if [[ -n "$gzc_pid" ]]; then
        echo "=> Gazebo GUI started (PID $gzc_pid)."
    else
        echo "WARNING: gzclient may have failed to start. Check $RUNDIR/gzclient.log"
    fi
}

stop_gui() {
    local pids
    pids=$(pgrep -x "gzclient" || true)
    if [[ -n "$pids" ]]; then
        echo "=> Stopping Gazebo GUI..."
        echo "$pids" | xargs -r kill -TERM 2>/dev/null || true
        sleep 2
        pids=$(pgrep -x "gzclient" || true)
        if [[ -n "$pids" ]]; then
            echo "$pids" | xargs -r kill -KILL 2>/dev/null || true
        fi
        echo "=> Gazebo GUI stopped."
    else
        echo "Gazebo GUI is not running."
    fi
}

case "${1:-}" in
    start)
        start_sim
        ;;
    stop)
        stop_sim
        ;;
    kill)
        force_kill_sim
        ;;
    gui)
        start_gui
        ;;
    stop-gui)
        stop_gui
        ;;
    status)
        show_status
        ;;
    logs)
        tail_logs
        ;;
    *)
        usage >&2
        exit 1
        ;;
esac
