from setuptools import find_packages, setup

package_name = 'sami_realsense_camera_forward'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='chloe',
    maintainer_email='chloe@todo.todo',
    description='Forward Intel RealSense distance and stop publisher for SAMI',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },

    entry_points={
        'console_scripts': [
            'camera = sami_realsense_camera_forward.realsense_camera_node:main',
            'avoid = sami_realsense_camera_forward.person_identify:main',
        ],
    },
)
