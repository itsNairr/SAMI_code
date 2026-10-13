"""
CLI live terminal streamer for MicroStrain 3DM-GX3-25.
"""

import argparse
import sys
import time
from imu.driver import MicroStrain3DMGX3Driver


def stream_cli():
    parser = argparse.ArgumentParser(description="Live CLI Stream for MicroStrain 3DM-GX3-25")
    parser.add_argument("--port", type=str, default=None, help="Serial port (e.g. COM4). Default: auto-detect")
    parser.add_argument("--rate", type=int, default=50, help="Streaming rate in Hz (default: 50)")
    args = parser.parse_args()

    print(f"Connecting (requested port: {args.port or 'auto-detect'})...")

    driver = MicroStrain3DMGX3Driver(port=args.port)
    try:
        driver.connect()
    except Exception as e:
        print(f"Error connecting to sensor: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Connected to: {driver.port}")
    print(f"Device: {driver.device_info.model_name} (S/N: {driver.device_info.serial_number})")
    print(f"Configured Rate: {args.rate} Hz")
    print("Press Ctrl+C to stop streaming.\n")

    driver.start_streaming(rate_hz=args.rate)

    count = 0
    t0 = time.time()
    try:
        while True:
            sample = driver.get_latest_data()
            if sample:
                count += 1
                fps = count / max(0.001, time.time() - t0)
                r, p, y = sample.euler_deg
                ax, ay, az = sample.accel_g
                gx, gy, gz = sample.gyro_degps
                qw, qx, qy, qz = sample.quat_wxyz

                output = (
                    f"\r[Rate: {fps:4.1f} Hz] "
                    f"Euler(deg): R={r:+6.1f} P={p:+6.1f} Y={y:+6.1f} | "
                    f"Accel(g): X={ax:+5.2f} Y={ay:+5.2f} Z={az:+5.2f} | "
                    f"Gyro(d/s): X={gx:+5.1f} Y={gy:+5.1f} Z={gz:+5.1f}"
                )
                sys.stdout.write(output)
                sys.stdout.flush()
            time.sleep(0.04)
    except KeyboardInterrupt:
        print("\nStopping stream...")
    finally:
        driver.disconnect()
        print("Disconnected cleanly.")


if __name__ == "__main__":
    stream_cli()
