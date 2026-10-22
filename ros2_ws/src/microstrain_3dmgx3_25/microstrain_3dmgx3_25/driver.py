"""
MicroStrain 3DM-GX3-25 MIP Protocol Driver.

Implements MicroStrain Inertial Protocol (MIP) packet communication over serial:
- Auto-detection of LORD/MicroStrain USB COM ports (VID 0x199B / PID 0x3065)
- Stream configuration (decimation from 1000 Hz base clock)
- High-rate packet parsing (Accelerometer, Gyroscope, Magnetometer, Euler angles, Quaternions)
- Thread-safe streaming and callback dispatch
"""

import math
import struct
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import serial
import serial.tools.list_ports


# Standard MIP Protocol Constants
MIP_SYNC1 = 0x75
MIP_SYNC2 = 0x65

# Descriptor Sets
DESCSET_BASE_CMD = 0x01
DESCSET_3DM_CMD = 0x0C
DESCSET_AHRS_DATA = 0x80

# Base Commands
CMD_BASE_PING = 0x01
CMD_BASE_SET_TO_IDLE = 0x02
CMD_BASE_GET_DEVICE_INFO = 0x03
CMD_BASE_RESET = 0x7E

# 3DM Commands
CMD_3DM_POLL_AHRS = 0x01
CMD_3DM_GET_BASE_RATE = 0x06
CMD_3DM_AHRS_MSG_FORMAT = 0x08
CMD_3DM_STREAM_CONTROL = 0x11

# AHRS Data Field Descriptors (inside 0x80 packet)
DATA_SCALED_ACCEL = 0x04   # 3 x float32 (g)
DATA_SCALED_GYRO = 0x05    # 3 x float32 (rad/s)
DATA_SCALED_MAG = 0x06     # 3 x float32 (Gauss)
DATA_DELTA_THETA = 0x07    # 3 x float32 (rad)
DATA_DELTA_VEL = 0x08      # 3 x float32 (g*s)
DATA_ORIENT_MAT = 0x09     # 9 x float32 (3x3 row-major)
DATA_QUATERNION = 0x0A     # 4 x float32 (q0=w, q1=x, q2=y, q3=z)
DATA_EULER_ANGLES = 0x0C   # 3 x float32 (roll, pitch, yaw in rad)

GRAVITY_MPS2 = 9.80665


def calc_fletcher16(data: bytes) -> bytes:
    """Computes the 16-bit Fletcher checksum used by MIP packets."""
    sum1 = 0
    sum2 = 0
    for b in data:
        sum1 = (sum1 + b) % 256
        sum2 = (sum2 + sum1) % 256
    return bytes([sum1, sum2])


@dataclass
class DeviceInfo:
    """MicroStrain hardware and firmware information."""
    model_name: str = ""
    model_number: str = ""
    serial_number: str = ""
    lot_number: str = ""
    device_options: str = ""
    firmware_version: int = 0

    def __str__(self) -> str:
        return (
            f"Model: {self.model_name} (No. {self.model_number}), "
            f"Serial: {self.serial_number}, "
            f"FW: {self.firmware_version}, "
            f"Options: {self.device_options}"
        )


