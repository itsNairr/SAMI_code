"""
Desktop 3D Orientation Visualizer for LORD MicroStrain 3DM-GX3-25.

Displays:
- Real-time 3D Box representation oriented by sensor Quaternions / Euler angles
- Body-frame coordinate axes (X=Red, Y=Green, Z=Blue)
- Live scrolling strip charts for Roll/Pitch/Yaw and Linear Acceleration
"""

import collections
import math
import sys
import time
from pathlib import Path

# Ensure local code directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from imu.driver import MicroStrain3DMGX3Driver


def quat_to_rot_matrix(qw, qx, qy, qz):
    """Converts unit quaternion (w, x, y, z) to 3x3 rotation matrix."""
    return np.array([
        [1 - 2*(qy**2 + qz**2), 2*(qx*qy - qz*qw),     2*(qx*qz + qy*qw)],
        [2*(qx*qy + qz*qw),     1 - 2*(qx**2 + qz**2), 2*(qy*qz - qx*qw)],
        [2*(qx*qz - qy*qw),     2*(qy*qz + qx*qw),     1 - 2*(qx**2 + qy**2)]
    ])


def main():
    print("Connecting to MicroStrain 3DM-GX3-25...")
    driver = MicroStrain3DMGX3Driver()
    try:
        driver.connect()
    except Exception as e:
        print(f"Failed to connect: {e}", file=sys.stderr)
        sys.exit(1)

    driver.start_streaming(rate_hz=50)
    print(f"Streaming from {driver.port}. Launching 3D Visualizer...")

    # Set up dark theme aesthetic
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(14, 7))
    fig.canvas.manager.set_window_title("MicroStrain 3DM-GX3-25 Real-Time 3D Monitor")

    # Left: 3D Attitude Box
    ax3d = fig.add_subplot(1, 2, 1, projection="3d")
    # Right top: Euler angles plot
    ax_euler = fig.add_subplot(2, 2, 2)
    # Right bottom: Accelerometer plot
    ax_accel = fig.add_subplot(2, 2, 4)

    # Box geometry centered at origin (dimensions in arb units)
    dx, dy, dz = 1.2, 0.8, 0.3
    base_vertices = np.array([
        [-dx, -dy, -dz],
        [+dx, -dy, -dz],
        [+dx, +dy, -dz],
        [-dx, +dy, -dz],
        [-dx, -dy, +dz],
        [+dx, -dy, +dz],
        [+dx, +dy, +dz],
        [-dx, +dy, +dz],
    ])
    faces_indices = [
        [0, 1, 2, 3], # bottom
        [4, 5, 6, 7], # top
        [0, 1, 5, 4], # front
        [2, 3, 7, 6], # back
        [1, 2, 6, 5], # right
        [0, 3, 7, 4], # left
    ]

    # History buffers for plots (last 100 points)
    hist_len = 100
    t_hist = collections.deque(maxlen=hist_len)
    roll_hist = collections.deque(maxlen=hist_len)
    pitch_hist = collections.deque(maxlen=hist_len)
    yaw_hist = collections.deque(maxlen=hist_len)
    ax_hist = collections.deque(maxlen=hist_len)
    ay_hist = collections.deque(maxlen=hist_len)
    az_hist = collections.deque(maxlen=hist_len)

    t0 = time.time()

    try:
        while plt.fignum_exists(fig.number):
            sample = driver.get_latest_data()
            if sample:
                now = time.time() - t0
                qw, qx, qy, qz = sample.quat_wxyz
                R = quat_to_rot_matrix(qw, qx, qy, qz)

                t_hist.append(now)
                roll_hist.append(sample.euler_deg[0])
                pitch_hist.append(sample.euler_deg[1])
                yaw_hist.append(sample.euler_deg[2])
                ax_hist.append(sample.accel_g[0])
                ay_hist.append(sample.accel_g[1])
                az_hist.append(sample.accel_g[2])

                # Rotate vertices
                rot_vertices = np.dot(base_vertices, R.T)
                faces = [[rot_vertices[j] for j in f] for f in faces_indices]

                # --- Draw 3D Box ---
                ax3d.cla()
                ax3d.set_xlim([-2, 2])
                ax3d.set_ylim([-2, 2])
                ax3d.set_zlim([-2, 2])
                ax3d.set_xlabel("X (North / Fwd)")
                ax3d.set_ylabel("Y (East / Right)")
                ax3d.set_zlabel("Z (Down / Up)")
                ax3d.set_title(
                    f"Attitude 3D View\nRoll: {sample.euler_deg[0]:+5.1f}° | "
                    f"Pitch: {sample.euler_deg[1]:+5.1f}° | "
                    f"Yaw: {sample.euler_deg[2]:+5.1f}°",
                    color="#00e5ff",
                    fontsize=11,
                    fontweight="bold"
                )

                # Add translucent 3D box
                poly = Poly3DCollection(faces, alpha=0.65, edgecolor="#00e5ff", linewidths=1.2)
                poly.set_facecolor(["#1a237e", "#29b6f6", "#0288d1", "#01579b", "#00bcd4", "#4fc3f7"])
                ax3d.add_collection3d(poly)

                # Body-frame coordinate axes
                axis_len = 1.8
                x_axis = np.dot([axis_len, 0, 0], R.T)
                y_axis = np.dot([0, axis_len, 0], R.T)
                z_axis = np.dot([0, 0, axis_len], R.T)
                ax3d.quiver(0, 0, 0, x_axis[0], x_axis[1], x_axis[2], color="#ff1744", linewidth=2.5, arrow_length_ratio=0.15)
                ax3d.quiver(0, 0, 0, y_axis[0], y_axis[1], y_axis[2], color="#00e676", linewidth=2.5, arrow_length_ratio=0.15)
                ax3d.quiver(0, 0, 0, z_axis[0], z_axis[1], z_axis[2], color="#2979ff", linewidth=2.5, arrow_length_ratio=0.15)

                # --- Draw Euler Plot ---
                ax_euler.cla()
                ax_euler.plot(t_hist, roll_hist, label=f"Roll ({sample.euler_deg[0]:+.1f}°)", color="#ff5252")
                ax_euler.plot(t_hist, pitch_hist, label=f"Pitch ({sample.euler_deg[1]:+.1f}°)", color="#69f0ae")
                ax_euler.plot(t_hist, yaw_hist, label=f"Yaw ({sample.euler_deg[2]:+.1f}°)", color="#40c4ff")
                ax_euler.set_ylabel("Angle (deg)")
                ax_euler.legend(loc="upper left", fontsize=8)
                ax_euler.grid(True, linestyle="--", alpha=0.3)
                ax_euler.set_title("Euler Angles History", fontsize=10)

                # --- Draw Accel Plot ---
                ax_accel.cla()
                ax_accel.plot(t_hist, ax_hist, label=f"Ax ({sample.accel_g[0]:+.2f}g)", color="#ff5252")
                ax_accel.plot(t_hist, ay_hist, label=f"Ay ({sample.accel_g[1]:+.2f}g)", color="#69f0ae")
                ax_accel.plot(t_hist, az_hist, label=f"Az ({sample.accel_g[2]:+.2f}g)", color="#40c4ff")
                ax_accel.set_ylabel("Accel (g)")
                ax_accel.set_xlabel("Time (s)")
                ax_accel.legend(loc="upper left", fontsize=8)
                ax_accel.grid(True, linestyle="--", alpha=0.3)
                ax_accel.set_title("Linear Acceleration History", fontsize=10)

                fig.tight_layout()
                plt.pause(0.03)
            else:
                plt.pause(0.01)

    except KeyboardInterrupt:
        pass
    finally:
        driver.disconnect()
        print("Visualizer stopped and disconnected.")


if __name__ == "__main__":
    main()
