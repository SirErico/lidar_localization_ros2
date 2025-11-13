import os

import launch
import launch.actions
import launch.events

import launch_ros
import launch_ros.actions
import launch_ros.events

from launch import LaunchDescription
from launch_ros.actions import LifecycleNode
from launch_ros.actions import Node

import lifecycle_msgs.msg

from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    ld = launch.LaunchDescription()

    # Note: Your robot should already publish these transforms
    # Only add these if they're missing from your robot's URDF/TF tree
    # lidar_tf = launch_ros.actions.Node(
    #     name='lidar_tf',
    #     package='tf2_ros',
    #     executable='static_transform_publisher',
    #     arguments=['0','0','0','0','0','0','1','j100_0000/base_link','j100_0000/velodyne'],
    #     remappings=[('/tf','/j100_0000/tf'),
    #         ('/tf_static','/j100_0000/tf_static')],
    #     )

    # imu_tf = launch_ros.actions.Node(
    #     name='imu_tf',
    #     package='tf2_ros',
    #     executable='static_transform_publisher',
    #     arguments=['0','0','0','0','0','0','1','j100_0000/base_link','j100_0000/imu_link'],
    #     remappings=[('/tf','/j100_0000/tf'),
    #         ('/tf_static','/j100_0000/tf_static')],
    #     )

    localization_param_dir = launch.substitutions.LaunchConfiguration(
        'localization_param_dir',
        default=os.path.join(
            get_package_share_directory('pcl_localization_ros2'),
            'param',
            'localization.yaml'))

    pcl_localization = launch_ros.actions.LifecycleNode(
        name='pcl_localization',
        namespace='',
        package='pcl_localization_ros2',
        executable='pcl_localization_node',
        parameters=[localization_param_dir],
        remappings=[
            ('velodyne_points', '/j100_0000/sensors/lidar3d_0/points'),  # Point cloud input
            ('imu', '/j100_0000/sensors/imu_0/data'),
            ('odom', '/j100_0000/platform/odom'),
            ('initialpose', '/j100_0000/initialpose'),
            ('/tf', '/j100_0000/tf'),
            ('/tf_static', '/j100_0000/tf_static'),     
        ],
        output='screen')

    to_inactive = launch.actions.EmitEvent(
        event=launch_ros.events.lifecycle.ChangeState(
            lifecycle_node_matcher=launch.events.matches_action(pcl_localization),
            transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
        )
    )

    from_unconfigured_to_inactive = launch.actions.RegisterEventHandler(
        launch_ros.event_handlers.OnStateTransition(
            target_lifecycle_node=pcl_localization,
            goal_state='unconfigured',
            entities=[
                launch.actions.LogInfo(msg="-- Unconfigured --"),
                launch.actions.EmitEvent(event=launch_ros.events.lifecycle.ChangeState(
                    lifecycle_node_matcher=launch.events.matches_action(pcl_localization),
                    transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
                )),
            ],
        )
    )

    from_inactive_to_active = launch.actions.RegisterEventHandler(
        launch_ros.event_handlers.OnStateTransition(
            target_lifecycle_node=pcl_localization,
            start_state = 'configuring',
            goal_state='inactive',
            entities=[
                launch.actions.LogInfo(msg="-- Inactive --"),
                launch.actions.EmitEvent(event=launch_ros.events.lifecycle.ChangeState(
                    lifecycle_node_matcher=launch.events.matches_action(pcl_localization),
                    transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE,
                )),
            ],
        )
    )

    ld.add_action(from_unconfigured_to_inactive)
    ld.add_action(from_inactive_to_active)

    ld.add_action(pcl_localization)
    # ld.add_action(lidar_tf)  # Uncomment if using static transforms above
    ld.add_action(to_inactive)

    return ld