#!/usr/bin/env python3
# type: ignore

"""Python setup script for bluepy3"""

import os
import platform
import shlex
import subprocess
import sys

from setuptools import setup
from setuptools.command.build_py import build_py

VERSION: str = "1.13.10"  # latest version for testing
# VERSION: str = "1.12.1"  # latest version for production
MAKEFILE: str = "bluepy3/Makefile"
VERSION_FILE: str = "bluepy3/version.h"
BLUEZ_VERSION: str = "(unknown)"


def pre_install() -> None:
    """Do the custom compiling of the bluepy3-helper executable from the makefile"""
    global BLUEZ_VERSION  # noqa  # pylint: disable=global-statement
    cmd: str = ""
    try:
        print("\n\n*** Executing pre-install ***\n")
        print(f"Working dir is {os.getcwd()}")
        with open(MAKEFILE, "r", encoding="utf-8") as makefile:
            lines: list[str] = makefile.readlines()
            for line in lines:
                if line.startswith("BLUEZ_VERSION"):
                    BLUEZ_VERSION = line.split("=")[1].strip()
        with open(VERSION_FILE, "w", encoding="utf-8") as verfile:
            verfile.write(f'#define VERSION_STRING "{VERSION}-{BLUEZ_VERSION}"\n')
        for cmd in ["make -dC bluepy3 clean", "make -dC bluepy3 -j1"]:
            print(f"\nexecute {cmd}")
            # pylint: disable-next=unused-variable
            msgs = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)  # noqa
        print("\n\n*** Finished pre-install ***\n\n")
    except subprocess.CalledProcessError as e:
        print(f"Command was {repr(cmd)} in {os.getcwd()}")
        print(f"Return code was {e.returncode}")
        err_out: str = e.output.decode("utf-8")
        print(f"Output was:\n{err_out}")
        print(
            f"\nFailed to compile bluepy3-helper version {VERSION}-{BLUEZ_VERSION}."
            f" Exiting install.\n"
        )
        sys.exit(1)


class MyBuildPy(build_py):
    def run(self):
        # To allow installation on non-Linux systems for testing purposes
        # compiling of bluepy3-helper is avoided on those systems.
        if platform.system() == "Linux":
            pre_install()
        build_py.run(self)


setup_cmdclass = {
    "build_py": MyBuildPy,
}

# TODO: this is, maybe, not OR always required on Python 3.8+
# Force package to be *not* pure Python
# Discussed at https://github.com/IanHarvey/bluepy/issues/158
try:
    from wheel.bdist_wheel import bdist_wheel  # type: ignore

    class BluepyBdistWheel(bdist_wheel):
        def finalize_options(self):
            bdist_wheel.finalize_options(self)
            self.root_is_pure = False  # noqa    # pylint: disable=attribute-defined-outside-init

    setup_cmdclass["bdist_wheel"] = BluepyBdistWheel
except ImportError:
    pass

setup(
    name="bluepy3",
    version=VERSION,
    description="Python module for interfacing with BLE devices through Bluez",
    author="mausy5043",
    url="https://github.com/Mausy5043/bluepy3",
    download_url="https://github.com/Mausy5043/bluepy3",
    keywords=[
        "Bluetooth",
        "Bluetooth Smart",
        "BLE",
        "Bluetooth Low Energy",
        "Raspberry Pi",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Home Automation",
    ],
    packages=["bluepy3"],
    python_requires=">=3.8",
    package_data={
        "bluepy3": [
            "bluepy3-helper",
            "uuids.json",
            "bluepy3-helper.c",
            "config.*.h",
            "version.h",
            "Makefile",
        ]
    },
    cmdclass=setup_cmdclass,
    entry_points={
        "console_scripts": [
            "blescan=bluepy3.blescan:main",
        ]
    },
)
