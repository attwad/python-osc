Dispatcher
============

The dispatcher maps OSC addresses to functions and calls the functions with the messages' arguments.
Function can also be mapped to wildcard addresses.


Example
---------

.. code-block:: python

    from pythonosc.dispatcher import Dispatcher
    from typing import List, Any

    dispatcher = Dispatcher()


    def set_filter(address: str, *args: List[Any]) -> None:
        # We expect two float arguments
        if not len(args) == 2 or type(args[0]) is not float or type(args[1]) is not float:
            return

        # Check that address starts with filter
        if not address[:-1] == "/filter":  # Cut off the last character
            return

        value1 = args[0]
        value2 = args[1]
        filterno = address[-1]
        print(f"Setting filter {filterno} values: {value1}, {value2}")


    dispatcher.map("/filter*", set_filter)  # Map wildcard address to set_filter function

    # Set up server and client for testing
    from pythonosc.osc_server import BlockingOSCUDPServer
    from pythonosc.udp_client import SimpleUDPClient

    server = BlockingOSCUDPServer(("127.0.0.1", 1337), dispatcher)
    client = SimpleUDPClient("127.0.0.1", 1337)

    # Send message and receive exactly one message (blocking)
    client.send_message("/filter1", [1., 2.])
    server.handle_request()

    client.send_message("/filter8", [6., -2.])
    server.handle_request()


Mapping
---------

The dispatcher associates addresses with functions by storing them in a mapping.
An address can contains wildcards as defined in the OSC specifications.
Call the ``Dispatcher.map`` method with an address pattern and a handler callback function:

.. code-block:: python

    from pythonosc.dispatcher import Dispatcher
    disp = Dispatcher()
    disp.map("/some/address*", some_printing_func)

This will for example print any OSC messages starting with ``/some/address``.

Additionally you can provide any amount of extra fixed argument that will always be passed before the OSC message arguments:

.. code-block:: python

    handler = disp.map("/some/other/address", some_printing_func, "This is a fixed arg", "and this is another fixed arg")

The handler callback signature must look like this:

.. code-block:: python

    def some_callback(address: str, *osc_arguments: List[Any]) -> None:
    def some_callback(address: str, fixed_argument: List[Any], *osc_arguments: List[Any]) -> None:

Instead of a list you can of course also use a fixed amount of arguments for ``osc_arguments``

The ``Dispatcher.map`` method returns a ``Handler`` object, which can be used to remove the mapping from the dispatcher.


Unmapping
-----------

A mapping can be undone with the ``Dispatcher.unmap`` method, which takes an address and ``Handler`` object as arguments.
For example, to unmap the mapping from the `Mapping`_ section:

.. code-block:: python

    disp.unmap("some/other/address", handler)

Alternatively the handler can be reconstructed from a function and optional fixed argument:

.. code-block:: python

    disp.unmap("some/other/address", some_printing_func, *some_fixed_args)

If the provided mapping doesn't exist, a ``ValueError`` is raised.


Default Handler
-----------------

It is possible to specify a handler callback function that is called for every unmatched address:

.. code-block:: python

    disp.set_default_handler(some_handler_function)

This is extremely useful if you quickly need to find out what addresses an undocumented device is transmitting on or for building a learning function for some controls.
The handler must have the same signature as map callbacks:

.. code-block:: python

    def some_callback(address: str, *osc_arguments: List[Any]) -> None:



Dispatcher Module Documentation
---------------------------------

.. automodule:: pythonosc.dispatcher
  :special-members:
  :members:
  :exclude-members: __weakref__
