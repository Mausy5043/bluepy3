#!/usr/bin/env python3

"""Make the bluepy3-helper binary executable on demand."""

import os
import platform
import shlex
import subprocess
import sys

from setuptools import setup
from setuptools.command.build_py import build_py

VERSION: str = "1.13.13"  # latest version for testing
# VERSION: str = "1.12.1"  # latest version for production
MAKEFILE: str = "bluepy3/Makefile"
VERSION_FILE: str = "bluepy3/version.h"
BLUEZ_VERSION: str = "(unknown)"


def make_helper(version: str = "installed") -> None:
    print(version)


def build() -> None:
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


if __name__ == "__main__":
    make_helper()
