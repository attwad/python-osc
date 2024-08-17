Client
========

The client allows you to connect and exchange messages with an OSC server.
Client classes are available for UDP and TCP protocols.
The base client class ``send`` method expects an :class:`OSCMessage` object, which is then sent out over TCP or UDP.
Additionally, a simple client class exists that constructs the :class:`OSCMessage` object for you.

See the examples folder for more use cases.

Examples
---------

.. code-block:: python

    from pythonosc.udp_client import SimpleUDPClient

    ip = "127.0.0.1"
    port = 1337

    client = SimpleUDPClient(ip, port)  # Create client

    client.send_message("/some/address", 123)   # Send float message
    client.send_message("/some/address", [1, 2., "hello"])  # Send message with int, float and string


.. code-block:: python

    from pythonosc.tcp_client import SimpleTCPClient

    ip = "127.0.0.1"
    port = 1337

    client = SimpleTCPClient(ip, port)  # Create client

    client.send_message("/some/address", 123)   # Send float message
    client.send_message("/some/address", [1, 2., "hello"])  # Send message with int, float and string

Client Module Documentation
---------------------------------

.. automodule:: pythonosc.udp_client
  :special-members:
  :members:
  :exclude-members: __weakref__

.. automodule:: pythonosc.tcp_client
  :special-members:
  :members:
  :exclude-members: __weakref__
