"""Python setup script for bluepy3"""

import os
import shlex
import subprocess
import sys

from setuptools import setup
from setuptools.command.build_py import build_py

# VERSION = "1.5.1"   # latest version for testing
VERSION = "1.6.1"   # latest version for production
MAKEFILE = "bluepy3/Makefile"
VERSION_FILE = "bluepy3/version.h"
BLUEZ_VERSION = "(unknown)"


def pre_install():
    """Do the custom compiling of the bluepy3-helper executable from the makefile"""
    global BLUEZ_VERSION
    cmd = ""
    try:
        print("\n\n*** Executing pre-install ***\n")
        print(f"Working dir is {os.getcwd()}")
        with open(MAKEFILE, "r") as makefile:
            lines = makefile.readlines()
            for line in lines:
                if line.startswith("BLUEZ_VERSION"):
                    BLUEZ_VERSION = line.split("=")[1].strip()
        with open(VERSION_FILE, "w") as verfile:
            verfile.write(f'#define VERSION_STRING "{VERSION}-{BLUEZ_VERSION}"\n')
        for cmd in ["make -dC bluepy3 clean", "make -dC bluepy3 -j1"]:
            print(f"\nexecute {cmd}")
            msgs = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)  # noqa
        print("\n\n*** Finished pre-install ***\n\n")
    except subprocess.CalledProcessError as e:
        print("Failed to compile bluepy3-helper. Exiting install.")
        print(f"Command was {repr(cmd)} in {os.getcwd()}")
        print(f"Return code was {e.returncode}")
        print(f"Output was:\n{e.output}")
        sys.exit(1)


class MyBuildPy(build_py):
    def run(self):
        pre_install()
        build_py.run(self)


setup_cmdclass = {
    "build_py": MyBuildPy,
}

# Force package to be *not* pure Python
# Discusssed at issue #158

try:
    from wheel.bdist_wheel import bdist_wheel  # noqa

    class BluepyBdistWheel(bdist_wheel):
        def finalize_options(self):
            bdist_wheel.finalize_options(self)
            self.root_is_pure = False  # noqa

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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Home Automation",
    ],
    packages=["bluepy3"],
    python_requires=">=3.7",
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
            "thingy52=bluepy3.thingy52:main",
            "sensortag=bluepy3.sensortag:main",
            "blescan=bluepy3.blescan:main",
        ]
    },
)
