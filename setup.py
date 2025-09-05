#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup do Middleware t031a5 para Robô Unitree G1

Sistema de orquestração completo para robótica humanoide,
projetado para integração multimodal e interação natural.
"""

from setuptools import setup, find_packages
import os

# Lê o arquivo README
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Lê as dependências
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="t031a5-middleware",
    version="1.0.0",
    author="Roberto",
    author_email="roberto@example.com",
    description="Middleware de Orquestração para Robótica Humanoide Unitree G1",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/roberto/t031a5-middleware",
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
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: System :: Hardware :: Hardware Drivers",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "docs": [
            "sphinx>=7.1.2",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "t031a5=t031a5_middleware.main:main",
            "t031a5-dashboard=t031a5_middleware.web.app:main",
            "t031a5-config=t031a5_middleware.utils.config_tool:main",
        ],
    },
    include_package_data=True,
    package_data={
        "t031a5_middleware": [
            "config/*.yaml",
            "web/static/*",
            "web/templates/*",
            "data/*",
        ],
    },
    zip_safe=False,
)