#!/usr/bin/env python3

"""Bluetooth Low Energy Python3 interface"""

import binascii
import json
import os
import signal
import struct
import subprocess
import sys
import time
from queue import Queue, Empty
from threading import Thread
from typing import Any, Optional


def preexec_function() -> None:
    # Ignore the SIGINT signal by setting the handler to the standard
    # signal handler SIG_IGN.
    signal.signal(signal.SIGINT, signal.SIG_IGN)


Debugging = False
script_path = os.path.join(os.path.abspath(os.path.dirname(__file__)))
helperExe = os.path.join(script_path, "bluepy3-helper")

SEC_LEVEL_LOW = "low"
SEC_LEVEL_MEDIUM = "medium"
SEC_LEVEL_HIGH = "high"

ADDR_TYPE_PUBLIC = "public"
ADDR_TYPE_RANDOM = "random"

BTLE_TIMEOUT = 32.1


def DBG(*args) -> None:  # type: ignore
    if Debugging:
        msg: str = " ".join([str(a) for a in args])
        print(f"{msg}")


class BTLEException(Exception):
    """Base class for all Bluepy exceptions"""

    def __init__(self, message: str, resp_dict: Optional[dict[str, str]] = None) -> None:
        self.message: str = message

        # optional messages from bluepy3-helper
        self.estat = None
        self.emsg = None
        if resp_dict:
            self.estat = resp_dict.get("estat", None)
            if isinstance(self.estat, list):
                self.estat = self.estat[0]
            self.emsg = resp_dict.get("emsg", None)
            if isinstance(self.emsg, list):
                self.emsg = self.emsg[0]

    def __str__(self) -> str:
        msg: str = self.message
        if self.estat or self.emsg:
            msg = f"{msg} ("
            if self.estat:
                msg = f"{msg}code: {self.estat}"
            if self.estat and self.emsg:
                msg = f"{msg}, "
            if self.emsg:
                msg = f"{msg}error: {self.emsg}"
            msg = f"{msg})"
        msg = f"(btle) {self.message}"
        return msg


class BTLEInternalError(BTLEException):
    def __init__(self, message: str, rsp: Optional[dict[str, str]] = None) -> None:
        BTLEException.__init__(self, message, rsp)


class BTLEConnectError(BTLEException):
    def __init__(self, message: str, rsp: Optional[dict[str, str]] = None) -> None:
        BTLEException.__init__(self, message, rsp)


class BTLEConnectTimeout(BTLEException):
    def __init__(self, message: str, rsp: Optional[dict[str, str]] = None) -> None:
        BTLEException.__init__(self, message, rsp)


class BTLEManagementError(BTLEException):
    def __init__(self, message: str, rsp: Optional[dict[str, str]] = None) -> None:
        BTLEException.__init__(self, message, rsp)


class BTLEGattError(BTLEException):
    def __init__(self, message: str, rsp: Optional[dict[str, str]] = None) -> None:
        BTLEException.__init__(self, message, rsp)


class UUID:
    def __init__(self, val: Any, commonName: str = "") -> None:
        """Initialisation
        We accept: 32-digit hex strings, with and without '-' characters,
        4 to 8 digit hex strings, and integers
        """
        if isinstance(val, int):
            if (val < 0) or (val > 0xFFFFFFFF):
                raise ValueError("(btle.py) Short form UUIDs must be in range 0..0xFFFFFFFF")
            val = f"{val:04X}"
        elif isinstance(val, self.__class__):
            val = str(val)
        else:
            val = str(val)  # Do our best

        val = val.replace("-", "")
        if len(val) <= 8:  # Short form
            val = ("0" * (8 - len(val))) + val + "00001000800000805F9B34FB"

        self.binVal: bytes = binascii.a2b_hex(val.encode("utf-8"))
        if len(self.binVal) != 16:
            raise ValueError(
                f"(btle.py) UUID must be 16 bytes, got '{val}' (len={len(self.binVal)})"
            )
        self.commonName: str = commonName

    def __str__(self) -> str:
        s = binascii.b2a_hex(self.binVal).decode("utf-8")
        return "-".join([s[0:8], s[8:12], s[12:16], s[16:20], s[20:32]])

    def __eq__(self, other: Any) -> bool:
        return self.binVal == UUID(other).binVal

    def __hash__(self) -> int:
        return hash(self.binVal)

    def getCommonName(self) -> str:
        s = AssignedNumbers.getCommonName(self)
        if s:
            return s
        s = str(self)
        if s.endswith("-0000-1000-8000-00805f9b34fb"):
            s = s[0:8]
            if s.startswith("0000"):
                s = s[4:]
        return s


