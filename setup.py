#!/usr/bin/env python3

from setuptools import find_packages, setup
from openai_ui import _version

with open("./README.md") as readme_file:
    readme = readme_file.read()

with open("./requirements.txt") as requirements_file:
    requirements = requirements_file.read().splitlines()

setup(
    author="Sky Moore",
    author_email="i@msky.me",
    classifiers=[
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    description="UI for openai completions",
    include_package_data=True,
    install_requires=requirements,
    keywords=[],
    license="MIT",
    long_description_content_type="text/markdown",
    long_description=readme,
    name="openai-ui",
    packages=find_packages(include=["openai_ui"]),
    entry_points={"gui_scripts": ["openai-ui = openai_ui.__main__:ui"]},
    url="https://github.com/skymoore/openai-ui",
    version=_version,
    zip_safe=True,
)
