"""
Launch-testing based end-to-end movement test.

Usage:
    cd $HOME/shared/neobotix_workspace
    source install/setup.bash
    launch_test src/neobotix_e2e_test/test/test_e2e_movement.py -v
"""

import os
import time
import unittest

import launch
import launch_testing
import launch_testing.actions
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_test_description():
    e2e_test_dir = get_package_share_directory('neobotix_e2e_test')

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(e2e_test_dir, 'launch', 'test_simulation.launch.py')
        )
    )

    # Delay test node to let simulation fully initialize (spawn_entity needs time)
    test_node = TimerAction(
        period=20.0,
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
        launch_testing.actions.ReadyToTest(),
    ])


class TestRobotMovement(unittest.TestCase):

    def test_wait_for_test_node(self, proc_info):
        """Wait for test_robot_movement node to appear, finish, and assert exit code 0."""
        test_proc = None
        start = time.monotonic()
        # Wait up to 30s for the process to appear
        while time.monotonic() - start < 30:
            for proc in proc_info.processes():
                name = proc.process_details.get('name', '')
                if 'test_robot_movement' in name:
                    test_proc = proc
                    break
            if test_proc is not None:
                break
            time.sleep(0.5)

        if test_proc is None:
            available = [p.process_details.get('name', '') for p in proc_info.processes()]
            self.fail(f"test_robot_movement process not found. Available: {available}")

        # Wait for the test node to finish (up to 180s)
        proc_info.assertWaitForShutdown(process=test_proc, timeout=180)

        # Assert it exited with code 0 (pass)
        launch_testing.asserts.assertExitCodes(
            proc_info,
            process=test_proc,
            allowable_exit_codes=[0],
        )


@launch_testing.post_shutdown_test()
class TestRobotMovementAfterShutdown(unittest.TestCase):

    def test_exit_codes(self, proc_info):
        """Allow SIGINT (-2) for normal shutdown."""
        launch_testing.asserts.assertExitCodes(
            proc_info,
            allowable_exit_codes=[0, 1, -2],
        )