class Service:
    def __init__(self, *args) -> None:
        (self.peripheral, uuidVal, self.hndStart, self.hndEnd) = args
        self.uuid = UUID(uuidVal)
        self.chars = None
        self.descs = None

    def getCharacteristics(self, forUUID=None):
        if not self.chars:  # Unset, or empty
            self.chars = (
                []
                if self.hndEnd <= self.hndStart
                else self.peripheral.getCharacteristics(self.hndStart, self.hndEnd)
            )
        if forUUID is not None:
            u = UUID(forUUID)
            return [ch for ch in self.chars if ch.uuid == u]
        return self.chars

    def getDescriptors(self, forUUID=None) -> list:
        if not self.descs:
            # Grab all descriptors in our range, except for the service
            # declaration descriptor
            all_descs = self.peripheral.getDescriptors(self.hndStart + 1, self.hndEnd)
            # Filter out the descriptors for the characteristic properties
            # Note that this does not filter out characteristic value descriptors
            self.descs = [desc for desc in all_descs if desc.uuid != 0x2803]
        if forUUID is not None:
            u = UUID(forUUID)
            return [desc for desc in self.descs if desc.uuid == u]
        return self.descs

    def __str__(self) -> str:
        return (
            f"Service <uuid={self.uuid.getCommonName()} "
            f"handleStart={self.hndStart} "
            f"handleEnd={self.hndEnd}>"
        )


class Characteristic:
    # Currently only READ is used in supportsRead function,
    # the rest is included to facilitate supportsXXXX functions if required
    props: dict[str, int] = {
        "BROADCAST": 0b00000001,
        "READ": 0b00000010,
        "WRITE_NO_RESP": 0b00000100,
        "WRITE": 0b00001000,
        "NOTIFY": 0b00010000,
        "INDICATE": 0b00100000,
        "WRITE_SIGNED": 0b01000000,
        "EXTENDED": 0b10000000,
    }

    propNames: dict[int, str] = {
        0b00000001: "BROADCAST",
        0b00000010: "READ",
        0b00000100: "WRITE NO RESPONSE",
        0b00001000: "WRITE",
        0b00010000: "NOTIFY",
        0b00100000: "INDICATE",
        0b01000000: "WRITE SIGNED",
        0b10000000: "EXTENDED PROPERTIES",
    }

    def __init__(self, *args) -> None:
        (self.peripheral, uuidVal, self.handle, self.properties, self.valHandle) = args
        self.uuid = UUID(uuidVal)
        self.descs = None

    def read(self):
        return self.peripheral.readCharacteristic(self.valHandle)

    def write(self, val, withResponse=False):
        return self.peripheral.writeCharacteristic(self.valHandle, val, withResponse)

    def getDescriptors(self, forUUID=None, hndEnd=0xFFFF):
        if not self.descs:
            # Descriptors (not counting the value descriptor) begin after
            # the handle for the value descriptor and stop when we reach
            # the handle for the next characteristic or service
            self.descs = []
            for desc in self.peripheral.getDescriptors(self.valHandle + 1, hndEnd):
                if desc.uuid in (0x2800, 0x2801, 0x2803):
                    # Stop if we reach another characteristic or service
                    break
                self.descs.append(desc)
        if forUUID is not None:
            u = UUID(forUUID)
            return [desc for desc in self.descs if desc.uuid == u]
        return self.descs

    def __str__(self) -> str:
        return f"Characteristic <{self.uuid.getCommonName()}>"

    def supportsRead(self) -> bool:
        return bool(self.properties & Characteristic.props["READ"])

    def propertiesToString(self) -> str:
        propStr: str = ""
        for p in Characteristic.propNames:  # pylint: disable=consider-using-dict-items)
            if p & self.properties:
                propStr += Characteristic.propNames[p] + " "
        return propStr

    def getHandle(self):
        return self.valHandle


class Descriptor:
    def __init__(self, *args) -> None:
        (self.peripheral, uuidVal, self.handle) = args
        self.uuid = UUID(uuidVal)

    def __str__(self) -> str:
        return f"Descriptor <{self.uuid.getCommonName()}>"

    def read(self):
        return self.peripheral.readCharacteristic(self.handle)

    def write(self, val, withResponse=False) -> None:
        self.peripheral.writeCharacteristic(self.handle, val, withResponse)


class DefaultDelegate:
    def __init__(self) -> None:
        pass

    def handleNotification(self, cHandle, data) -> None:
        hex_data: str = binascii.b2a_hex(data).decode("utf-8")
        DBG(f"    -btle- Notification: {cHandle} sent data {hex_data}")

    def handleDiscovery(
        self,
        scanEntry,
        isNewDev,  # pylint: disable=unused-argument
        isNewData,  # pylint: disable=unused-argument
    ) -> None:
        dev_str: str = str(scanEntry.addr)
        DBG(f"    -btle- Discovered device {dev_str}")


