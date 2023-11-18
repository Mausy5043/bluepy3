#!/usr/bin/env python3

"""Make the bluepy3-helper binary executable on demand."""

import os

# import platform
import shlex
import subprocess  # nosec: B404
import sys


VERSION: str = "1.13.13"  # latest version for testing
# VERSION: str = "1.12.1"  # latest version for production
MAKEFILE: str = "bluepy3/Makefile"
VERSION_FILE: str = "bluepy3/version.h"
BLUEZ_VERSION: str = "(unknown)"


def make_helper(version: str = "installed") -> None:
    bt_version: str = version
    if bt_version == "installed":
        bt_version = get_btctl_version()
    print(bt_version)


def get_btctl_version() -> str:
    # bluetoothctl version
    args: list[str] = ["bluetoothctl", "version"]
    try:
        _exit_code = (
            subprocess.check_output(
                args, shell=False, encoding="utf-8", timeout=5.0
            )  # nosec B603
            .strip("\n")
            .strip("'")
        ).split()
    except FileNotFoundError:
        return "not installed"
    return f"{_exit_code[1]}"


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
            msgs = subprocess.check_output(  # noqa: F841  # pylint: disable=unused-variable
                shlex.split(cmd), stderr=subprocess.STDOUT
            )  # nosec: B603
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
