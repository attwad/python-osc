"""OSC Servers that receive UDP packets and invoke handlers accordingly.

Use like this:

dispatcher = dispatcher.Dispatcher()
# This will print all parameters to stdout.
dispatcher.map("/bpm", print)
server = ForkingOSCUDPServer((ip, port), dispatcher)
server.serve_forever()

or run the server on its own thread:
server = ForkingOSCUDPServer((ip, port), dispatcher)
server_thread = threading.Thread(target=server.serve_forever)
server_thread.start()
...
server.shutdown()


Those servers are using the standard socketserver from the standard library:
http://docs.python.org/library/socketserver.html


Alternatively, the AsyncIOOSCUDPServer server can be integrated with an
asyncio event loop:

loop = asyncio.get_event_loop()
server = AsyncIOOSCUDPServer(server_address, dispatcher, loop)
server.serve()
loop.run_forever()

"""

import asyncio
import os
import socketserver

from pythonosc import osc_bundle
from pythonosc import osc_message




class _UDPHandler(socketserver.BaseRequestHandler):
  """Handles correct UDP messages for all types of server.

  Whether this will be run on its own thread, the server's or a whole new
  process depends on the server you instanciated, look at their documentation.

  This method is called after a basic sanity check was done on the datagram,
  basically whether this datagram looks like an osc message or bundle,
  if not the server won't even bother to call it and so no new
  threads/processes will be spawned.
  """
  def handle(self):
    self.server.dispatcher.call_handlers_for_packet(self.request[0], self.client_address)


def _is_valid_request(request):
  """Returns true if the request's data looks like an osc bundle or message."""
  data = request[0]
  return (
      osc_bundle.OscBundle.dgram_is_bundle(data)
      or osc_message.OscMessage.dgram_is_message(data))


class OSCUDPServer(socketserver.UDPServer):
  """Superclass for different flavors of OSCUDPServer"""

  def __init__(self, server_address, dispatcher):
    super().__init__(server_address, _UDPHandler)
    self._dispatcher = dispatcher

  def verify_request(self, request, client_address):
    """Returns true if the data looks like a valid OSC UDP datagram."""
    return _is_valid_request(request)

  @property
  def dispatcher(self):
    """Dispatcher accessor for handlers to dispatch osc messages."""
    return self._dispatcher


class BlockingOSCUDPServer(OSCUDPServer):
  """Blocking version of the UDP server.

  Each message will be handled sequentially on the same thread.
  Use this is you don't care about latency in your message handling or don't
  have a multiprocess/multithread environment (really?).
  """


class ThreadingOSCUDPServer(socketserver.ThreadingMixIn, OSCUDPServer):
  """Threading version of the OSC UDP server.

  Each message will be handled in its own new thread.
  Use this when lightweight operations are done by each message handlers.
  """


if hasattr(os, "fork"):
  class ForkingOSCUDPServer(socketserver.ForkingMixIn, OSCUDPServer):
    """Forking version of the OSC UDP server.

    Each message will be handled in its own new process.
    Use this when heavyweight operations are done by each message handlers
    and forking a whole new process for each of them is worth it.
    """


class AsyncIOOSCUDPServer():
  """Asyncio version of the OSC UDP Server.
  Each UDP message is handled by call_handlers_for_packet, the same method as in the
  OSCUDPServer family of blocking, threading, and forking servers
  """

  def __init__(self, server_address, dispatcher, loop):
    """
    :param server_address: tuple of (IP address to bind to, port)
    :param dispatcher: a pythonosc.dispatcher.Dispatcher
    :param loop: an asyncio event loop
    """

    self._server_address = server_address
    self._dispatcher = dispatcher
    self._loop = loop

  class _OSCProtocolFactory(asyncio.DatagramProtocol):
    """OSC protocol factory which passes datagrams to dispatcher"""

    def __init__(self, dispatcher):
      self.dispatcher = dispatcher

    def datagram_received(self, data, client_address):
      self.dispatcher.call_handlers_for_packet(data, client_address)

  def serve(self):
    """Creates a datagram endpoint and registers it with our event loop.

    Use this only if you are not currently running your asyncio loop.
    (i.e. not from within a coroutine).
    """
    self._loop.run_until_complete(self.create_serve_endpoint())

  def create_serve_endpoint(self):
    """Creates a datagram endpoint and registers it with our event loop as coroutine."""
    return self._loop.create_datagram_endpoint(
      lambda: self._OSCProtocolFactory(self.dispatcher),
      local_addr=self._server_address)

  @property
  def dispatcher(self):
    return self._dispatcher
