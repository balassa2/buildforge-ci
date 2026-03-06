"""Setup for the buildforge CLI tool."""

from setuptools import setup, find_packages

setup(
    name="buildforge-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0",
        "requests>=2.28",
        "rich>=13.0",
    ],
    entry_points={
        "console_scripts": [
            "buildforge=buildforge_cli.main:cli",
        ],
    },
)
