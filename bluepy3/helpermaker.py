#!/usr/bin/env python3

"""Make the bluepy3-helper binary executable on demand."""

import os

import platform
import shlex
import subprocess  # nosec: B404
import sys

try:
    import tomllib as tl
except ModuleNotFoundError:
    import tomli as tl  # type: ignore[no-redef]

# We distinguish between three versions:
# VERSION
#   bluepy3 package (stored in pyproject.toml)
# BLUEZ_VERSION
#   the version of BlueZ (https://github.com/bluez/bluez) against which
#   the bluepy3-helper.c will be compiled. By default this will be the
#   version of bluetooth that is installed. This is discovered using
#   `bluetoothctl --version` and can be overriden by the user/client by
#   calling: make_helper(version="x.xx"), where "x.xx" is the required
#   version (str).
# BUILD_VERSION
#   the version that `bluepy3-helper` will get during the build.

_sep = "/"

HERE: str = _sep.join(__file__.split(_sep)[:-1])
APP_ROOT: str = HERE
MAKEFILE: str = f"{APP_ROOT}/Makefile"
VERSION_H: str = f"{APP_ROOT}/version.h"
PYPROJECT_TOML: str = f"{APP_ROOT}/pyproject.toml"


def get_btctl_version() -> str:
    """Return the bluetooth version (only on Linux)."""
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


def get_project_version() -> str:
    """Lookup the project version in pyproject.toml."""
    _pv = "pyproject.toml not found."
    try:
        with open(PYPROJECT_TOML, mode="rb") as _fp:
            TOML_CONTENTS = tl.load(_fp)
            _pv = str(TOML_CONTENTS["project"]["version"])
    except FileNotFoundError:
        pass
    return _pv


# fmt: off
def get_helper_version() -> str:
    """Look up the version of the helper binary, if installed."""
    _exit_code = "not installed."
    helper = f"{APP_ROOT}/bluepy3-helper"
    args = [helper, "version"]
    try:
        _exit_code = (
            subprocess.check_output(args, shell=False, encoding="utf-8", stderr=subprocess.STDOUT)  # noqa # nosec B603
            .strip("\n")
            .strip("'")
        ).split()
    except subprocess.CalledProcessError as exc:
        _exit_code = str(exc.output.split("\n")[0])
    except FileNotFoundError:
        print("Helper executable not found")
        pass
    return _exit_code
# fmt: on


VERSION: str = get_project_version()
BLUEZ_VERSION: str = get_btctl_version()
BUILD_VERSION: str = f"{VERSION}-{BLUEZ_VERSION}"
HELPER_VERSION: str = get_helper_version()
# print(APP_ROOT)
# print(f"Package version        : {VERSION}")
# print(f"bluetoothctl version   : {BLUEZ_VERSION}")
# print(f"bluepy3-helper version : {HELPER_VERSION}")


def build() -> None:
    """Do the custom compiling of the bluepy3-helper executable from the makefile"""
    cmd: str = ""
    # create the version.h containing the BUILD_VERSION
    with open(VERSION_H, "w", encoding="utf-8") as verfile:
        verfile.write(f'#define VERSION_STRING "{BUILD_VERSION}"\n')

    # read the Makefile
    with open(MAKEFILE, "r", encoding="utf-8") as makefile:
        lines: list[str] = makefile.readlines()
    # write the Makefile while inserting the desired BLUEZ_VERSION
    with open(MAKEFILE, "w", encoding="utf-8") as makefile:
        for line in lines:
            if line.startswith("BLUEZ_VERSION"):
                line = f"BLUEZ_VERSION={BLUEZ_VERSION}\n"
            makefile.write(line)
    if platform.system() == "Linux":
        # Windows and macOS aere not supported
        print("\n\n*** Building bluepy3-helper\n")
        for cmd in [f"make -C {APP_ROOT} clean", f"make -C {APP_ROOT} -j1"]:
            print(f"\n    Execute {cmd}")
            msgs: bytes = b""
            try:
                msgs = subprocess.check_output(  # noqa: F841  # pylint: disable=unused-variable
                    shlex.split(cmd), stderr=subprocess.STDOUT
                )  # nosec: B603
            except subprocess.CalledProcessError as e:
                print(f"Command was {repr(cmd)} in {os.getcwd()}")
                print(f"Return code was {e.returncode}")
                err_out: str = e.output.decode("utf-8")
                print(f"Output was:\n{err_out}")
                print(
                    f"\nFailed to compile bluepy3-helper version {BUILD_VERSION}."
                    f"\nExiting install.\n"
                )
                sys.exit(1)
            print(f"    Returned message: {msgs.decode(encoding='utf-8')}")
    else:
        print("\n\n*** Skipping build of bluepy3-helper")
        print("*** Windows and macOS are not supported")
    print("\n\n*** Finished post-install\n\n")


def make_helper(version: str = "installed") -> None:
    global BUILD_VERSION
    if version == "installed":
        BUILD_VERSION = f"{VERSION}-{BLUEZ_VERSION}"
    if version != "installed":
        BUILD_VERSION = f"{VERSION}-{version}"
    print(f"Building helper version {BUILD_VERSION} in {HERE}")
    build()


if __name__ == "__main__":
    make_helper()
    pass
