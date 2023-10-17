#!/usr/bin/env python3

import argparse
import binascii
import os
import sys

from . import btle

if os.getenv("C", "1") == "0":
    ANSI_RED = ""
    ANSI_GREEN = ""
    ANSI_YELLOW = ""
    ANSI_CYAN = ""
    ANSI_WHITE = ""
    ANSI_OFF = ""
else:
    ANSI_CSI = "\033["
    ANSI_RED = ANSI_CSI + "31m"
    ANSI_GREEN = ANSI_CSI + "32m"
    ANSI_YELLOW = ANSI_CSI + "33m"
    ANSI_CYAN = ANSI_CSI + "36m"
    ANSI_WHITE = ANSI_CSI + "37m"
    ANSI_OFF = ANSI_CSI + "0m"


def dump_services(dev):
    services = sorted(dev.services, key=lambda k: k.hndStart)
    for s in services:
        print(f"\t{s.hndStart:04X}: {s}")
        if s.hndStart == s.hndEnd:
            continue
        chars = s.getCharacteristics()
        for i, c in enumerate(chars):
            props = c.propertiesToString()
            h = c.getHandle()
            if "READ" in props:
                val = c.read()
                if c.uuid == btle.AssignedNumbers.device_name:
                    string = ANSI_CYAN + "'" + val.decode("utf-8") + "'" + ANSI_OFF
                elif c.uuid == btle.AssignedNumbers.device_information:
                    string = repr(val)
                else:
                    string = "<s" + binascii.b2a_hex(val).decode("utf-8") + ">"
            else:
                string = ""
            print(f"\t{h:04X}:    {c} {props:>59} {string:>12}")

            while True:
                h += 1
                if h > s.hndEnd or (i < len(chars) - 1 and h >= chars[i + 1].getHandle() - 1):
                    break
                try:
                    val = dev.readCharacteristic(h)
                    bval = binascii.b2a_hex(val).decode("utf-8")
                    print(f"\t{h:04x}:     <{bval}>")
                except btle.BTLEException:
                    break


class ScanPrint(btle.DefaultDelegate):
    def __init__(self, opts):
        btle.DefaultDelegate.__init__(self)
        self.opts = opts

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            status = "new"
        elif isNewData:
            if self.opts.new:
                return
            status = "update"
        else:
            if not self.opts.all:
                return
            status = "old"

        if dev.rssi < self.opts.sensitivity:
            return
        dev_connectable = "(not connectable)"
        if dev.connectable:
            dev_connectable = ""
        print(
            f"    Device ({status}): {ANSI_WHITE}{dev.addr}{ANSI_OFF} ({dev.addrType}),"
            f" {dev.rssi} dBm {dev_connectable}"
        )
        for sdid, desc, val in dev.getScanData():
            if sdid in [8, 9]:
                print(f"\t{desc}: '{ANSI_CYAN}{val}{ANSI_OFF}'")
            else:
                print(f"\t{desc}: <{val}>")
        if not dev.scanData:
            print("\t(no data)")
        print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--hci",
        action="store",
        type=int,
        default=0,
        help="Interface number for scan",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        action="store",
        type=int,
        default=4,
        help="Scan delay, 0 for continuous",
    )
    parser.add_argument(
        "-s",
        "--sensitivity",
        action="store",
        type=int,
        default=-128,
        help="dBm value for filtering far devices",
    )
    parser.add_argument(
        "-d",
        "--discover",
        action="store_true",
        help="Connect and discover service to scanned devices",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Display duplicate adv responses, by default show new + updated",
    )
    parser.add_argument(
        "-n",
        "--new",
        action="store_true",
        help="Display only new adv responses, by default show new + updated",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase output verbosity"
    )
    arg = parser.parse_args(sys.argv[1:])

    btle.Debugging = arg.verbose

    scanner = btle.Scanner(arg.hci).withDelegate(ScanPrint(arg))

    print(ANSI_RED + "Scanning for devices..." + ANSI_OFF)
    devices = scanner.scan(arg.timeout)

    if arg.discover:
        print(ANSI_RED + "Discovering services..." + ANSI_OFF)

        for d in devices:
            if not d.connectable or d.rssi < arg.sensitivity:
                continue

            print("    Connecting to", ANSI_WHITE + d.addr + ANSI_OFF + ":")
            try:
                dev = btle.Peripheral(d)
                dump_services(dev)
                dev.disconnect()
            except:
                print(ANSI_RED + "Oops! Device doesn't want to talk to us." + ANSI_OFF)
            print()


if __name__ == "__main__":
    main()
