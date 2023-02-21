.. _peripheral:

The ``Peripheral`` class
========================

Bluepy's ``Peripheral`` class encapsulates a connection to a Bluetooth LE peripheral. You create a ``Peripheral`` object directly by specifying its MAC address; when the connection is established, the services and characteristics offered by that device can be discovered and read or written.

Constructor
-----------

.. function:: Peripheral([deviceAddr=None, [addrType=ADDR_TYPE_PUBLIC [, iface=None [, timeout=None]]]])

   If *deviceAddr* is not ``None``, creates a ``Peripheral`` object and makes a connection
   to the device indicated by *deviceAddr*. *deviceAddr* should be a string comprising six hex
   bytes separated by colons, e.g. ``"11:22:33:ab:cd:ed"``.

   If *deviceAddr* is ``None``, creates an un-connected ``Peripheral`` object. You must call the ``connect()`` method on this object (passing it a device address) before it will be usable.

   The *addrType* parameter can be used to select between fixed (``btle.ADDR_TYPE_PUBLIC``)
   and random (``btle.ADDR_TYPE_RANDOM``) address types, depending on what the target
   peripheral requires. See section 10.8 of the Bluetooth 4.0 specification for more
   details.

   The *iface* parameter allows the Bluetooth interface on which to make the connection to be set.
   On Linux, 0 means */dev/hci0*, 1 means */dev/hci1* and so on.

   The *timeout* parameter (in seconds) can be used to limit the hang time for trying to connect to device.

   *deviceAddr* may also be a ``ScanEntry`` object. In this case the device address,
   address type, and interface number are all taken from the ``ScanEntry`` values, and
   the *addrType* and *iface* parameters are ignored.

   The constructor will throw a ``BTLEException`` if connection to the device fails.

Instance Methods
----------------

.. function:: connect(addr, [addrType=ADDR_TYPE_PUBLIC [, iface=None [, timeout=None]]])

    Makes a connection to the device indicated by *addr*, with address type
    *addrType* and interface number *iface* and a timeout parameter *timeout* (see the ``Peripheral`` constructor for details).
    You should only call
    this method if the ``Peripheral`` is un-connected (i.e. you did not pass a *addr*
    to the constructor); a given peripheral object cannot be re-connected once connected.

.. function:: disconnect()

    Drops the connection to the device, and cleans up associated OS resources. Although the
    Python destructor for a ``Peripheral`` will attempt to call this method, you should not
    rely on this happening at any particular time. Therefore, always explicitly call
    ``disconnect()`` if you have finished communicating with a device.

.. function:: getState()

    Returns a string indicating device state. Possible states are: "conn" - connected,
    "disc" - disconnected, "scan" scanning and "tryconn" - connecting.

.. function:: getServices()

    Returns a list of ``Service`` objects representing the services offered by the peripheral.
    This will perform Bluetooth service discovery if this has not already been done;
    otherwise it will return a cached list of services immediately.

    On Python 3.x, this returns a *dictionary view* object, not a list.

.. function:: getServiceByUUID( uuidVal )

    Returns an instance of a ``Service`` object which has the indicated UUID.
    ``uuidVal`` can be a ``UUID`` object, or any string or integer which can be
    used to construct a ``UUID`` object. The method will return immediately if the
    service was previously discovered (e.g. by *getServices()*), and will query
    the peripheral otherwise. It raises a *BTLEEException* if the service is not
    found.

.. function:: getCharacteristics(startHnd=1, endHnd=0xFFFF, uuid=None)

    Returns a list containing ``Characteristic`` objects for the peripheral. If no
    arguments are given, will return all characteristics. If *startHnd* and/or
    *endHnd* are given, the list is restricted to characteristics whose handles are
    within the given range - note that it's usually more convenient to use
    ``Service.getCharacteristics()`` to get the characteristics associated with
    a particular service. Alternatively, *uuid* may be specified to locate a
    characteristic with a particular UUID value. *uuid* may be any string, integer,
    or ``UUID`` type which can be used to construct a ``UUID`` object.

    If no matching characteristics are found, returns an empty list.

.. function:: getDescriptors(startHnd=1, endHnd=0xFFFF)

    Returns a list containing ``Descriptor`` objects for the peripheral. If no
    arguments are given, will return all descriptors. If *startHnd* and/or
    *endHnd* are given, the list is restricted to descriptors whose handles are
    within the given range. Again, it's usually more convenient to use
    ``Service.getDescriptors()`` to get the descriptors associated with
    a particular service.

    If no matching descriptors are found, returns an empty list.

.. function:: withDelegate(delegate)

    This stores a reference to a "delegate" object, which is called when asynchronous
    events such as Bluetooth notifications occur. This should be a subclass of the
    ``DefaultDelegate`` class. See :ref:`notifications` for more information. This
    method returns the ``Peripheral`` object.

.. function:: setDelegate(delegate)

    *(deprecated since 0.9.10)* Same as *withDelegate()*.

.. function:: waitForNotifications(timeout)

    Blocks until a notification is received from the peripheral, or until the
    given *timeout* (in seconds) has elapsed. If a notification is received, the
    delegate object's ``handleNotification()`` method will be called, and
    ``waitForNotifications()`` will then return ``True``.

    If nothing is received before the timeout elapses, this will return ``False``.

.. function:: writeCharacteristic(handle, val, withResponse=False)

    Writes the data *val* (of type ``str`` on Python 2.x, ``byte`` on 3.x) to the
    characteristic identified by handle *handle*, which should be an integer in the
    range 1 to 65535. This is useful if you know a characteristic's GATT handle,
    but do not have a ``Characteristic`` object.

    If *withResponse* is true, will await confirmation that the write was successful
    from the device.

.. function:: readCharacteristic(handle)

    Reads the current value of the characteristic identified by *handle*. This is
    useful if you know the handle for the characteristic but do not have a suitable
    ``Characteristic`` object.

Properties
----------

All the properties listed below are read-only.

.. py:attribute:: addr

    Device MAC address (as a hex string separated by colons).

.. py:attribute:: addrType

    Device address type - one of *ADDR_TYPE_PUBLIC* or *ADDR_TYPE_RANDOM*; this will be a
    printable string.

.. py:attribute:: iface

    Bluetooth interface number (0 = ``/dev/hci0``) used for the connection.
