"""
Setup script for AgriTech Assistant
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agritech-assistant",
    version="2.0.0",
    author="AgriTech Team",
    author_email="team@agritech.com",
    description="AI-powered agricultural assistance platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/agritech/agritech-assistant",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Agriculture",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "gpu": [
            "torch[cuda]",
            "torchvision[cuda]",
        ],
    },
    entry_points={
        "console_scripts": [
            "agritech-server=main:app",
            "agritech-dev=run:main",
        ],
    },
    include_package_data=True,
    package_data={
        "app": ["templates/*", "static/*"],
    },
)