"""
High-performance timestamped Data Logger for MicroStrain IMU / AHRS.

Supports:
- Streaming to CSV with buffered writes
- Exporting to NumPy (.npz) and Pandas DataFrame
- Computing live sample rate and statistics
"""

import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .driver import IMUSample, MicroStrain3DMGX3Driver


CSV_HEADER = [
    "timestamp_s",
    "dt_s",
    "roll_deg",
    "pitch_deg",
    "yaw_deg",
    "roll_rad",
    "pitch_rad",
    "yaw_rad",
    "quat_w",
    "quat_x",
    "quat_y",
    "quat_z",
    "accel_x_g",
    "accel_y_g",
    "accel_z_g",
    "accel_x_mps2",
    "accel_y_mps2",
    "accel_z_mps2",
    "gyro_x_degps",
    "gyro_y_degps",
    "gyro_z_degps",
    "gyro_x_radps",
    "gyro_y_radps",
    "gyro_z_radps",
    "mag_x_gauss",
    "mag_y_gauss",
    "mag_z_gauss",
    "mag_x_tesla",
    "mag_y_tesla",
    "mag_z_tesla",
]


class IMULogger:
    """
    Manages writing timestamped IMU records to CSV and NumPy formats.
    """

    def __init__(
        self,
        output_path: Optional[str] = None,
        driver: Optional[MicroStrain3DMGX3Driver] = None,
        flush_interval_sec: float = 1.0,
    ):
        self.output_path = output_path
        self.driver = driver
        self.flush_interval_sec = flush_interval_sec

        self._file = None
        self._writer = None
        self._is_logging = False
        self._sample_count = 0
        self._start_time: Optional[float] = None
        self._last_time: Optional[float] = None
        self._last_flush: float = 0.0

        # Memory buffer if export to dataframe/npz is needed
        self._memory_samples: List[IMUSample] = []
        self._store_in_memory = True

        if self.driver:
            self.attach(self.driver)

    def attach(self, driver: MicroStrain3DMGX3Driver):
        """Attaches logger to driver callback stream."""
        self.driver = driver
        self.driver.add_callback(self.log_sample)

    def detach(self):
        """Detaches logger from driver."""
        if self.driver:
            self.driver.remove_callback(self.log_sample)

    def _resolve_output_path(self) -> Path:
        if self.output_path:
            p = Path(self.output_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            return p

        # Default to sensor's experiments/logs directory
        sensor_dir = Path(__file__).resolve().parent.parent.parent
        exp_logs = sensor_dir / "experiments" / "logs"
        if exp_logs.parent.exists():
            exp_logs.mkdir(parents=True, exist_ok=True)
            logs_dir = exp_logs
        else:
            logs_dir = Path("logs")
            logs_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        return logs_dir / f"imu_log_{timestamp_str}.csv"

    def start(self, output_path: Optional[str] = None):
        """Opens log file and begins writing incoming samples."""
        if self._is_logging:
            return

        if output_path:
            self.output_path = output_path

        target_file = self._resolve_output_path()
        self.output_path = str(target_file)

        self._file = open(target_file, mode="w", newline="", buffering=1024 * 64)
        self._writer = csv.writer(self._file)
        self._writer.writerow(CSV_HEADER)

        self._sample_count = 0
        self._start_time = time.time()
        self._last_time = None
        self._last_flush = time.time()
        self._memory_samples.clear()
        self._is_logging = True

    def stop(self) -> str:
        """Stops logging and closes file handle."""
        self._is_logging = False
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None
            self._writer = None
        return self.output_path or ""

    def log_sample(self, sample: IMUSample):
        """Logs a single sample to the open CSV file."""
        if not self._is_logging or not self._writer:
            return

        now = sample.timestamp
        dt = (now - self._last_time) if self._last_time is not None else 0.0
        self._last_time = now

        row = [
            f"{sample.timestamp:.6f}",
            f"{dt:.6f}",
            f"{sample.euler_deg[0]:.4f}",
            f"{sample.euler_deg[1]:.4f}",
            f"{sample.euler_deg[2]:.4f}",
            f"{sample.euler_rad[0]:.6f}",
            f"{sample.euler_rad[1]:.6f}",
            f"{sample.euler_rad[2]:.6f}",
            f"{sample.quat_wxyz[0]:.6f}",
            f"{sample.quat_wxyz[1]:.6f}",
            f"{sample.quat_wxyz[2]:.6f}",
            f"{sample.quat_wxyz[3]:.6f}",
            f"{sample.accel_g[0]:.6f}",
            f"{sample.accel_g[1]:.6f}",
            f"{sample.accel_g[2]:.6f}",
            f"{sample.accel_mps2[0]:.6f}",
            f"{sample.accel_mps2[1]:.6f}",
            f"{sample.accel_mps2[2]:.6f}",
            f"{sample.gyro_degps[0]:.4f}",
            f"{sample.gyro_degps[1]:.4f}",
            f"{sample.gyro_degps[2]:.4f}",
            f"{sample.gyro_radps[0]:.6f}",
            f"{sample.gyro_radps[1]:.6f}",
            f"{sample.gyro_radps[2]:.6f}",
            f"{sample.mag_gauss[0]:.6f}",
            f"{sample.mag_gauss[1]:.6f}",
            f"{sample.mag_gauss[2]:.6f}",
            f"{sample.mag_tesla[0]:.8e}",
            f"{sample.mag_tesla[1]:.8e}",
            f"{sample.mag_tesla[2]:.8e}",
        ]
        self._writer.writerow(row)
        self._sample_count += 1

        if self._store_in_memory:
            self._memory_samples.append(sample)

        # Periodic flush
        if now - self._last_flush >= self.flush_interval_sec:
            self._file.flush()
            self._last_flush = now

    @property
    def is_logging(self) -> bool:
        return self._is_logging

    @property
    def sample_count(self) -> int:
        return self._sample_count

    @property
    def elapsed_time(self) -> float:
        if not self._start_time:
            return 0.0
        return time.time() - self._start_time

    @property
    def current_rate_hz(self) -> float:
        elapsed = self.elapsed_time
        if elapsed > 0 and self._sample_count > 0:
            return self._sample_count / elapsed
        return 0.0

    def save_npz(self, npz_path: Optional[str] = None) -> str:
        """Saves recorded memory samples to compressed NumPy archive (.npz)."""
        import numpy as np

        if not self._memory_samples:
            raise ValueError("No samples in memory to save.")

        if not npz_path:
            csv_p = Path(self.output_path or "logs/imu_log.csv")
            npz_path = str(csv_p.with_suffix(".npz"))

        n = len(self._memory_samples)
        timestamps = np.zeros(n, dtype=np.float64)
        accel_g = np.zeros((n, 3), dtype=np.float32)
        accel_mps2 = np.zeros((n, 3), dtype=np.float32)
        gyro_radps = np.zeros((n, 3), dtype=np.float32)
        gyro_degps = np.zeros((n, 3), dtype=np.float32)
        euler_deg = np.zeros((n, 3), dtype=np.float32)
        quat_wxyz = np.zeros((n, 4), dtype=np.float32)
        mag_gauss = np.zeros((n, 3), dtype=np.float32)

        for i, s in enumerate(self._memory_samples):
            timestamps[i] = s.timestamp
            accel_g[i] = s.accel_g
            accel_mps2[i] = s.accel_mps2
            gyro_radps[i] = s.gyro_radps
            gyro_degps[i] = s.gyro_degps
            euler_deg[i] = s.euler_deg
            quat_wxyz[i] = s.quat_wxyz
            mag_gauss[i] = s.mag_gauss

        np.savez_compressed(
            npz_path,
            timestamps=timestamps,
            accel_g=accel_g,
            accel_mps2=accel_mps2,
            gyro_radps=gyro_radps,
            gyro_degps=gyro_degps,
            euler_deg=euler_deg,
            quat_wxyz=quat_wxyz,
            mag_gauss=mag_gauss,
        )
        return npz_path

    def to_dataframe(self):
        """Converts memory samples to a Pandas DataFrame."""
        import pandas as pd

        if self.output_path and os.path.exists(self.output_path):
            return pd.read_csv(self.output_path)

        data = []
        for s in self._memory_samples:
            data.append({
                "timestamp_s": s.timestamp,
                "roll_deg": s.euler_deg[0],
                "pitch_deg": s.euler_deg[1],
                "yaw_deg": s.euler_deg[2],
                "accel_x_g": s.accel_g[0],
                "accel_y_g": s.accel_g[1],
                "accel_z_g": s.accel_g[2],
                "gyro_x_degps": s.gyro_degps[0],
                "gyro_y_degps": s.gyro_degps[1],
                "gyro_z_degps": s.gyro_degps[2],
                "quat_w": s.quat_wxyz[0],
                "quat_x": s.quat_wxyz[1],
                "quat_y": s.quat_wxyz[2],
                "quat_z": s.quat_wxyz[3],
            })
        return pd.DataFrame(data)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
