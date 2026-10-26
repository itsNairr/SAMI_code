#!/usr/bin/env bash
SIM_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source /opt/ros/humble/setup.bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:$SIM_DIR/models

ros2 launch clearpath_gz simulation.launch.py \
  setup_path:=$SIM_DIR/clearpath \
  world:=$SIM_DIR/worlds/sami_world \
  x:=0 y:=10 z:=10 \
  "$@"
