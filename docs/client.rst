Client
========

The client allows you to connect and send messages to an OSC server. The client class expects an :class:`OSCMessage` object, which is then sent out via UDP. Additionally, a simple client class exists that constructs the :class:`OSCMessage` object for you.

Example
---------

.. code-block:: python

    from pythonosc.udp_client import SimpleUDPClient

    ip = "127.0.0.1"
    port = 1337

    client = SimpleUDPClient(ip, port)  # Create client

    client.send_message("/some/address", 123)   # Send float message
    client.send_message("/some/address", [1, 2., "hello"])  # Send message with int, float and string


Client Module Documentation
---------------------------------

.. automodule:: pythonosc.udp_client
  :special-members:
  :members:
  :exclude-members: __weakref__
