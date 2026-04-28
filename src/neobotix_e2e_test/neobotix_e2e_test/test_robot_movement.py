#!/usr/bin/env python3
"""
End-to-end movement test for Neobotix robot in Gazebo.

Steps:
1. Wait for /odom topic and capture initial pose.
2. Publish cmd_vel (linear.x) for a fixed duration.
3. Wait for robot to settle.
4. Compare final pose with initial pose.
5. Exit 0 if displacement >= expected_min_distance, else exit 1.
"""

import sys
import time
import threading
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math


class RobotMovementTest(Node):
    def __init__(self):
        super().__init__('robot_movement_test')

        # Parameters
        self.declare_parameter('linear_speed', 0.5)
        self.declare_parameter('drive_duration_sec', 3.0)
        self.declare_parameter('settle_duration_sec', 2.0)
        self.declare_parameter('expected_min_distance', 1.0)
        self.declare_parameter('topic_timeout_sec', 60.0)
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('odom_topic', '/odom')

        self.linear_speed = self.get_parameter('linear_speed').value
        self.drive_duration = self.get_parameter('drive_duration_sec').value
        self.settle_duration = self.get_parameter('settle_duration_sec').value
        self.expected_min_distance = self.get_parameter('expected_min_distance').value
        self.topic_timeout = self.get_parameter('topic_timeout_sec').value
        self.cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        self.odom_topic = self.get_parameter('odom_topic').value

        self.get_logger().info(
            f"Config: speed={self.linear_speed} m/s, drive={self.drive_duration}s, "
            f"expected_min={self.expected_min_distance} m"
        )

        # Publishers / Subscribers
        self.cmd_vel_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10)
        self.odom_sub = self.create_subscription(
            Odometry, self.odom_topic, self.odom_callback, 10
        )

        # State
        self.initial_pose = None
        self.latest_pose = None
        self.odom_received_event = threading.Event()
        self.test_passed = False
        self.test_done = False

    def wait_for_topics(self) -> bool:
        """Verify required topics exist before starting test."""
        self.get_logger().info("Checking required topics exist ...")
        required_topics = [self.cmd_vel_topic, self.odom_topic]
        start = time.monotonic()
        while time.monotonic() - start < self.topic_timeout:
            topic_names = [t for t, _ in self.get_topic_names_and_types()]
            missing = [t for t in required_topics if t not in topic_names]
            if not missing:
                self.get_logger().info(
                    f"All required topics available: {required_topics}"
                )
                return True
            time.sleep(0.5)
        self.get_logger().error(
            f"Timeout waiting for topics. Missing: {missing}"
        )
        return False

    def odom_callback(self, msg: Odometry):
        pose = msg.pose.pose
        if self.initial_pose is None:
            self.initial_pose = pose
            self.get_logger().info(
                f"Initial pose captured: x={pose.position.x:.3f}, y={pose.position.y:.3f}"
            )
            self.odom_received_event.set()
        self.latest_pose = pose

    def wait_for_odom(self) -> bool:
        self.get_logger().info(f"Waiting for odometry on {self.odom_topic} ...")
        start = time.monotonic()
        while time.monotonic() - start < self.topic_timeout:
            if self.odom_received_event.is_set():
                return True
            time.sleep(0.1)
        self.get_logger().error("Timeout waiting for odometry topic!")
        return False

    def drive_forward(self):
        self.get_logger().info(
            f"Driving forward at {self.linear_speed} m/s for {self.drive_duration}s ..."
        )
        twist = Twist()
        twist.linear.x = self.linear_speed
        twist.angular.z = 0.0

        start = time.monotonic()
        while time.monotonic() - start < self.drive_duration:
            self.cmd_vel_pub.publish(twist)
            time.sleep(0.1)

        # Stop
        twist.linear.x = 0.0
        self.cmd_vel_pub.publish(twist)
        self.get_logger().info("Drive command complete, robot stopped.")

    def evaluate(self) -> bool:
        if self.initial_pose is None or self.latest_pose is None:
            self.get_logger().error("Missing pose data for evaluation!")
            return False

        dx = self.latest_pose.position.x - self.initial_pose.position.x
        dy = self.latest_pose.position.y - self.initial_pose.position.y
        distance = math.hypot(dx, dy)

        self.get_logger().info(
            f"Final pose: x={self.latest_pose.position.x:.3f}, y={self.latest_pose.position.y:.3f}"
        )
        self.get_logger().info(
            f"Displacement: dx={dx:.3f}, dy={dy:.3f}, total={distance:.3f} m"
        )

        if distance >= self.expected_min_distance:
            self.get_logger().info(
                f"PASS: Robot moved {distance:.3f} m (>= {self.expected_min_distance} m)"
            )
            return True
        else:
            self.get_logger().error(
                f"FAIL: Robot moved only {distance:.3f} m (< {self.expected_min_distance} m)"
            )
            return False

    def run(self) -> bool:
        if not self.wait_for_topics():
            return False
        if not self.wait_for_odom():
            return False

        # Brief pause to ensure robot is ready
        time.sleep(1.0)

        self.drive_forward()

        self.get_logger().info(
            f"Waiting {self.settle_duration}s for robot to settle ..."
        )
        time.sleep(self.settle_duration)

        self.test_passed = self.evaluate()
        self.test_done = True
        return self.test_passed


def main(args=None):
    rclpy.init(args=args)
    node = RobotMovementTest()

    # Spin in background so callbacks work while we run the test sequence
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    try:
        passed = node.run()
    except Exception as e:
        node.get_logger().fatal(f"Test crashed: {e}")
        passed = False
    finally:
        node.destroy_node()
        rclpy.shutdown()

    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
