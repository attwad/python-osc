"""Class that maps OSC addresses to handlers."""
import collections
import logging
import re
import time
from pythonosc import osc_packet

class Handler(object):
  def __init__(self, _callback, _args, _needs_reply_address=False):
    self.callback = _callback
    self.args = _args
    self.needs_reply_address = _needs_reply_address

  # needed for test module
  def __eq__(self, other):
    return (type(self)==type(other) and
      self.callback==other.callback and
      self.args==other.args and
      self.needs_reply_address==other.needs_reply_address)

  def invoke(self, client_address, message):
    if self.needs_reply_address:
      if self.args:
        self.callback(client_address, message.address, self.args, *message)
      else:
        self.callback(client_address, message.address, *message)
    else:
      if self.args:
        self.callback(message.address, self.args, *message)
      else:
        self.callback(message.address, *message)

class Dispatcher(object):
  """Register addresses to handlers and can match vice-versa."""

  def __init__(self):
    self._map = collections.defaultdict(list)
    self._default_handler = None

  def map(self, address, handler, *args, needs_reply_address=False):
    """Map a given address to a handler.

    Args:
      - address: An explicit endpoint.
      - handler: A function that will be run when the address matches with
                 the OscMessage passed as parameter.
      - args: Any additional arguments that will be always passed to the
              handlers after the osc messages arguments if any.
      - needs_reply_address: True if the handler function needs the
              originating client address passed (as the first argument).
    """
    # TODO: Check the spec:
    # http://opensoundcontrol.org/spec-1_0
    # regarding multiple mappings
    self._map[address].append(Handler(handler, list(args), needs_reply_address))

  def handlers_for_address(self, address_pattern):
    """yields Handler namedtuples matching the given OSC pattern."""
    # First convert the address_pattern into a matchable regexp.
    # '?' in the OSC Address Pattern matches any single character.
    # Let's consider numbers and _ "characters" too here, it's not said
    # explicitly in the specification but it sounds good.
    escaped_address_pattern = re.escape(address_pattern)
    pattern = escaped_address_pattern.replace('\\?', '\\w?')
    # '*' in the OSC Address Pattern matches any sequence of zero or more
    # characters.
    pattern = pattern.replace('\\*', '[\w|\+]*')
    # The rest of the syntax in the specification is like the re module so
    # we're fine.
    pattern = pattern + '$'
    pattern = re.compile(pattern)
    matched = False

    for addr, handlers in self._map.items():
      if (pattern.match(addr)
        or (('*' in addr) and re.match(addr.replace('*','[^/]*?/*'), address_pattern))):
        yield from handlers
        matched = True

    if not matched and self._default_handler:
      logging.debug('No handler matched but default handler present, added it.')
      yield self._default_handler

  def call_handlers_for_packet(self, data, client_address):
    """
    This function calls the handlers registered to the dispatcher for
    every message it found in the packet.
    The process/thread granularity is thus the OSC packet, not the handler.

    If parameters were registered with the dispatcher, then the handlers are
    called this way:
      handler('/address that triggered the message',
              registered_param_list, osc_msg_arg1, osc_msg_arg2, ...)
    if no parameters were registered, then it is just called like this:
      handler('/address that triggered the message',
              osc_msg_arg1, osc_msg_arg2, osc_msg_param3, ...)
    """

    # Get OSC messages from all bundles or standalone message.
    try:
      packet = osc_packet.OscPacket(data)
      for timed_msg in packet.messages:
        now = time.time()
        handlers = self.handlers_for_address(
            timed_msg.message.address)
        if not handlers:
          continue
        # If the message is to be handled later, then so be it.
        if timed_msg.time > now:
          time.sleep(timed_msg.time - now)
        for handler in handlers:
          handler.invoke(client_address, timed_msg.message)
    except osc_packet.ParseError:
      pass

  def set_default_handler(self, handler, needs_reply_address=False):
    """Sets the default handler.

    Must be a function with the same constaints as with the self.map method
    or None to unset the default handler.
    """
    self._default_handler = None if (handler is None) else Handler(handler, [], needs_reply_address)