class Bluepy3Helper:
    def __init__(self) -> None:
        self._helper = None
        self._lineq = None
        self._stderr = None
        self._mtu = 0
        self.delegate = DefaultDelegate()
        self._aita = 0

    def withDelegate(self, delegate_):
        self.delegate = delegate_
        return self

    def _startHelper(self, iface=None) -> None:
        if self._helper is None:
            DBG(f"    -btle- Running {helperExe}")
            self._aita = 0
            self._lineq = Queue()
            self._mtu = 0
            # pylint: disable-next=consider-using-with
            self._stderr = open(os.devnull, "w")  # pylint: disable=unspecified-encoding
            args = [helperExe]
            if iface is not None:
                args.append(str(iface))
            #
            # pylint: disable-next=consider-using-with, disable-next=W1509  # FIXME: should not be using preexec_fn
            self._helper = subprocess.Popen(
                args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self._stderr,
                universal_newlines=True,
                preexec_fn=preexec_function,
            )
            t = Thread(target=self._readToQueue)
            t.daemon = True  # don't wait for it to exit
            t.start()

    def _readToQueue(self) -> None:
        """Thread to read lines from stdout and insert in queue."""
        while self._helper:
            line = self._helper.stdout.readline()
            if not line:  # EOF
                break
            self._lineq.put(line)

    def _stopHelper(self) -> None:
        if self._helper is not None:
            DBG(f"    -btle- Stopping {helperExe}")
            self._helper.stdin.write("quit\n")
            self._helper.stdin.flush()
            self._helper.wait()
            self._helper = None
            self._aita = None
        if self._stderr is not None:
            self._stderr.close()
            self._stderr = None

    def _writeCmd(self, cmd) -> None:
        if self._helper is None:
            raise BTLEInternalError("Helper not started (did you call connect()?)")
        DBG(f"    -btle- Sent:   {cmd}")
        self._helper.stdin.write(cmd)
        self._helper.stdin.flush()

    def _mgmtCmd(self, cmd) -> None:
        self._writeCmd(cmd + "\n")
        rsp = self._waitResp("mgmt")
        if rsp["code"][0] != "success":
            self._stopHelper()
            raise BTLEManagementError(f"Failed to execute management command '{cmd}'", rsp)

    @staticmethod
    def parseResp(line):
        resp = {}
        for item in line.rstrip().split("\x1e"):
            (tag, tval) = item.split("=")
            if len(tval) == 0:
                val = None
            elif tval[0] == "$" or tval[0] == "'":
                # Both symbols and strings as Python strings
                val = tval[1:]
            elif tval[0] == "h":
                val = int(tval[1:], 16)
            elif tval[0] == "b":
                val = binascii.a2b_hex(tval[1:].encode("utf-8"))
            else:
                raise BTLEInternalError(f"Cannot understand response value {repr(tval)}")
            if tag not in resp:
                resp[tag] = [val]
            else:
                resp[tag].append(val)
        return resp

    def _waitResp(self, wantType, timeout=BTLE_TIMEOUT) -> dict[str, str]:
        while True:
            if self._helper.poll() is not None:
                raise BTLEInternalError("Helper exited")

            try:
                rv = self._lineq.get(timeout=timeout)
            except Empty:
                DBG("*** -btle- Select timeout")
                return None
            dehex_rv = (
                repr(rv).replace("\\x1e", "; ").replace("\\n", "").replace("'", "").strip('"')
            )
            DBG(f"    -btle- Got:    {dehex_rv}")
            if rv.startswith("#") or rv == "\n" or len(rv) == 0:
                continue

            resp = Bluepy3Helper.parseResp(rv)
            if "rsp" not in resp:
                raise BTLEInternalError("No response type indicator", resp)

            # sometimes devices just keep sending `ntfy`
            if "ntfy" in repr(rv):
                self._aita += 1
                if self._aita > 3:
                    self._stopHelper()
                    raise BTLEInternalError("Device keeps repeating itself. Giving up.", resp)

            respType = resp["rsp"][0]

            # always check for MTU updates
            if "mtu" in resp and len(resp["mtu"]) > 0:
                new_mtu = int(resp["mtu"][0])
                if self._mtu != new_mtu:
                    self._mtu = new_mtu
                    DBG(f"    -btle- Updated MTU: {str(self._mtu)}")

            if respType in wantType:
                return resp
            if respType == "stat":
                if "state" in resp and len(resp["state"]) > 0 and resp["state"][0] == "disc":
                    self._stopHelper()
                    raise BTLEConnectError("Device disconnected", resp)
            if respType == "err":
                errcode = resp["code"][0]
                if errcode == "nomgmt":
                    raise BTLEManagementError(
                        "Management not available (permissions problem?)", resp
                    )
                if errcode == "atterr":
                    raise BTLEGattError("Bluetooth command failed", resp)
                raise BTLEException(f"Error from bluepy3-helper ({errcode})", resp)
            if respType == "scan":
                # Scan response when we weren't interested. Ignore it
                continue
            raise BTLEInternalError(f"Unexpected response ({respType})", resp)

    def status(self):
        self._writeCmd("stat\n")
        return self._waitResp(["stat"])


