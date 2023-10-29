# bluepy3

[![PyPI version](https://img.shields.io/pypi/v/bluepy3.svg?logo=pypi&logoColor=FFE873)](https://pypi.org/project/bluepy3)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/bluepy3?logo=python&logoColor=FFE873)](https://pypi.org/project/bluepy3)
[![PyPI downloads](https://img.shields.io/pypi/dm/bluepy3.svg)](https://pypistats.org/packages/bluepy3)
[![Code style: Black](https://img.shields.io/badge/code%20style-Black-000000.svg)](https://github.com/psf/black)

This is a Python3 library to allow communication with Bluetooth Low Energy devices on Linux.

###### ATTENTION: If you are reading this on [PyPi](https://pypi.org/project/bluepy3/) then note that the formatting below looks terrible. Visit the project's homepage to read the correctly formatted [README.md](https://github.com/Mausy5043/bluepy3#readme) file. 

## Requirements

Please be aware that this is not a beginners tool. Some experience with Linux CLI, Python3 and BT/BLE is expected.

Development of this package is done in Python 3.9. The package is considered forwards compatible at least upto Python 3.11 and probably also beyond. Backwards compatibility is not guaranteed; if it works on Python 3.7 or before consider yourself lucky. [Python versions that are end-of-life](https://devguide.python.org/versions/) are not supported.

The package has been extensively tested on a Raspberry Pi 3 Model B+ (aarch64) with Debian GNU Linux 11 w/ Python 3.9.* AND with Debian GNU Linux 12 /w Python 3.11.*.

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

For documentation you are referred to [the documentation that comes with `bluepy`](http://ianharvey.github.io/bluepy-doc/).

## Contributing

Your assistance to improve this package is greatly appreciated.  
See [CONTRIBUTING](CONTRIBUTING.md) for details.

## License  

See [LICENSE](LICENSE)

## Acknowledgements

This work builds on previous work by [Ian Harvey](https://github.com/IanHarvey/bluepy) and uses code 
by the [BlueZ project](http://www.bluez.org/) (not a https site) and the more 
up-to-date [BlueZ on GitHub](https://github.com/bluez/bluez)

Original source code can be found at:   
>  https://github.com/IanHarvey/bluepy
