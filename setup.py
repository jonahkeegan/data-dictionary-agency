"""
Setup script for the Data Dictionary Agency package.
"""
import os
from setuptools import setup, find_packages

# Get version from environment or default
version = os.environ.get("VERSION", "0.1.0")

# Read requirements
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

# Read the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="data-dictionary-agency",
    version=version,
    description="Automated data dictionary generation for GitHub repositories",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="DDA Team",
    author_email="example@example.com",
    url="https://github.com/example/data-dictionary-agency",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={
        "console_scripts": [
            "dda=src.cli:main",
        ],
    },
)
