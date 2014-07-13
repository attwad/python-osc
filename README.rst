==========
python-osc
==========

Open Sound Control server and client implementations in **pure python** (3.3+).

Current status
==============

This library was developped following the specifications at
http://opensoundcontrol.org/spec-1_0
and is currently in a stable state.

Features
========

* UDP blocking/threading/forking server implementations
* UDP client
* int, float, string, blob OSC arguments
* simple OSC address<->callback matching system
* extensive unit test coverage
* basic client and server examples

Installation
============

python-osc is a pure python library that has no external dependencies,
to install it just use pip (prefered):

.. code-block:: bash

    $ pip install python-osc

or from the raw sources for the development version:

.. code-block:: bash

    $ python setup.py test
    $ python setup.py install

Examples
========

Simple client
-------------

.. code-block:: python

  """
  This program sends 10 random values between 0.0 and 1.0 to the /filter address,
  waiting for 1 seconds between each value.
  """
  import argparse
  import random
  import time

  from pythonosc import osc_message_builder
  from pythonosc import udp_client


  if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1",
        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=8000,
        help="The port the OSC server is listening on")
    args = parser.parse_args()

    client = udp_client.UDPClient(args.ip, args.port)

    for x in range(10):
      msg = osc_message_builder.OscMessageBuilder(address = "/filter")
      msg.add_arg(random.random())
      msg = msg.build()
      client.send(msg)
      time.sleep(1)


Simple server
-------------

.. code-block:: python

  import argparse
  import math

  from pythonosc import dispatcher
  from pythonosc import osc_server

  def print_volume_handler(unused_addr, args, volume):
    print("[{0}] ~ {1}".format(args[0], volume))

  def print_compute_handler(unused_addr, args, volume):
    try:
      print("[{0}] ~ {1}".format(args[0], args[1](volume)))
    except ValueError: pass

  if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
        default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port",
        type=int, default=5005, help="The port to listen on")
    args = parser.parse_args()

    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/debug", print)
    dispatcher.map("/volume", print_volume_handler, "Volume")
    dispatcher.map("/logvolume", print_compute_handler, "Log volume", math.log)

    server = osc_server.ThreadingOSCUDPServer(
        (args.ip, args.port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()

License?
========
WTFPL (http://www.wtfpl.net)
