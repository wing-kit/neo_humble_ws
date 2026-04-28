from setuptools import setup

package_name = 'neobotix_e2e_test'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/e2e_test.launch.py',
            'launch/test_simulation.launch.py',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Test User',
    maintainer_email='test@example.com',
    description='End-to-end automated testing for Neobotix robot simulation',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'test_robot_movement = neobotix_e2e_test.test_robot_movement:main',
        ],
    },
)
