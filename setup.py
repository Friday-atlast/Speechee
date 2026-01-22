"""
Speechee Setup Script
Install with: pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="speechee",
    version="1.0.0-dev",
    description="Offline-First Speech-to-Text System",
    author="Friday",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "requests==2.28.2",
        "sounddevice==0.4.6",
        "soundfile==0.12.1",
        "numpy==1.24.3",
        "pyaudio==0.2.13",
        "pipwin==0.5.1",
        "colorama==0.4.6"
    ],
    entry_points={
        "console_scripts": [
            "speechee=cli.speechee:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)