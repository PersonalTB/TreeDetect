from setuptools import setup
import io

NAME = 'TreeDetect'
DESCRIPTION = 'Module for detecting trees with aerial photography and LiDAR data from geo-data sources.'
URL = ''
AUTHOR = 'Tim Bergman'
EMAIL = 'timbergman-personal@proton.me'
REQUIRES_PYTHON = '>=3.6.0'
VERSION = '0.1.0'

try:
    with io.open(os.path.join('.', 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

setup(
    name="TreeDetect",
    version="0.1",
    description="This is a python module for detecting trees with aerial photography and LiDAR data from PDOK geo-data sources.",
    license="MIT",
    author="Tim Bergman",
    author_email="timbergman-personal@proton.me",
    packages=['TreeDetect'],
    install_requires=["scipy>=1.1.0", "numpy>=1.17.3", "scikit-image>=0.16.2", "OWSLib>=0.19.1", "pyyaml",
    "pandas>=0.23.4", "rasterio>=1.1.3", "Pillow>=5.2.0", "matplotlib>=3.0.3", 
    "libpysal>=4.7.0", "networkx>=3.1"]
)
