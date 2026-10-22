"""
Quick CLI Runner for MicroStrain 3DM-GX3-25 live streaming.
"""

import sys
from pathlib import Path

# Ensure local code directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from imu.stream_cli import stream_cli

if __name__ == "__main__":
    stream_cli()
