"""Launch simulation and then run the e2e movement test."""

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    e2e_test_dir = get_package_share_directory('neobotix_e2e_test')

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(e2e_test_dir, 'launch', 'test_simulation.launch.py')
        )
    )

    # Wait a bit for simulation to start before running test
    test_node = TimerAction(
        period=15.0,
        actions=[
            Node(
                package='neobotix_e2e_test',
                executable='test_robot_movement',
                name='robot_movement_test',
                output='screen',
                parameters=[{
                    'linear_speed': 0.5,
                    'drive_duration_sec': 5.0,
                    'settle_duration_sec': 2.0,
                    'expected_min_distance': 0.2,
                    'topic_timeout_sec': 180.0,
                }],
            )
        ]
    )

    return LaunchDescription([
        simulation,
        test_node,
    ])
