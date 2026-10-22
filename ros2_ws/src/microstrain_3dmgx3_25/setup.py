from setuptools import find_packages, setup

package_name = "microstrain_3dmgx3_25"

setup(
    name=package_name,
    version="1.0.0",
    packages=find_packages(),
    data_files=[
        # Register package with ament index
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools", "pyserial"],
    zip_safe=True,
    maintainer="User",
    maintainer_email="user@todo.todo",
    description="ROS 2 Humble driver and publisher node for LORD MicroStrain 3DM-GX3-25",
    license="MIT",
    entry_points={
        "console_scripts": [
            # Main node entry point
            "microstrain_node = microstrain_3dmgx3_25.microstrain_node:main",
        ],
    },
)