class Peripheral(Bluepy3Helper):
    # fmt: off
    def __init__(self, addr: str = "", addrType: str = ADDR_TYPE_PUBLIC, iface: str = "", timeout: float = BTLE_TIMEOUT) -> None:
        Bluepy3Helper.__init__(self)
        self._serviceMap = None  # Indexed by UUID
        self.addr = addr
        self.addrType = addrType
        self.iface = iface

        if isinstance(addr, ScanEntry):
            self._connect(addr.addr, addr.addrType, addr.iface, timeout)
        elif addr:
            self._connect(addr, addrType, iface, timeout)
    # fmt: on

    def setDelegate(self, delegate_):  # same as withDelegate(), deprecated
        return self.withDelegate(delegate_)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, exception_traceback) -> None:
        self.disconnect()

    def _getResp(self, wantType, timeout=BTLE_TIMEOUT):
        if isinstance(wantType, list) is not True:
            wantType = [wantType]
        while True:
            resp = self._waitResp(wantType + ["ntfy", "ind"], timeout)
            if resp is None:
                return None

            respType = resp["rsp"][0]
            if respType in ["ntfy", "ind"]:
                hnd = resp["hnd"][0]
                data = resp["d"][0]
                if self.delegate is not None:
                    self.delegate.handleNotification(hnd, data)
            if respType not in wantType:
                continue
            return resp

    def _connect(
        self, addr: str, addrType=ADDR_TYPE_PUBLIC, iface="", timeout=BTLE_TIMEOUT
    ) -> None:
        max_retries = 5
        if len(addr.split(":")) != 6:
            raise ValueError(f"(btle.py) Expected MAC address, got {repr(addr)}")
        if addrType not in (ADDR_TYPE_PUBLIC, ADDR_TYPE_RANDOM):
            raise ValueError(f"(btle.py) Expected address type public or random, got {addrType}")
        self.retries = max_retries
        while self.retries > 0:
            self._startHelper(iface)
            self.addr = addr
            self.addrType = addrType
            self.iface = iface
            if iface:
                self._writeCmd(f"conn {addr} {addrType} hci{str(iface)}\n")
            else:
                self._writeCmd(f"conn {addr} {addrType}\n")
            rsp = self._getResp("stat", timeout)
            timeout_exception = BTLEConnectTimeout(
                f"Timed out while trying to connect to peripheral {addr}, "
                f"addr type: {addrType}, interface {iface}, timeout={timeout}",
                rsp,
            )
            if rsp is None:
                raise timeout_exception
            while rsp and rsp["state"][0] == "tryconn":
                rsp = self._getResp("stat", timeout)
            if rsp is not None and rsp["state"][0] == "conn":
                DBG("    -btle- Succesfully connected.")
                # successful
                self.retries = 0
            if rsp is None or rsp["state"][0] != "conn":
                self._stopHelper()
                if rsp is None:
                    raise timeout_exception
                DBG(f"*** -btle-  Failed to connect. ({self.retries})")
                time.sleep(0.5 * (max_retries - self.retries))
                if self.retries <= 1:
                    raise BTLEConnectError(
                        f"Failed to connect to peripheral {addr}, "
                        f"addr type: {addrType}, interface {iface}, timeout={timeout}",
                        rsp,
                    )
            self.retries -= 1

    def connect(self, addr, addrType=ADDR_TYPE_PUBLIC, iface=None, timeout=BTLE_TIMEOUT) -> None:
        if isinstance(addr, ScanEntry):
            self._connect(addr.addr, addr.addrType, addr.iface, timeout)
        elif addr is not None:
            self._connect(addr, addrType, iface, timeout)

    def disconnect(self) -> None:
        if self._helper is None:
            return
        # Unregister the delegate first
        self.setDelegate(None)

        self._writeCmd("disc\n")
        self._getResp("stat")
        self._stopHelper()

    def discoverServices(self):
        self._writeCmd("svcs\n")
        rsp = self._getResp("find")
        starts = rsp["hstart"]
        ends = rsp["hend"]
        uuids = rsp["uuid"]
        nSvcs = len(uuids)
        assert len(starts) == nSvcs and len(ends) == nSvcs
        self._serviceMap = {}
        for i in range(nSvcs):
            self._serviceMap[UUID(uuids[i])] = Service(self, uuids[i], starts[i], ends[i])
        return self._serviceMap

    def getState(self):
        status = self.status()
        return status["state"][0]

    @property
    def services(self):
        if self._serviceMap is None:
            self._serviceMap = self.discoverServices()
        return list(self._serviceMap.values())

    def getServices(self):
        return self.services

    def getServiceByUUID(self, uuidVal):
        uuid = UUID(uuidVal)
        if self._serviceMap is not None and uuid in self._serviceMap:
            return self._serviceMap[uuid]
        self._writeCmd(f"svcs {uuid}\n")
        rsp = self._getResp("find")
        if "hstart" not in rsp:
            raise BTLEGattError(f"Service {uuid.getCommonName()} not found", rsp)
        svc = Service(self, uuid, rsp["hstart"][0], rsp["hend"][0])

        if self._serviceMap is None:
            self._serviceMap = {}
        self._serviceMap[uuid] = svc
        return svc

    def _getIncludedServices(self, startHnd=1, endHnd=0xFFFF):
        self._writeCmd(f"incl {startHnd:X} {endHnd:X}\n")
        return self._getResp("find")

    def getCharacteristics(self, startHnd=1, endHnd=0xFFFF, uuid=None, timeout=BTLE_TIMEOUT):
        cmd = f"char {startHnd:X} {endHnd:X}"
        if uuid:
            cmd += f" {UUID(uuid)}"
        self._writeCmd(cmd + "\n")
        rsp = self._getResp("find", timeout)
        timeout_exception = BTLEConnectTimeout(
            f"Timed out while trying to get characteristics from peripheral {self.addr}, "
            f"addr type: {self.addrType}",
            rsp,
        )
        if rsp is None:
            raise timeout_exception
        nChars = len(rsp["hnd"])
        return [
            Characteristic(self, rsp["uuid"][i], rsp["hnd"][i], rsp["props"][i], rsp["vhnd"][i])
            for i in range(nChars)
        ]

    def getDescriptors(self, startHnd=1, endHnd=0xFFFF):
        self._writeCmd(f"desc {startHnd:X} {endHnd:X}\n")
        # Historical note:
        # Certain Bluetooth LE devices are not capable of sending back all
        # descriptors in one packet due to the limited size of MTU. So the
        # guest needs to check the response and make retries until all handles
        # are returned.
        # In bluez 5.25 and later, gatt_discover_desc() in attrib/gatt.c does the retry
        # so bluetooth_helper always returns a full list.
        # This was broken in earlier versions.
        resp = self._getResp("desc")
        ndesc = len(resp["hnd"])
        return [Descriptor(self, resp["uuid"][i], resp["hnd"][i]) for i in range(ndesc)]

    def readCharacteristic(self, handle):
        self._writeCmd(f"rd {handle:X}\n")
        resp = self._getResp("rd")
        return resp["d"][0]

    def _readCharacteristicByUUID(self, uuid, startHnd, endHnd):
        # Not used at present
        self._writeCmd(f"rdu {UUID(uuid)} {startHnd:X} {endHnd:X}\n")
        return self._getResp("rd")

    def writeCharacteristic(self, handle, val, withResponse=False, timeout=BTLE_TIMEOUT):
        # Without response, a value too long for one packet will be truncated,
        # but with response, it will be sent as a queued write
        cmd = "wrr" if withResponse else "wr"
        bval: str = binascii.b2a_hex(val).decode("utf-8")
        self._writeCmd(f"{cmd} {handle:X} {bval}\n")
        return self._getResp("wr", timeout)

    def setSecurityLevel(self, level):
        self._writeCmd(f"secu {level}\n")
        return self._getResp("stat")

    def unpair(self):
        self._mgmtCmd("unpair")

    def pair(self) -> None:
        self._mgmtCmd("pair")

    def getMTU(self) -> int:
        return self._mtu

    def setMTU(self, mtu):
        self._writeCmd(f"mtu {mtu}\n")
        return self._getResp("stat")

    def waitForNotifications(self, timeout) -> bool:
        resp = self._getResp(["ntfy", "ind"], timeout)
        return resp is not None

    def _setRemoteOOB(self, address, address_type, oob_data, iface=None) -> None:
        if self._helper is None:
            self._startHelper(iface)
        self.addr = address
        self.addrType = address_type
        self.iface = iface
        cmd = "remote_oob " + address + " " + address_type
        if oob_data["C_192"] is not None and oob_data["R_192"] is not None:
            cmd += " C_192 " + oob_data["C_192"] + " R_192 " + oob_data["R_192"]
        if oob_data["C_256"] is not None and oob_data["R_256"] is not None:
            cmd += " C_256 " + oob_data["C_256"] + " R_256 " + oob_data["R_256"]
        if iface is not None:
            cmd += " hci" + str(iface)
        self._writeCmd(cmd)

    def setRemoteOOB(self, address, address_type, oob_data, iface=None) -> None:
        if len(address.split(":")) != 6:
            raise ValueError(f"(btle.py) Expected MAC address, got {repr(address)}")
        if address_type not in (ADDR_TYPE_PUBLIC, ADDR_TYPE_RANDOM):
            raise ValueError(
                f"(btle.py) Expected address type public or random, got {address_type}"
            )
        if isinstance(address, ScanEntry):
            return self._setRemoteOOB(address.addr, address.addrType, oob_data, address.iface)
        return self._setRemoteOOB(address, address_type, oob_data, iface)

    def getLocalOOB(self, iface=None):
        cmd = ""
        if self._helper is None:
            self._startHelper(iface)
        self.iface = iface
        self._writeCmd("local_oob\n")
        if iface is not None:
            cmd += " hci" + str(iface)
        resp = self._getResp("oob")
        if resp is not None:
            data = resp.get("d", [""])[0]
            if data is None:
                raise BTLEManagementError("Failed to get local OOB data.")
            if (
                struct.unpack_from("<B", data, 0)[0] != 8
                or struct.unpack_from("<B", data, 1)[0] != 0x1B
            ):
                raise BTLEManagementError("Malformed local OOB data (address).")
            address = data[2:8]
            address_type = data[8:9]
            if (
                struct.unpack_from("<B", data, 9)[0] != 2
                or struct.unpack_from("<B", data, 10)[0] != 0x1C
            ):
                raise BTLEManagementError("Malformed local OOB data (role).")
            role = data[11:12]
            if (
                struct.unpack_from("<B", data, 12)[0] != 17
                or struct.unpack_from("<B", data, 13)[0] != 0x22
            ):
                raise BTLEManagementError("Malformed local OOB data (confirm).")
            confirm = data[14:30]
            if (
                struct.unpack_from("<B", data, 30)[0] != 17
                or struct.unpack_from("<B", data, 31)[0] != 0x23
            ):
                raise BTLEManagementError("Malformed local OOB data (random).")
            random = data[32:48]
            if (
                struct.unpack_from("<B", data, 48)[0] != 2
                or struct.unpack_from("<B", data, 49)[0] != 0x1
            ):
                raise BTLEManagementError("Malformed local OOB data (flags).")
            flags = data[50:51]
            # fmt: off
            return {
                "Address": "".join(["%02X" % struct.unpack("<B", c)[0] for c in address]),      # pylint: disable=C0209
                "Type": "".join(["%02X" % struct.unpack("<B", c)[0] for c in address_type]),    # pylint: disable=C0209
                "Role": "".join(["%02X" % struct.unpack("<B", c)[0] for c in role]),            # pylint: disable=C0209
                "C_256": "".join(["%02X" % struct.unpack("<B", c)[0] for c in confirm]),        # pylint: disable=C0209
                "R_256": "".join(["%02X" % struct.unpack("<B", c)[0] for c in random]),         # pylint: disable=C0209
                "Flags": "".join(["%02X" % struct.unpack("<B", c)[0] for c in flags]),          # pylint: disable=C0209
            }
            # fmt: on
        return {}

    def __del__(self) -> None:
        self.disconnect()


