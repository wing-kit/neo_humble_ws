# NeoBotix ROS 2 Humble Workspace

This workspace contains ROS 2 packages for Neobotix robots, configured for ROS 2 Humble. It runs on any Ubuntu 22.04 PC with ROS 2 Humble installed, and also inside Docker containers.

## Packages

This workspace includes the following packages:

- `neo_common2` - Common utilities and helpers for Neobotix robots
- `neo_local_planner2` - Local planner plugin for navigation
- `neo_localization2` - Localization package for Neobotix robots
- `neo_msgs2` - Message definitions for Neobotix robots
- `neo_nav2_bringup` - Navigation bringup configurations and launch files
- `neo_simulation2` - Simulation packages for Neobotix robots
- `neo_srvs2` - Service definitions for Neobotix robots

## Prerequisites

- Ubuntu 22.04
- ROS 2 Humble installed (`/opt/ros/humble/setup.bash`)
- Gazebo (classic) and `gazebo_ros_pkgs`

## Setup

1. Clone this repository:
```bash
git clone --recurse-submodules https://github.com/wing-kit/neo_humble_ws.git
cd neo_humble_ws
```

2. Source ROS 2 Humble:
```bash
source /opt/ros/humble/setup.bash
```

3. Build the workspace:
```bash
colcon build
```

4. Source the workspace:
```bash
source install/setup.bash
```

## Running the Simulation

A convenience script is provided at the workspace root:

```bash
./run_sim.sh start      # Start the simulation headless
./run_sim.sh gui        # Start the Gazebo GUI (connects to running sim)
./run_sim.sh stop       # Stop the simulation gracefully
./run_sim.sh kill       # Force-kill the simulation
./run_sim.sh status     # Check simulation status
./run_sim.sh logs       # Tail the simulation log
```

The script auto-detects whether it is running inside a Docker container and adjusts `DISPLAY` accordingly. On a normal PC it will use your existing X11 session; in Docker it defaults to `:10` for headless/VNC setups.

You can also launch manually:
```bash
ros2 launch neo_simulation2 simulation.launch.py my_robot:=mpo_700 world:=neo_workshop
```

## Gazebo Desktop Shortcut

`Gazebo.desktop` is a portable desktop entry. It resolves its own location and runs `run_gazebo_gui.sh` next to it. If you copy the `.desktop` file elsewhere, ensure `run_gazebo_gui.sh` stays in the same directory.

## Notes

- `build/` and `install/` contain absolute paths from the machine they were last built on. Always run `colcon build` after cloning to a new PC or location.
- The `robot_name.txt` state file is now stored in `~/.neo_sim/robot_name.txt` so launch files work regardless of the current working directory.

## License

Each package maintains its own license. Please refer to individual package LICENSE files.
