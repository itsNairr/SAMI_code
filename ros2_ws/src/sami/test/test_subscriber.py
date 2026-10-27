from array import array

from sami.summary import summarize_message


class Sample:
    data = array('B', range(256))
    ranges = [0.1] * 100
    distance = 1.25

    def get_fields_and_field_types(self):
        return {'data': 'uint8[]', 'ranges': 'float[]', 'distance': 'float'}


def test_summary_keeps_large_payloads_compact():
    summary = summarize_message(Sample())
    assert 'data=256 bytes' in summary
    assert 'ranges=[0.1, 0.1, 0.1] ... (100 values)' in summary
    assert 'distance=1.25' in summary


def test_sensor_subscriber_starts():
    import pytest

    rclpy = pytest.importorskip('rclpy')
    from sami.sensor_subscriber import SamiSensorSubscriber

    rclpy.init()
    node = None
    try:
        node = SamiSensorSubscriber()
        assert node.get_name() == 'sami_sensor_subscriber'
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