class ScanEntry:
    addrTypes: dict[int, str] = {1: ADDR_TYPE_PUBLIC, 2: ADDR_TYPE_RANDOM}

    FLAGS: int = 0x01
    INCOMPLETE_16B_SERVICES: int = 0x02
    COMPLETE_16B_SERVICES: int = 0x03
    INCOMPLETE_32B_SERVICES: int = 0x04
    COMPLETE_32B_SERVICES: int = 0x05
    INCOMPLETE_128B_SERVICES: int = 0x06
    COMPLETE_128B_SERVICES: int = 0x07
    SHORT_LOCAL_NAME: int = 0x08
    COMPLETE_LOCAL_NAME: int = 0x09
    TX_POWER: int = 0x0A
    SERVICE_SOLICITATION_16B: int = 0x14
    SERVICE_SOLICITATION_32B: int = 0x1F
    SERVICE_SOLICITATION_128B: int = 0x15
    SERVICE_DATA_16B: int = 0x16
    SERVICE_DATA_32B: int = 0x20
    SERVICE_DATA_128B: int = 0x21
    PUBLIC_TARGET_ADDRESS: int = 0x17
    RANDOM_TARGET_ADDRESS: int = 0x18
    APPEARANCE: int = 0x19
    ADVERTISING_INTERVAL: int = 0x1A
    MANUFACTURER: int = 0xFF

    dataTags: dict[int, str] = {
        FLAGS: "Flags",
        INCOMPLETE_16B_SERVICES: "Incomplete 16b Services",
        COMPLETE_16B_SERVICES: "Complete 16b Services",
        INCOMPLETE_32B_SERVICES: "Incomplete 32b Services",
        COMPLETE_32B_SERVICES: "Complete 32b Services",
        INCOMPLETE_128B_SERVICES: "Incomplete 128b Services",
        COMPLETE_128B_SERVICES: "Complete 128b Services",
        SHORT_LOCAL_NAME: "Short Local Name",
        COMPLETE_LOCAL_NAME: "Complete Local Name",
        TX_POWER: "Tx Power",
        SERVICE_SOLICITATION_16B: "16b Service Solicitation",
        SERVICE_SOLICITATION_32B: "32b Service Solicitation",
        SERVICE_SOLICITATION_128B: "128b Service Solicitation",
        SERVICE_DATA_16B: "16b Service Data",
        SERVICE_DATA_32B: "32b Service Data",
        SERVICE_DATA_128B: "128b Service Data",
        PUBLIC_TARGET_ADDRESS: "Public Target Address",
        RANDOM_TARGET_ADDRESS: "Random Target Address",
        APPEARANCE: "Appearance",
        ADVERTISING_INTERVAL: "Advertising Interval",
        MANUFACTURER: "Manufacturer",
    }

    def __init__(self, addr, iface) -> None:
        self.addr = addr
        self.iface = iface
        self.addrType = None
        self.rssi = None
        self.connectable = False
        self.rawData = None
        self.scanData = {}
        self.updateCount = 0

    def _decodeUUID(self, val, nbytes):
        if len(val) < nbytes:
            return None
        bval = bytearray(val)
        rs = ""
        # Bytes are little-endian; convert to big-endian string
        for i in range(nbytes):
            rs = f"{bval[i]:02X}{rs}"
        return UUID(rs)

    def _decodeUUIDlist(self, val, nbytes):
        result = []
        for i in range(0, len(val), nbytes):
            if len(val) >= (i + nbytes):
                result.append(self._decodeUUID(val[i : i + nbytes], nbytes))
        return result

    def getDescription(self, sdid) -> str:
        return self.dataTags.get(sdid, hex(sdid))

    def getValue(self, sdid):
        val = self.scanData.get(sdid, None)
        if val is None:
            return None
        if sdid in [ScanEntry.SHORT_LOCAL_NAME, ScanEntry.COMPLETE_LOCAL_NAME]:
            try:
                # Beware! Vol 3 Part C 18.3 doesn't give an encoding. Other references
                # to 'local name' (e.g. vol 3 E, 6.23) suggest it's UTF-8 but in practice
                # devices sometimes have garbage here. See #259, #275, #292.
                return val.decode("utf-8")
            except UnicodeDecodeError:
                bbval = bytearray(val)
                return "".join([(chr(x) if x in range(32, 127) else "?") for x in bbval])
        if sdid in [ScanEntry.INCOMPLETE_16B_SERVICES, ScanEntry.COMPLETE_16B_SERVICES]:
            return self._decodeUUIDlist(val, 2)
        if sdid in [ScanEntry.INCOMPLETE_32B_SERVICES, ScanEntry.COMPLETE_32B_SERVICES]:
            return self._decodeUUIDlist(val, 4)
        if sdid in [ScanEntry.INCOMPLETE_128B_SERVICES, ScanEntry.COMPLETE_128B_SERVICES]:
            return self._decodeUUIDlist(val, 16)
        return val

    def getValueText(self, sdid):
        val = self.getValue(sdid)
        if val is None:
            return None
        if sdid in [ScanEntry.SHORT_LOCAL_NAME, ScanEntry.COMPLETE_LOCAL_NAME]:
            return val
        if isinstance(val, list):
            return ",".join(str(v) for v in val)
        return binascii.b2a_hex(val).decode("ascii")

    def getScanData(self):
        """Return list of tuples [(tag, description, value)]"""
        return [
            (sdid, self.getDescription(sdid), self.getValueText(sdid))
            for sdid in self.scanData.keys()  # pylint: disable=consider-iterating-dictionary
        ]

    def update(self, resp) -> bool:
        addrType = self.addrTypes.get(resp["type"][0], None)
        if (self.addrType is not None) and (addrType != self.addrType):
            raise BTLEInternalError(f"Address type changed during scan, for address {self.addr}")
        self.addrType = addrType
        self.rssi = -resp["rssi"][0]
        self.connectable = (resp["flag"][0] & 0x4) == 0
        data = resp.get("d", [""])[0]
        self.rawData = data

        # Note: bluez is notifying devices twice: once with advertisement data,
        # then with scan response data. Also, the device may update the
        # advertisement or scan data
        isNewData = False
        while len(data) >= 2:
            sdlen, sdid = struct.unpack_from("<BB", data)
            val = data[2 : sdlen + 1]
            if (sdid not in self.scanData) or (val != self.scanData[sdid]):
                isNewData = True
            self.scanData[sdid] = val
            data = data[sdlen + 1 :]

        self.updateCount += 1
        return isNewData


