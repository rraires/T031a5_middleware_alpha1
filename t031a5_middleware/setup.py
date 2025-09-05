#!/usr/bin/env python3
"""
Setup script for t031a5_middleware.
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = ""
readme_path = this_directory / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding='utf-8')

# Read requirements
requirements_path = this_directory / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() for line in f.readlines()
            if line.strip() and not line.startswith('#') and not line.startswith('-')
        ]

# Filter out platform-specific requirements for setup.py
filtered_requirements = []
for req in requirements:
    if '; platform_machine==' in req:
        # Skip platform-specific requirements in setup.py
        continue
    if req.startswith('#') or not req.strip():
        continue
    filtered_requirements.append(req)

setup(
    name="t031a5_middleware",
    version="1.0.0",
    author="Unitree Robotics",
    author_email="support@unitree.com",
    description="Advanced middleware system for Unitree quadruped robots",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/unitree/t031a5_middleware",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware :: Hardware Drivers",
    ],
    python_requires=">=3.8",
    install_requires=filtered_requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.7.0",
            "isort>=5.12.0",
            "pre-commit>=3.5.0",
        ],
        "ml": [
            "torch>=2.1.0",
            "torchvision>=0.16.0",
            "tensorflow>=2.14.0",
            "scikit-learn>=1.3.0",
            "opencv-contrib-python>=4.8.0",
        ],
        "hardware": [
            "rpi-ws281x>=5.0.0",
            "neopixel>=6.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "t031a5-middleware=main:main",
            "t031a5-config=utils.config:main",
            "t031a5-test=tests:main",
        ],
    },
    include_package_data=True,
    package_data={
        "t031a5_middleware": [
            "config.json",
            "data/gestures/*.json",
            "web/static/**/*",
            "web/templates/*.html",
            "web_dashboard/dist/**/*",
        ],
    },
    zip_safe=False,
    keywords=[
        "robotics",
        "unitree",
        "middleware",
        "quadruped",
        "robot",
        "automation",
        "control",
        "ai",
        "machine-learning",
    ],
    project_urls={
        "Bug Reports": "https://github.com/unitree/t031a5_middleware/issues",
        "Source": "https://github.com/unitree/t031a5_middleware",
        "Documentation": "https://docs.unitree.com/middleware",
    },
)