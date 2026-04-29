#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default DISPLAY for Docker headless; on a normal PC keep whatever is already set.
if [[ -f /.dockerenv ]]; then
    export DISPLAY=${DISPLAY:-:10}
fi

source /opt/ros/humble/setup.bash
source "$SCRIPT_DIR/install/setup.bash"
exec gzclient --gui-client-plugin=libgazebo_ros_eol_gui.so
