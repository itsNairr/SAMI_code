from glob import glob
from setuptools import find_packages, setup

package_name = 'sami'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    tests_require=['pytest'],
    zip_safe=True,
    maintainer='SAMI team',
    maintainer_email='sami@example.com',
    description='SAMI sensor subscriber and launch entry point',
    license='MIT',
    entry_points={
        'console_scripts': [
            'sensor_subscriber = sami.sensor_subscriber:main',
        ],
    },
)
