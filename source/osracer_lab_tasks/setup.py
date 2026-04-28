"""Installation script for the osracer_lab_tasks package."""

import os
import toml
from setuptools import setup, find_packages

EXTENSION_PATH = os.path.dirname(os.path.realpath(__file__))
EXTENSION_TOML_DATA = toml.load(os.path.join(EXTENSION_PATH, "config", "extension.toml"))

setup(
    name="osracer_lab_tasks",
    packages=find_packages(),
    author=EXTENSION_TOML_DATA["package"]["author"],
    maintainer=EXTENSION_TOML_DATA["package"]["maintainer"],
    url=EXTENSION_TOML_DATA["package"]["repository"],
    version=EXTENSION_TOML_DATA["package"]["version"],
    description=EXTENSION_TOML_DATA["package"]["description"],
    keywords=EXTENSION_TOML_DATA["package"]["keywords"],
    install_requires=["toml", "gymnasium==1.0.0", "osracer_lab_assets"],
    license="MIT",
    include_package_data=True,
    python_requires=">=3.10",
    zip_safe=False,
)