class Scanner(Bluepy3Helper):
    def __init__(self, iface=0) -> None:
        Bluepy3Helper.__init__(self)
        self.scanned: dict = {}
        self.iface: int = iface
        self.passive: bool = False

    def _cmd(self) -> str:
        return "pasv" if self.passive else "scan"

    def start(self, passive: bool = False) -> None:
        self.passive = passive
        self._startHelper(iface=self.iface)
        self._mgmtCmd("le on")
        self._writeCmd(self._cmd() + "\n")
        rsp = self._waitResp("mgmt")
        if rsp["code"][0] == "success":
            return
        # Sometimes previous scan still ongoing
        if rsp["code"][0] == "busy":
            self._mgmtCmd(self._cmd() + "end")
            rsp = self._waitResp("stat")
            assert rsp["state"][0] == "disc"
            self._mgmtCmd(self._cmd())

    def stop(self) -> None:
        self._mgmtCmd(self._cmd() + "end")
        self._stopHelper()

    def clear(self) -> None:
        self.scanned = {}

    def process(self, timeout=10.0) -> None:
        if self._helper is None:
            raise BTLEInternalError("Helper not started (did you call start()?)")
        start = time.time()
        while True:
            if timeout:
                remain = start + timeout - time.time()
                if remain <= 0.0:
                    break
            else:
                remain = None
            resp = self._waitResp(["scan", "stat"], remain)
            if resp is None:
                break

            respType = resp["rsp"][0]
            if respType == "stat":
                # if scan ended, restart it
                if resp["state"][0] == "disc":
                    self._mgmtCmd(self._cmd())
            elif respType == "scan":
                # device found
                addr: str = binascii.b2a_hex(resp["addr"][0]).decode("utf-8")
                addr = ":".join([addr[i : i + 2] for i in range(0, 12, 2)])
                if addr in self.scanned:
                    dev = self.scanned[addr]
                else:
                    dev = ScanEntry(addr, self.iface)
                    self.scanned[addr] = dev
                isNewData = dev.update(resp)
                if self.delegate is not None:
                    self.delegate.handleDiscovery(dev, (dev.updateCount <= 1), isNewData)
            else:
                raise BTLEInternalError(f"Unexpected response: {respType}", resp)

    def getDevices(self):
        return list(self.scanned.values())

    def scan(self, timeout=10, passive=False):
        self.clear()
        self.start(passive=passive)
        self.process(timeout)
        self.stop()
        return self.getDevices()


