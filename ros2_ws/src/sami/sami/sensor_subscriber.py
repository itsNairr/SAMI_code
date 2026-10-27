"""Log compact samples of SAMI's published ROS topics."""

from functools import partial
from time import monotonic

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile, qos_profile_sensor_data
from rosidl_runtime_py.utilities import get_message

from .summary import summarize_message


class SamiSensorSubscriber(Node):
    """Subscribe to topics as their publishers appear."""

    def __init__(self):
        super().__init__('sami_sensor_subscriber')
        self._topic_subscriptions = {}
        self.last_log = {}
        self.unsupported = set()
        self.create_timer(2.0, self.discover_topics)
        self.get_logger().info('Watching for published topics')
        self.discover_topics()

    def discover_topics(self):
        for topic, types in self.get_topic_names_and_types():
            if topic in ('/rosout', '/parameter_events') or topic in self._topic_subscriptions:
                continue
            publishers = self.get_publishers_info_by_topic(topic)
            if not publishers:
                continue
            if len(types) != 1:
                self.warn_once(topic, f'expected one message type, found {types}')
                continue
            try:
                message_type = get_message(types[0])
                qos = qos_profile_sensor_data
                if all(
                    publisher.qos_profile.durability == QoSDurabilityPolicy.TRANSIENT_LOCAL
                    for publisher in publishers
                ):
                    qos = QoSProfile(
                        depth=5,
                        reliability=qos_profile_sensor_data.reliability,
                        durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
                    )
                subscription = self.create_subscription(
                    message_type,
                    topic,
                    partial(self.log_message, topic, types[0]),
                    qos,
                )
            except Exception as exc:
                self.warn_once(topic, f'cannot subscribe: {exc}')
                continue
            self._topic_subscriptions[topic] = subscription
            self.get_logger().info(f'Listening to {topic} ({types[0]})')

    def warn_once(self, topic, reason):
        if topic not in self.unsupported:
            self.get_logger().warning(f'Skipping {topic}: {reason}')
            self.unsupported.add(topic)

    def log_message(self, topic, message_type, message):
        now = monotonic()
        if now - self.last_log.get(topic, -float('inf')) < 1.0:
            return
        self.last_log[topic] = now
        self.get_logger().info(
            f'{topic} ({message_type}): {summarize_message(message)}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = SamiSensorSubscriber()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
