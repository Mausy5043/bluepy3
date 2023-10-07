# bluepy3

[![PyPI version](https://img.shields.io/pypi/v/bluepy3.svg?logo=pypi&logoColor=FFE873)](https://pypi.org/project/bluepy3)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/bluepy3?logo=python&logoColor=FFE873)](https://pypi.org/project/bluepy3)
[![PyPI downloads](https://img.shields.io/pypi/dm/bluepy3.svg)](https://pypistats.org/packages/bluepy3)
[![Code style: Black](https://img.shields.io/badge/code%20style-Black-000000.svg)](https://github.com/psf/black)

This is a Python3 library to allow communication with Bluetooth Low Energy devices on Linux.

###### Note: If you are reading this on [PyPi](https://pypi.org/project/bluepy3/) then note that the formatting below looks terrible. Visit the project's homepage to read the correctly formatted [README.md](https://github.com/Mausy5043/bluepy3#readme) file. 

## Requirements

Please be aware that this is not a beginners tool. Some experience with Linux CLI, Python3 and BT/BLE is expected.

The package has been extensively tested on a Raspberry Pi 3 Model B+ (aarch64) with Debian GNU Linux 11 kernel 6.* and Python 3.9.*. It requires Python v3.7 or higher to be installed.

The code needs an executable `bluepy3-helper` which is compiled from C source automatically 
if you use the recommended pip installation method (see below). Otherwise,
you can rebuild it using the Makefile in the `bluepy3` directory.

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

To install the current released version, on most Debian-based systems:
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
This should list all (compatible) Bluetooth devices in range.

It may be considered to have command-line tools from BlueZ available for debugging. There
are instructions for building BlueZ on the Raspberry Pi at http://www.elinux.org/RPi_Bluetooth_LE.

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

Although Python v3.7 will still work, official support for v3.7 is dropped as of JUN2023 since that is EOL. It is advised to upgrade your Python installation to v3.9 or above.

## Documentation

Documentation can be built from the sources in the `docs/` directory using Sphinx.

## License  

See [LICENSE](LICENSE)

## Acknowledgements

This work builds on previous work by [Ian Harvey](https://github.com/IanHarvey/bluepy) and uses code 
by the [BlueZ project](http://www.bluez.org/) (not a https site) and the more 
up-to-date [BlueZ on GitHub](https://github.com/bluez/bluez)

Original source code and excellent documentation can be found at:   
  https://github.com/IanHarvey/bluepy   
  http://ianharvey.github.io/bluepy-doc/
