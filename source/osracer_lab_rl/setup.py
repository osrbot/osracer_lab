from setuptools import setup, find_packages

setup(
    name="osracer_lab_rl",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["toml", "gymnasium==1.0.0", "rsl-rl-lib>=2.3.0", "osracer_lab_tasks"],
    python_requires=">=3.10",
)
