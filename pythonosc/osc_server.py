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
server_thread.Start()
...
server.shutdown()


Those servers are using the standard socketserver from the standard library:
http://docs.python.org/library/socketserver.html
"""

import calendar
import socketserver
import time

from pythonosc import osc_bundle
from pythonosc import osc_message
from pythonosc import osc_packet

class _UDPHandler(socketserver.BaseRequestHandler):
  """Handles correct UDP messages for all types of server.

  Whether this will be run on its own thread, the server's or a whole new
  process depends on the server you instanciated, look at their documentation.

  This method is called after a basic sanity check was done on the datagram,
  basically whether this datagram looks like an osc message or bundle,
  if not the server won't even bother to call it and so no new threads/processes
  will be spawned.

  This method calls the handlers registered to the server's dispatcher for
  every message it found in the packet.
  The process/thread granularity is thus the OSC packet, not the handler.

  If parameters were registered with the dispatcher, then the handlers are called this way:
    handler(registered_param_list, osc_msg_arg1, osc_msg_arg2, ...)
  if no parameters were registered, then it is just called like this:
    handler(osc_msg_arg1, osc_msg_arg2, osc_msg_param3, ...)
  """
  def handle(self):
    data = self.request[0].strip()
    # Get OSC messages from all bundles or standalone message.
    try:
      packet = osc_packet.OscPacket(data)
      for timed_msg in packet.messages:
        now = calendar.timegm(time.gmtime())
        handlers = self.server.dispatcher.handlers_for_address(
            timed_msg.message.address)
        if not handlers: continue
        # If the message is to be handled later, then so be it.
        if timed_msg.time > now:
          time.sleep(timed_msg.time - now)
        for handler in handlers:
          # TODO: Use namedtuples.
          if handler[1]:
            handler[0](handler[1], *timed_msg.message)
          else:
            handler[0](*timed_msg.message)
    except osc_packet.ParseError as pe:
      pass


def _is_valid_request(request):
  """Returns true if the request's data looks like an osc bundle or message."""
  data = request[0]
  return (
      osc_bundle.OscBundle.dgram_is_bundle(data)
      or osc_message.OscMessage.dgram_is_message(data))


class BlockingOSCUDPServer(socketserver.UDPServer):
  """Blocking version of the UDP server.

  Each message will be handled sequentially on the same thread.
  Use this is you don't care about latency in your message handling or don't
  have a multiprocess/multithread environment (really?).
  """

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

class ThreadingOSCUDPServer(
    socketserver.ThreadingMixIn, socketserver.UDPServer):
  """Threading version of the OSC UDP server.

  Each message will be handled in its own new thread.
  Use this when lightweight operations are done by each message handlers.
  """

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


class ForkingOSCUDPServer(
    socketserver.ForkingMixIn, socketserver.UDPServer):
  """Forking version of the OSC UDP server.
 
  Each message will be handled in its own new process.
  Use this when heavyweight operations are done by each message handlers
  and forking a whole new process for each of them is worth it.
  """

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
