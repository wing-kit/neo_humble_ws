# NeoBotix ROS 2 Humble Workspace

This workspace contains ROS 2 packages for Neobotix robots, configured for ROS 2 Humble.

## Packages

This workspace includes the following packages:

- `neo_common2` - Common utilities and helpers for Neobotix robots
- `neo_local_planner2` - Local planner plugin for navigation
- `neo_localization2` - Localization package for Neobotix robots
- `neo_msgs2` - Message definitions for Neobotix robots
- `neo_nav2_bringup` - Navigation bringup configurations and launch files
- `neo_simulation2` - Simulation packages for Neobotix robots
- `neo_srvs2` - Service definitions for Neobotix robots

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

## Usage

Refer to individual package README files for specific usage instructions.

## License

Each package maintains its own license. Please refer to individual package LICENSE files.
