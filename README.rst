==========
python-osc
==========

Open Sound Control server and client implementations in **pure python** (3.5+).

.. image:: https://github.com/attwad/python-osc/actions/workflows/python-test.yml/badge.svg
    :target: https://github.com/attwad/python-osc/actions/workflows/python-test.yml


Current status
==============

This library was developped following the specifications at
http://opensoundcontrol.org/spec-1_0
and is currently in a stable state.

Features
========

* UDP blocking/threading/forking/asyncio server implementations
* UDP client
* int, int64, float, string, double, MIDI, timestamps, blob OSC arguments
* simple OSC address<->callback matching system
* extensive unit test coverage
* basic client and server examples

Documentation
=============

Available at https://python-osc.readthedocs.io/.

Installation
============

python-osc is a pure python library that has no external dependencies,
to install it just use pip (prefered):

.. image:: https://img.shields.io/pypi/v/python-osc.svg
    :target: https://pypi.python.org/pypi/python-osc

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

  """Small example OSC client

  This program sends 10 random values between 0.0 and 1.0 to the /filter address,
  waiting for 1 seconds between each value.
  """
  import argparse
  import random
  import time

  from pythonosc import udp_client


  if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1",
        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=5005,
        help="The port the OSC server is listening on")
    args = parser.parse_args()

    client = udp_client.SimpleUDPClient(args.ip, args.port)

    for x in range(10):
      client.send_message("/filter", random.random())
      time.sleep(1)

Simple server
-------------

.. code-block:: python

  """Small example OSC server

  This program listens to several addresses, and prints some information about
  received packets.
  """
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
    dispatcher.map("/filter", print)
    dispatcher.map("/volume", print_volume_handler, "Volume")
    dispatcher.map("/logvolume", print_compute_handler, "Log volume", math.log)

    server = osc_server.ThreadingOSCUDPServer(
        (args.ip, args.port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()

Building bundles
----------------

.. code-block:: python

    from pythonosc import osc_bundle_builder
    from pythonosc import osc_message_builder

    bundle = osc_bundle_builder.OscBundleBuilder(
        osc_bundle_builder.IMMEDIATELY)
    msg = osc_message_builder.OscMessageBuilder(address="/SYNC")
    msg.add_arg(4.0)
    # Add 4 messages in the bundle, each with more arguments.
    bundle.add_content(msg.build())
    msg.add_arg(2)
    bundle.add_content(msg.build())
    msg.add_arg("value")
    bundle.add_content(msg.build())
    msg.add_arg(b"\x01\x02\x03")
    bundle.add_content(msg.build())

    sub_bundle = bundle.build()
    # Now add the same bundle inside itself.
    bundle.add_content(sub_bundle)
    # The bundle has 5 elements in total now.

    bundle = bundle.build()
    # You can now send it via a client as described in other examples.

License?
========
Unlicensed, do what you want with it. (http://unlicense.org)