def capitaliseName(descr: str) -> str:
    words = descr.replace("(", " ").replace(")", " ").replace("-", " ").split(" ")
    capWords = [words[0].lower()]
    capWords += [w[0:1].upper() + w[1:].lower() for w in words[1:]]
    return "".join(capWords)


class _UUIDNameMap:
    # Constructor sets self.currentTimeService, self.txPower, and so on
    # from names.
    def __init__(self, idList) -> None:
        self.idMap = {}
        for uuid in idList:
            attrName: str = capitaliseName(uuid.commonName)
            vars(self)[attrName] = uuid
            self.idMap[uuid] = uuid

    def getCommonName(self, uuid) -> str:
        if uuid in self.idMap:
            return self.idMap[uuid].commonName
        return ""


def get_json_uuid():
    uuid_entry = list[int, str, str]
    # an entry in the uuid_list is a list containing an `int`` and two `str`
    # example: [10082, 'day', 'time (day)']
    uuid_list = list[uuid_entry]
    # a list of `uuid_entry`s
    json_content = dict[str, uuid_list]
    # a dict containing the `uuid_lists`s. The key is the name of each list as a `str`
    _v: uuid_entry
    number: int
    cname: str
    name: str

    with open(os.path.join(script_path, "uuids.json"), "rb") as fp:
        _uuid_data: json_content = json.loads(fp.read().decode("utf-8"))
    for _, _v in _uuid_data.items():
        for number, cname, name in _v:
            yield UUID(number, cname)
            yield UUID(number, name)


AssignedNumbers = _UUIDNameMap(get_json_uuid())


if __name__ == "__main__":
    Debugging = True
    print(AssignedNumbers.device_name)
    if len(sys.argv) < 2:
        sys.exit(f"Usage:\n  {sys.argv[0]} <mac-address> [random]")

    # if not os.path.isfile(helperExe):
    #     raise ImportError(f"(btle.py) Cannot find required executable '{helperExe}'")

    my_device_address: str = sys.argv[1]
    if len(sys.argv) == 3:
        my_address_type: str = sys.argv[2]
    else:
        my_address_type = ADDR_TYPE_PUBLIC
    print(f"Connecting to: {my_device_address}, address type: {my_address_type}")
    conn = Peripheral(my_device_address, my_address_type)
    try:
        for service in conn.services:
            print(f"{str(service)}:")
            for ch in service.getCharacteristics():
                print(f"    {ch}, hnd={hex(ch.handle)}, supports {ch.propertiesToString()}")
                chName = AssignedNumbers.getCommonName(ch.uuid)
                if ch.supportsRead():
                    try:
                        print(f"    ->{repr(ch.read())}")
                    except BTLEException as e:
                        print(f"    ->{e}")

    finally:
        conn.disconnect()
