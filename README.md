# bluepy3

[![PyPI version](https://img.shields.io/pypi/v/bluepy3.svg?logo=pypi&logoColor=FFE873)](https://pypi.org/project/bluepy3)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/bluepy3.svg?logo=python&logoColor=FFE873)](https://pypi.org/project/bluepy3)
[![PyPI downloads](https://img.shields.io/pypi/dm/bluepy3.svg)](https://pypistats.org/packages/bluepy3)
[![Code style: Black](https://img.shields.io/badge/code%20style-Black-000000.svg)](https://github.com/psf/black)

This is a Python3 library to allow communication with Bluetooth Low Energy devices on Linux.

## Requirements

The code needs an executable `bluepy3-helper` to be compiled from C source. This is done
automatically if you use the recommended pip installation method (see below). Otherwise,
you can rebuild it using the Makefile in the `bluepy3` directory.

On Raspberry Pi (debian flavours like: dietpi; raspbian) additional APT packages are required and can be installed with:
```(bash)
sudo apt-get install libbluetooth-dev
```

If you want to rebuild `uuids.json` then Python3 modules `requests` and `lxml` need to be installed.
```(python3)
python3 -m pip install requests lxml
```
Then rebuild `uuid.json` thus: 
```(bash)
cd src/bluepy3
make uuid.json
```

## Installation

To install the current released version, on most Debian-based systems:
```(bash)
sudo apt-get install python3-pip libglib2.0-dev
python3 -m pip install bluepy3
```

*If this fails* you should install from source.
```bash
sudo apt-get install git build-essential libglib2.0-dev libbluetooth-dev
git clone https://github.com/Mausy5043/bluepy3.git
cd bluepy3
...tbd...
```

It is recommended having command-line tools from BlueZ available for debugging. There
are instructions for building BlueZ on the Raspberry Pi at http://www.elinux.org/RPi_Bluetooth_LE.

## Documentation

Documentation can be built from the sources in the docs/ directory using Sphinx.

## License  

See [LICENSE](LICENSE)

## Acknowledgements

This work builds on previous work by [Ian Harvey](https://github.com/IanHarvey/bluepy) and uses code 
by the [BleuZ project](http://www.bluez.org/) (not a https site) and the more up-to-date [BleuZ on GitHub](https://github.com/bluez/bluez)

Original source code and documentation can be found at:   
  https://github.com/IanHarvey/bluepy   
  http://ianharvey.github.io/bluepy-doc/
