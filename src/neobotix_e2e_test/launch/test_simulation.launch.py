"""Minimal simulation launch for e2e testing (no teleop/xterm)."""

import os
import launch
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import xacro


def generate_launch_description():
    use_sim_time = True
    my_neo_robot = 'mpo_700'
    my_neo_environment = 'neo_workshop'

    # World path
    world_path = os.path.join(
        get_package_share_directory('neo_simulation2'),
        'worlds',
        my_neo_environment + '.world'
    )

    # Gazebo
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': world_path,
            'verbose': 'true',
            'gui': 'false',
        }.items()
    )

    # Robot description
    robot_description_xacro = os.path.join(
        get_package_share_directory('neo_simulation2'),
        'robots/' + my_neo_robot + '/',
        my_neo_robot + '.urdf.xacro'
    )

    xacro_args = {'use_gazebo': 'true', 'arm_type': '', 'use_docking_adapter': 'False'}
    robot_description_file = xacro.process_file(
        robot_description_xacro,
        mappings=xacro_args
    ).toxml()

    # Spawn robot
    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', my_neo_robot, '-topic', '/robot_description',
                   '-x', '0.0', '-y', '0.0', '-z', '0.0', '-Y', '0.0'],
        output='screen'
    )

    # Robot state publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_description_file
        }]
    )

    return LaunchDescription([
        robot_state_publisher,
        gazebo,
        spawn_entity,
    ])
