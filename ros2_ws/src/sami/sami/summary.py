"""Compact text for ROS messages, including large sensor payloads."""

from array import array


def summarize_message(message):
    fields = []
    for name in message.get_fields_and_field_types():
        value = getattr(message, name)
        if isinstance(value, (bytes, bytearray)) or (
            isinstance(value, array) and value.typecode == 'B'
        ):
            detail = f'{len(value)} bytes'
        elif isinstance(value, (list, tuple, array)) and len(value) > 8:
            detail = f'{list(value[:3])} ... ({len(value)} values)'
        else:
            detail = str(value).replace('\n', ' ')[:160]
        fields.append(f'{name}={detail}')
    return ', '.join(fields)