@dataclass
class IMUSample:
    """
    Parsed timestamped IMU measurement packet.
    Units:
      - accel_g: (X, Y, Z) in g
      - accel_mps2: (X, Y, Z) in m/s^2
      - gyro_radps: (X, Y, Z) in rad/s
      - gyro_degps: (X, Y, Z) in deg/s
      - mag_gauss: (X, Y, Z) in Gauss
      - mag_tesla: (X, Y, Z) in Tesla
      - euler_rad: (roll, pitch, yaw) in radians
      - euler_deg: (roll, pitch, yaw) in degrees
      - quat_wxyz: (w, x, y, z) unit quaternion
      - quat_xyzw: (x, y, z, w) for ROS geometry_msgs/Quaternion
    """
    timestamp: float = 0.0
    accel_g: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    accel_mps2: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    gyro_radps: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    gyro_degps: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    mag_gauss: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    mag_tesla: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    euler_rad: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    euler_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    quat_wxyz: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    quat_xyzw: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    raw_packet: bytes = field(default=b"", repr=False)

    def to_ros_dict(self, frame_id: str = "imu_link") -> Dict:
        """
        Returns a dictionary structure matching standard ROS/ROS2 sensor_msgs/Imu
        and sensor_msgs/MagneticField messages.
        """
        secs = int(self.timestamp)
        nsecs = int((self.timestamp - secs) * 1e9)
        return {
            "header": {
                "stamp": {"sec": secs, "nanosec": nsecs},
                "frame_id": frame_id,
            },
            "orientation": {
                "x": self.quat_xyzw[0],
                "y": self.quat_xyzw[1],
                "z": self.quat_xyzw[2],
                "w": self.quat_xyzw[3],
            },
            "angular_velocity": {
                "x": self.gyro_radps[0],
                "y": self.gyro_radps[1],
                "z": self.gyro_radps[2],
            },
            "linear_acceleration": {
                "x": self.accel_mps2[0],
                "y": self.accel_mps2[1],
                "z": self.accel_mps2[2],
            },
            "magnetic_field": {
                "x": self.mag_tesla[0],
                "y": self.mag_tesla[1],
                "z": self.mag_tesla[2],
            },
            "euler_degrees": {
                "roll": self.euler_deg[0],
                "pitch": self.euler_deg[1],
                "yaw": self.euler_deg[2],
            },
        }


