#!/usr/bin/env python3

# bluepy3
# Copyright (C) 2024  Maurice (mausy5043) Hendrix
# AGPL-3.0-or-later  - see LICENSE

"""Make the bluepy3-helper binary executable on demand.

Usage:
    import this module then call the function `make_helper(version="x.xx")` or
    execute `helpermaker --version x.xx` from the CLI
"""

import argparse
import logging.handlers
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
#   bluepy3 package (read from pyproject.toml)
# BLUEZ_VERSION
#   the version of BlueZ (https://github.com/bluez/bluez) against which
#   the bluepy3-helper.c will be compiled. By default this will be the
#   version of bluetooth that is installed. This is discovered using
#   `bluetoothctl --version` and can be overriden by the user/client by
#   calling:
#       - `make_helper(version="x.xx")` from a Python script or
#       - `helpermaker --version x.xx` from the CLI
#   where "x.xx" is the required version (str).
# BUILD_VERSION
#   the version that `bluepy3-helper` will get during the build.

_sep = "/"

HERE: str = _sep.join(__file__.split(_sep)[:-1])
CONFIG_DIR: str = f"{HERE}/config"
APP_ROOT: str = HERE
DEBUG: str = ""
MAKEFILE: str = f"{APP_ROOT}/Makefile"
VERSION_H: str = f"{APP_ROOT}/version.h"
PYPROJECT_TOML: str = f"{APP_ROOT}/pyproject.toml"

# Configure the logging module
logging.basicConfig(
    level=logging.INFO,
    format="%(module)s.%(funcName)s [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.handlers.SysLogHandler(
            address="/dev/log", facility=logging.handlers.SysLogHandler.LOG_DAEMON
        )
    ],
)

_LOGGER = logging.getLogger(__name__)


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
    _exit_code: str = "not installed."
    helper: str = f"{APP_ROOT}/bluepy3-helper"
    args: list[str] = [helper, "version"]
    try:
        # bluepy3_helper will print its version and then return an error
        # because 'version' is not a valid parameter value.
        _: list[str] = (
            subprocess.check_output(args, shell=False, encoding="utf-8", stderr=subprocess.STDOUT)  # noqa # nosec B603
            .strip("\n")
            .strip("'")
        ).split()
    except subprocess.CalledProcessError as exc:
        _exit_code = str(exc.output.split("\n")[0])
        _exit_code = _exit_code.replace("# ", "")
    except FileNotFoundError:
        _LOGGER.info("Helper executable not found")
    return _exit_code
# fmt: on


def get_builds() -> list[str]:
    _dir: list[str] = sorted(os.listdir(CONFIG_DIR))
    _config: list[str] = ["installed"]
    for _file in _dir:
        if _file[0:7] == "config." and _file[-2:] == ".h":
            _config.append(_file[7:-2])
    return _config


VERSION: str = get_project_version()
BLUEZ_VERSION: str = get_btctl_version()
BUILD_VERSION: str = f"{VERSION}-{BLUEZ_VERSION}"
HELPER_VERSION: str = get_helper_version()
SUPPORTED_BUILDS: list[str] = get_builds()


def build_helper() -> None:
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
    if platform.system().lower() == "linux":
        # Windows and macOS are not supported
        _LOGGER.info("*** Building bluepy3-helper")
        for cmd in [f"make -C {APP_ROOT} clean", f"make {DEBUG} -C {APP_ROOT} -j1"]:
            _LOGGER.info(f"Execute {cmd}")
            msgs: bytes = b""
            try:
                msgs = subprocess.check_output(  # noqa: F841  # pylint: disable=unused-variable
                    shlex.split(cmd), stderr=subprocess.STDOUT
                )  # nosec: B603
            except subprocess.CalledProcessError as e:
                _LOGGER.error(f"Command was:\n    {repr(cmd)} in {os.getcwd()}")
                _LOGGER.error(f"Return code was\n    {e.returncode}")
                err_out: str = e.output.decode("utf-8")
                _LOGGER.error(f"Output was:\n    {err_out}")
                _LOGGER.info(
                    f"Failed to compile bluepy3-helper version {BUILD_VERSION}."
                    f"Exiting install."
                )
                sys.exit(1)
            _LOGGER.info(f"Returned message:\n{msgs.decode(encoding='utf-8')}")
    else:
        _LOGGER.warning("*** Skipping build of bluepy3-helper")
        _LOGGER.warning("*** Windows and macOS are not supported")
    _LOGGER.info("*** Finished building bluepy3-helper")


def make_helper(build: str = "installed") -> None:
    global BLUEZ_VERSION  # pylint: disable=global-statement
    global BUILD_VERSION  # pylint: disable=global-statement
    if build == "installed":
        build = BLUEZ_VERSION
    if build in SUPPORTED_BUILDS:
        BLUEZ_VERSION = build
        BUILD_VERSION = f"{VERSION}-{build}"
        _LOGGER.info(f"Building helper version {BUILD_VERSION} in {HERE}")
        build_helper()
    else:
        _LOGGER.error(f"Version {build} is not supported.")
        raise RuntimeError(
            f"Version {build} is not supported.\nSupported versions are: {SUPPORTED_BUILDS}"
        )


def main() -> None:
    global DEBUG  # pylint: disable=global-statement
    # fmt: off
    parser = argparse.ArgumentParser(description="Compile the bluepy3-helper binary.")

    parser.add_argument("-b", "--build", type=str, help="version of BlueZ against which to compile the binary")
    parser.add_argument("-d", "--debug", action="store_true", help="enable debugging mode in the binary")
    parser.add_argument("-l", "--list", action="store_true", help="show a list of supported BlueZ versions")
    OPTION = parser.parse_args()
    # fmt: on
    print(f"Executing from here    : {APP_ROOT}")
    print(f"Package version        : {VERSION}")
    print(f"bluetoothctl version   : {BLUEZ_VERSION}")
    print(f"bluepy3-helper version : {HELPER_VERSION}")
    print(f"Requested to build     : {OPTION.build}")
    if OPTION.list:
        print(f"\nSupported versions of BlueZ are: {SUPPORTED_BUILDS}\n")
    if OPTION.debug:
        DEBUG = "DEBUGGING=1"
    if OPTION.build:
        make_helper(build=OPTION.build)


if __name__ == "__main__":
    main()
