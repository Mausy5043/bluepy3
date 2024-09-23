
[![License](https://img.shields.io/github/license/mausy5043/bluepy3)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/bluepy3.svg?logo=pypi&logoColor=FFE873)](https://pypi.org/project/bluepy3)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/bluepy3?logo=python&logoColor=FFE873)](https://pypi.org/project/bluepy3)
[![PyPI downloads](https://img.shields.io/pypi/dm/bluepy3.svg)](https://pypistats.org/packages/bluepy3)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Mausy5043/bluepy3/devel.svg)](https://results.pre-commit.ci/latest/github/Mausy5043/bluepy3/devel)

# bluepy3

This is a Python3 library to allow communication with Bluetooth Low Energy devices on Linux.

## Requirements

Please be aware that this is not a beginners tool. Some experience with Linux CLI, Python3 and BT/BLE is expected.

Development of this package is done in Python 3.11. The package is considered forwards compatible at least upto Python 3.12 and probably also beyond. Backwards compatibility is not guaranteed; if it works on Python 3.9 or before consider yourself lucky. [Python versions that are end-of-life](https://devguide.python.org/versions/) are not supported.

The package has been extensively tested on a Raspberry Pi 3 Model B+ (aarch64) with Debian GNU Linux 11 w/ Python 3.9.* AND with Debian GNU Linux 12 /w Python 3.11.*.

The code needs an executable `bluepy3-helper` which is compiled from C source automatically
when first used (see below).

The `bluepy3` package comes installed with lists of compatible UUIDs in `uuids.json`.
If, for whatever reason, you want to rebuild those lists, then the Python3 modules
`bs4`, `requests` and `lxml` need to be installed.
```(python3)
python3 -m pip install bs4 lxml requests
```
Then find where the bluepy3 package is installed and rebuild `uuids.json` thus:
```(bash)
cd some_path_name/site-packages/bluepy3/
make uuids.json
```

## Installation

To install the currently released version, on most Debian-based systems:
```(bash)
sudo apt-get install libglib2.0-dev libbluetooth-dev
python3 -m pip install --upgrade bluepy3
```
Then test the installation using:
```(bash)
sudo setcap cap_net_raw,cap_net_admin+ep $(find . -name bluepy3-helper)
blescan -n
sudo hcitool lescan
```
This should list the (compatible) Bluetooth devices in range.

Upon the first `import` of `bluepy3.btle` the required binary is compiled. This requires the download of the BlueZ source (20MB) to `/tmp` (don't worry this is done automatically). The default behaviour is to compile against the version of the BlueZ source that matches the version of the installed `bluetoothctl`. The user may override this by forcing compilation against any of the supported source trees by running `helpermaker --build <version>`. You are advised NOT to use `make` directly, but rather use the python script `helpermaker`.

It may be considered to have command-line tools from BlueZ available for debugging.

## Troubleshooting

Make sure the user is part of the `bluetooth` group.
Use `hciconfig` to confirm that the device actually exists. This should output something like:
```
hci0:    Type: Primary  Bus: UART
BD Address: B8:27:EB:90:4F:F5  ACL MTU: 1021:8  SCO MTU: 64:1
UP RUNNING
RX bytes:15332515 acl:452626 sco:0 events:333729 errors:0
TX bytes:7376962 acl:438075 sco:0 commands:72113 errors:0
```
Use `hciconfig [hci0] up` to activate the BT device if the above returns an error.

## Documentation

For documentation you are referred to [the documentation that comes with `bluepy`](http://ianharvey.github.io/bluepy-doc/). Be warned though that as development of `bluepy3` advances some of the documentation may be off a bit.

## Contributing

Your assistance to improve this package is greatly appreciated.
See [CONTRIBUTING](CONTRIBUTING.md) for details.

## Disclaimer & License
As of September 2024 `bluepy3` is distributed under [AGPL-3.0-or-later](LICENSE).

## Acknowledgements

This work builds on previous work by [Ian Harvey](https://github.com/IanHarvey/bluepy) and uses code
by the [BlueZ project](http://www.bluez.org/) and the GitHub repository [BlueZ on GitHub](https://github.com/bluez/bluez)
