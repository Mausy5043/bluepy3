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

## Installation

To install the current released version, on most Debian-based systems:
```bash
sudo apt-get install python3-pip libglib2.0-dev
sudo pip3 install bluepy3
```

On Fedora do:
```bash
sudo dnf install python3-pip glib2-devel
```

*If this fails* you should install from source.
```bash
sudo apt-get install git build-essential libglib2.0-dev
git clone https://github.com/Mausy5043/bluepy3.git
cd bluepy3
..
```
It is recommended having command-line tools from BlueZ available for debugging. There
are instructions for building BlueZ on the Raspberry Pi at http://www.elinux.org/RPi_Bluetooth_LE.

## Documentation

Documentation can be built from the sources in the docs/ directory using Sphinx.

## License  

See [LICENSE](LICENSE)



## Acknowledgements

This work builds on previous work by [Ian Harvey](https://github.com/IanHarvey/bluepy3) and uses code 
by the [BleuZ project](http://www.bluez.org/) (not a https site) and the more up-to-date [BleuZ on GitHub](https://github.com/bluez/bluez)

Original source code and documentation can be found at:   
  https://github.com/IanHarvey/bluepy3   
  http://ianharvey.github.io/bluepy3-doc/
