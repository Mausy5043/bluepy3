"""Python setup script for bluepy3"""

import os
import shlex
import subprocess
import sys

from setuptools import setup
from setuptools.command.build_py import build_py

VERSION = "1.3.1"  # -kimnaty
# versionnumber kept to fix error during installation:
#   ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
#   This behaviour is the source of the following dependency conflicts.
#   lywsd02 0.0.9 requires bluepy==1.3.0, but you have bluepy 1.3.0-kimnaty which is incompatible.


def pre_install():
    """Do the custom compiling of the bluepy3-helper executable from the makefile"""
    try:
        print("Working dir is " + os.getcwd())
        with open("bluepy3/version.h", "w") as verfile:
            verfile.write('#define VERSION_STRING "%s"\n' % VERSION)
        for cmd in ["make -C ./bluepy3 clean", "make -C bluepy3 -j1"]:
            print("execute " + cmd)
            msgs = subprocess.check_output(shlex.split(cmd), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print("Failed to compile bluepy3-helper. Exiting install.")
        print("Command was " + repr(cmd) + " in " + os.getcwd())
        print("Return code was %d" % e.returncode)
        print("Output was:\n%s" % e.output)
        sys.exit(1)


class my_build_py(build_py):
    def run(self):
        pre_install()
        build_py.run(self)


setup_cmdclass = {
    "build_py": my_build_py,
}

# Force package to be *not* pure Python
# Discusssed at issue #158

try:
    from wheel.bdist_wheel import bdist_wheel

    class BluepyBdistWheel(bdist_wheel):
        def finalize_options(self):
            bdist_wheel.finalize_options(self)
            self.root_is_pure = False

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
    keywords=["Bluetooth", "Bluetooth Smart", "BLE", "Bluetooth Low Energy"],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    packages=["bluepy3"],
    package_data={
        "bluepy3": [
            "bluepy3-helper",
            "*.json",
            "bluez-src.tgz",
            "bluepy3-helper.c",
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
