"""
Standalone IMU Data Logger Runner.

Usage:
    python run_imu_logger.py --duration 10 --rate 50 --out logs/my_experiment.csv
    python run_imu_logger.py --rate 100
"""

import argparse
import sys
import time
from pathlib import Path

# Ensure local code directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from imu.driver import MicroStrain3DMGX3Driver
from imu.logger import IMULogger


def main():
    parser = argparse.ArgumentParser(description="Log LORD MicroStrain 3DM-GX3-25 IMU Data to CSV / NPZ")
    parser.add_argument("--port", type=str, default=None, help="Serial port (default: auto-detect)")
    parser.add_argument("--rate", type=int, default=50, help="Sampling frequency in Hz (default: 50)")
    parser.add_argument("--duration", type=float, default=0.0, help="Recording duration in seconds (0 = run until Ctrl+C)")
    parser.add_argument("--out", type=str, default=None, help="Output CSV path (default: logs/imu_log_TIMESTAMP.csv)")
    parser.add_argument("--npz", action="store_true", help="Also save compressed NumPy (.npz) file when finished")
    args = parser.parse_args()

    print("==================================================")
    print(" LORD MicroStrain 3DM-GX3-25 Data Logger")
    print("==================================================")

    driver = MicroStrain3DMGX3Driver(port=args.port)
    try:
        driver.connect()
    except Exception as e:
        print(f"Connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Connected to: {driver.port}")
    print(f"Device: {driver.device_info}")

    logger = IMULogger(driver=driver)
    logger.start(output_path=args.out)
    print(f"Logging to: {logger.output_path}")

    driver.start_streaming(rate_hz=args.rate)
    print(f"Streaming started at {args.rate} Hz.")
    print("Press Ctrl+C to stop logging anytime.\n")

    t_start = time.time()
    try:
        while True:
            elapsed = time.time() - t_start
            rate = logger.current_rate_hz
            count = logger.sample_count
            latest = driver.get_latest_data()
            r_str = f"R:{latest.euler_deg[0]:+5.1f} P:{latest.euler_deg[1]:+5.1f} Y:{latest.euler_deg[2]:+5.1f}" if latest else ""

            sys.stdout.write(f"\rLogging [{elapsed:5.1f}s] Samples: {count:<6} Rate: {rate:4.1f} Hz | {r_str}  ")
            sys.stdout.flush()

            if args.duration > 0 and elapsed >= args.duration:
                print(f"\nCompleted target duration ({args.duration}s).")
                break

            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nLogging stopped by user.")
    finally:
        driver.stop_streaming()
        driver.disconnect()
        csv_path = logger.stop()
        print(f"\n[+] Successfully saved CSV: {csv_path} ({logger.sample_count} samples)")

        if args.npz:
            npz_path = logger.save_npz()
            print(f"[+] Successfully saved NPZ: {npz_path}")


if __name__ == "__main__":
    main()