class MicroStrain3DMGX3Driver:
    """
    High-performance serial driver for LORD MicroStrain 3DM-GX3-25.
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        timeout: float = 1.0,
        auto_reconnect: bool = True,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect

        self._ser: Optional[serial.Serial] = None
        self._lock = threading.Lock()
        self._running = False
        self._rx_thread: Optional[threading.Thread] = None

        self._latest_sample: Optional[IMUSample] = None
        self._sample_lock = threading.Lock()
        self._callbacks: List[Callable[[IMUSample], None]] = []

        self.device_info = DeviceInfo()
        self.base_rate_hz: int = 1000

    @staticmethod
    def find_microstrain_port() -> Optional[str]:
        """Scans system serial ports for LORD MicroStrain devices."""
        ports = list(serial.tools.list_ports.comports())
        # First priority: matching VID 0x199B
        for p in ports:
            if p.vid == 0x199B:
                return p.device
        # Second priority: device description matching Microstrain
        for p in ports:
            desc = (p.description or "").lower()
            mfg = (p.manufacturer or "").lower()
            if "microstrain" in desc or "microstrain" in mfg or "lord" in desc:
                return p.device
        # Third priority: COM4 if available
        for p in ports:
            if p.device.upper() == "COM4":
                return p.device
        return None

    def connect(self) -> bool:
        """Opens serial connection and initializes communications."""
        with self._lock:
            if self._ser and self._ser.is_open:
                return True

            target_port = self.port or self.find_microstrain_port()
            if not target_port:
                raise IOError("No MicroStrain 3DM-GX3-25 port detected.")
            self.port = target_port

            self._ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=self.timeout,
            )
            self._ser.reset_input_buffer()
            self._ser.reset_output_buffer()

        # Verify device communication
        if not self.ping():
            # If device was streaming, put to idle and try ping again
            self.set_to_idle()
            time.sleep(0.05)
            if not self.ping():
                raise IOError(f"Device at {self.port} did not respond to MIP ping.")

        self.get_device_info()
        self.get_base_rate()
        return True

    def disconnect(self):
        """Stops streaming and closes the serial port."""
        self.stop_streaming()
        with self._lock:
            if self._ser and self._ser.is_open:
                try:
                    self._send_packet_raw(DESCSET_BASE_CMD, bytes([0x02, CMD_BASE_SET_TO_IDLE]))
                except Exception:
                    pass
                self._ser.close()
            self._ser = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    # --- Low-Level MIP Packet Operations ---

    def _build_packet(self, desc_set: int, payload: bytes) -> bytes:
        header = bytes([MIP_SYNC1, MIP_SYNC2, desc_set, len(payload)])
        full = header + payload
        return full + calc_fletcher16(full)

    def _send_packet_raw(self, desc_set: int, payload: bytes):
        if not self._ser or not self._ser.is_open:
            raise IOError("Serial port is not open.")
        pkt = self._build_packet(desc_set, payload)
        self._ser.write(pkt)

    def _send_command(
        self,
        desc_set: int,
        field_desc: int,
        field_data: bytes = b"",
        expected_resp_desc: Optional[int] = None,
        timeout: float = 0.5,
    ) -> Tuple[bool, bytes]:
        """
        Sends a command packet and waits for matching ACK/NACK or response.
        """
        with self._lock:
            if not self._ser or not self._ser.is_open:
                raise IOError("Serial port not open.")

            field_len = 2 + len(field_data)
            payload = bytes([field_len, field_desc]) + field_data
            pkt = self._build_packet(desc_set, payload)

            self._ser.reset_input_buffer()
            self._ser.write(pkt)

            start = time.time()
            buffer = bytearray()
            while time.time() - start < timeout:
                n = self._ser.in_waiting
                if n > 0:
                    buffer.extend(self._ser.read(n))
                else:
                    time.sleep(0.005)

                # Search buffer for MIP packet
                while len(buffer) >= 6:
                    if buffer[0] != MIP_SYNC1 or buffer[1] != MIP_SYNC2:
                        buffer.pop(0)
                        continue

                    p_desc_set = buffer[2]
                    p_len = buffer[3]
                    total_len = 4 + p_len + 2

                    if len(buffer) < total_len:
                        break  # Need more bytes

                    packet_bytes = bytes(buffer[:total_len])
                    buffer = buffer[total_len:]

                    # Verify checksum
                    calc_ck = calc_fletcher16(packet_bytes[:-2])
                    if packet_bytes[-2:] != calc_ck:
                        continue  # Checksum mismatch

                    # Check response
                    if p_desc_set == desc_set:
                        payload_data = packet_bytes[4:-2]
                        # Parse fields looking for ACK or expected field
                        idx = 0
                        while idx < len(payload_data):
                            f_len = payload_data[idx]
                            f_desc = payload_data[idx + 1]
                            f_val = payload_data[idx + 2 : idx + f_len]

                            if f_desc == 0xF1 and len(f_val) >= 2:
                                cmd_echo = f_val[0]
                                err_code = f_val[1]
                                if cmd_echo == field_desc and err_code == 0x00:
                                    return True, payload_data
                                elif cmd_echo == field_desc:
                                    return False, payload_data
                            idx += f_len

                        return True, payload_data

            return False, b""

    # --- Device Commands ---

    def ping(self) -> bool:
        """Pings device to confirm MIP connectivity."""
        success, _ = self._send_command(
            desc_set=DESCSET_BASE_CMD,
            field_desc=CMD_BASE_PING,
            timeout=0.3,
        )
        return success

    def set_to_idle(self) -> bool:
        """Halts active streaming and returns device to idle."""
        success, _ = self._send_command(
            desc_set=DESCSET_BASE_CMD,
            field_desc=CMD_BASE_SET_TO_IDLE,
            timeout=0.3,
        )
        return success

    def get_device_info(self) -> DeviceInfo:
        """Queries model, serial, options, and firmware from device."""
        success, payload = self._send_command(
            desc_set=DESCSET_BASE_CMD,
            field_desc=CMD_BASE_GET_DEVICE_INFO,
            timeout=0.5,
        )
        if success and len(payload) >= 8:
            idx = 0
            while idx < len(payload):
                flen = payload[idx]
                fdesc = payload[idx + 1]
                fdata = payload[idx + 2 : idx + flen]
                if fdesc == 0x81 and len(fdata) >= 68:
                    fw = int.from_bytes(fdata[0:2], "big")
                    model = fdata[2:18].decode("ascii", errors="ignore").strip("\x00").strip()
                    model_num = fdata[18:34].decode("ascii", errors="ignore").strip("\x00").strip()
                    serial_num = fdata[34:50].decode("ascii", errors="ignore").strip("\x00").strip()
                    lot_num = fdata[50:66].decode("ascii", errors="ignore").strip("\x00").strip()
                    opts = fdata[66:82].decode("ascii", errors="ignore").strip("\x00").strip()
                    self.device_info = DeviceInfo(
                        model_name=model or "3DM-GX3-25",
                        model_number=model_num,
                        serial_number=serial_num,
                        lot_number=lot_num,
                        device_options=opts,
                        firmware_version=fw,
                    )
                idx += flen
        return self.device_info

    def get_base_rate(self) -> int:
        """Queries device base clock rate (typically 1000 Hz)."""
        success, payload = self._send_command(
            desc_set=DESCSET_3DM_CMD,
            field_desc=CMD_3DM_GET_BASE_RATE,
            timeout=0.5,
        )
        if success and len(payload) >= 8:
            idx = 0
            while idx < len(payload):
                flen = payload[idx]
                fdesc = payload[idx + 1]
                fdata = payload[idx + 2 : idx + flen]
                if fdesc == 0x83 and len(fdata) >= 2:
                    self.base_rate_hz = struct.unpack(">H", fdata[:2])[0]
                    return self.base_rate_hz
                idx += flen
        return self.base_rate_hz

    def configure_stream(
        self,
        rate_hz: int = 50,
        enable_accel: bool = True,
        enable_gyro: bool = True,
        enable_mag: bool = True,
        enable_euler: bool = True,
        enable_quat: bool = True,
    ) -> bool:
        """
        Configures AHRS message format with specified sampling frequency.
        """
        base_rate = self.base_rate_hz or 1000
        rate_hz = max(1, min(rate_hz, 500))
        decimation = max(1, base_rate // rate_hz)

        channels = []
        if enable_accel:
            channels.append(DATA_SCALED_ACCEL)
        if enable_gyro:
            channels.append(DATA_SCALED_GYRO)
        if enable_mag:
            channels.append(DATA_SCALED_MAG)
        if enable_euler:
            channels.append(DATA_EULER_ANGLES)
        if enable_quat:
            channels.append(DATA_QUATERNION)

        # Field payload: Function=0x01 (Apply), Count=N, [desc, decimation_u16]...
        field_payload = bytearray([0x01, len(channels)])
        for ch in channels:
            field_payload.append(ch)
            field_payload.extend(struct.pack(">H", decimation))

        success, _ = self._send_command(
            desc_set=DESCSET_3DM_CMD,
            field_desc=CMD_3DM_AHRS_MSG_FORMAT,
            field_data=bytes(field_payload),
            timeout=0.5,
        )
        return success

    def start_streaming(self, rate_hz: int = 50) -> bool:
        """
        Configures stream and launches background receiver thread.
        """
        if self._running:
            return True

        if not self._ser or not self._ser.is_open:
            self.connect()

        self.configure_stream(rate_hz=rate_hz)

        # Enable stream 0x01 (AHRS)
        # Function=0x01, Stream=0x01, Enable=0x01
        success, _ = self._send_command(
            desc_set=DESCSET_3DM_CMD,
            field_desc=CMD_3DM_STREAM_CONTROL,
            field_data=bytes([0x01, 0x01, 0x01]),
            timeout=0.5,
        )
        if not success:
            raise IOError("Failed to enable continuous data stream.")

        self._running = True
        self._rx_thread = threading.Thread(
            target=self._stream_receiver_loop,
            daemon=True,
            name="MicroStrain-Rx",
        )
        self._rx_thread.start()
        return True

    def stop_streaming(self):
        """Stops background receiver thread and disables stream on sensor."""
        self._running = False
        if self._rx_thread and self._rx_thread.is_alive():
            self._rx_thread.join(timeout=1.0)
            self._rx_thread = None

        if self._ser and self._ser.is_open:
            try:
                # Send disable stream: Function=0x01, Stream=0x01, Enable=0x00
                pkt = self._build_packet(
                    DESCSET_3DM_CMD,
                    bytes([0x05, CMD_3DM_STREAM_CONTROL, 0x01, 0x01, 0x00]),
                )
                self._ser.write(pkt)
                time.sleep(0.05)
                self._ser.reset_input_buffer()
            except Exception:
                pass

    def add_callback(self, callback: Callable[[IMUSample], None]):
        """Registers a callback function to be called on each new IMUSample."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[IMUSample], None]):
        """Removes a registered callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def get_latest_data(self) -> Optional[IMUSample]:
        """Returns the most recent parsed IMU sample in a thread-safe manner."""
        with self._sample_lock:
            return self._latest_sample

    # --- Receiver Loop & Packet Parser ---

    def _stream_receiver_loop(self):
        """Dedicated background loop that ingests bytes and parses AHRS packets."""
        buffer = bytearray()
        while self._running:
            try:
                if not self._ser or not self._ser.is_open:
                    if self.auto_reconnect:
                        time.sleep(0.5)
                        try:
                            self.connect()
                        except Exception:
                            continue
                    else:
                        break

                n = self._ser.in_waiting
                if n > 0:
                    buffer.extend(self._ser.read(n))
                else:
                    time.sleep(0.001)
                    continue

                # Process packets from buffer
                while len(buffer) >= 6:
                    if buffer[0] != MIP_SYNC1 or buffer[1] != MIP_SYNC2:
                        buffer.pop(0)
                        continue

                    desc_set = buffer[2]
                    payload_len = buffer[3]
                    total_len = 4 + payload_len + 2

                    if len(buffer) < total_len:
                        break  # Wait for remaining bytes of this packet

                    packet_bytes = bytes(buffer[:total_len])
                    buffer = buffer[total_len:]

                    # Check Fletcher-16
                    if packet_bytes[-2:] != calc_fletcher16(packet_bytes[:-2]):
                        continue

                    if desc_set == DESCSET_AHRS_DATA:
                        sample = self._parse_ahrs_packet(packet_bytes)
                        if sample:
                            with self._sample_lock:
                                self._latest_sample = sample
                            for cb in self._callbacks:
                                try:
                                    cb(sample)
                                except Exception:
                                    pass

            except (serial.SerialException, IOError):
                if not self._running:
                    break
                time.sleep(0.1)
            except Exception:
                pass

    def _parse_ahrs_packet(self, packet: bytes) -> Optional[IMUSample]:
        """Unpacks an AHRS (0x80) data packet into an IMUSample dataclass."""
        ts = time.time()
        payload = packet[4:-2]

        ax, ay, az = 0.0, 0.0, 0.0
        gx, gy, gz = 0.0, 0.0, 0.0
        mx, my, mz = 0.0, 0.0, 0.0
        roll, pitch, yaw = 0.0, 0.0, 0.0
        q0, q1, q2, q3 = 1.0, 0.0, 0.0, 0.0

        idx = 0
        while idx < len(payload):
            flen = payload[idx]
            if flen < 2 or idx + flen > len(payload):
                break
            fdesc = payload[idx + 1]
            fdata = payload[idx + 2 : idx + flen]

            if fdesc == DATA_SCALED_ACCEL and len(fdata) >= 12:
                ax, ay, az = struct.unpack(">fff", fdata[:12])
            elif fdesc == DATA_SCALED_GYRO and len(fdata) >= 12:
                gx, gy, gz = struct.unpack(">fff", fdata[:12])
            elif fdesc == DATA_SCALED_MAG and len(fdata) >= 12:
                mx, my, mz = struct.unpack(">fff", fdata[:12])
            elif fdesc == DATA_EULER_ANGLES and len(fdata) >= 12:
                roll, pitch, yaw = struct.unpack(">fff", fdata[:12])
            elif fdesc == DATA_QUATERNION and len(fdata) >= 16:
                q0, q1, q2, q3 = struct.unpack(">ffff", fdata[:16])

            idx += flen

        return IMUSample(
            timestamp=ts,
            accel_g=(ax, ay, az),
            accel_mps2=(ax * GRAVITY_MPS2, ay * GRAVITY_MPS2, az * GRAVITY_MPS2),
            gyro_radps=(gx, gy, gz),
            gyro_degps=(math.degrees(gx), math.degrees(gy), math.degrees(gz)),
            mag_gauss=(mx, my, mz),
            mag_tesla=(mx * 1e-4, my * 1e-4, mz * 1e-4),
            euler_rad=(roll, pitch, yaw),
            euler_deg=(math.degrees(roll), math.degrees(pitch), math.degrees(yaw)),
            quat_wxyz=(q0, q1, q2, q3),
            quat_xyzw=(q1, q2, q3, q0),
            raw_packet=packet,
        )
