"""Class that maps OSC addresses to handlers."""
import collections
import logging
import re
import time
from pythonosc import osc_packet
from typing import overload, List, Union, Any, Generator
from types import FunctionType
from pythonosc.osc_message import OscMessage


class Handler(object):
    def __init__(self, _callback: FunctionType, _args: Union[Any, List[Any]],
                 _needs_reply_address: bool = False) -> None:
        self.callback = _callback
        self.args = _args
        self.needs_reply_address = _needs_reply_address

    # needed for test module
    def __eq__(self, other) -> bool:
        return (type(self) == type(other) and
                self.callback == other.callback and
                self.args == other.args and
                self.needs_reply_address == other.needs_reply_address)

    def invoke(self, client_address: str, message: OscMessage) -> None:
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

    def __init__(self) -> None:
        self._map = collections.defaultdict(list)
        self._default_handler = None

    def map(self, address: str, handler: FunctionType, *args: Union[Any, List[Any]],
            needs_reply_address: bool = False) -> Handler:
        """Map a given address to a handler.

        Args:
          - address: An explicit endpoint.
          - handler: A function that will be run when the address matches with
                     the OscMessage passed as parameter.
          - args: Any additional arguments that will be always passed to the
                  handlers after the osc messages arguments if any.
          - needs_reply_address: True if the handler function needs the
                  originating client address passed (as the first argument).
          Returns:
          - Handler object
        """
        # TODO: Check the spec:
        # http://opensoundcontrol.org/spec-1_0
        # regarding multiple mappings
        handlerobj = Handler(handler, list(args), needs_reply_address)
        self._map[address].append(handlerobj)
        return handlerobj

    @overload
    def unmap(self, address: str, handler: Handler) -> None:
        """Remove an already mapped handler from an address

            Args:
              - address: An explicit endpoint.
              - handler: A Handler object as returned from map().
        """
        pass

    @overload
    def unmap(self, address: str, handler: FunctionType, *args: Union[Any, List[Any]],
              needs_reply_address: bool = False) -> None:
        """Remove an already mapped handler from an address

        Args:
          - address: An explicit endpoint.
          - handler: A function that will be run when the address matches with
                     the OscMessage passed as parameter.
          - args: Any additional arguments that will be always passed to the
                  handlers after the osc messages arguments if any.
          - needs_reply_address: True if the handler function needs the
                  originating client address passed (as the first argument).
        """
        pass

    def unmap(self, address, handler, *args, needs_reply_address=False):
        try:
            if isinstance(handler, Handler):
                self._map[address].remove(handler)
            else:
                self._map[address].remove(Handler(handler, list(args), needs_reply_address))
        except ValueError as e:
            if str(e) == "list.remove(x): x not in list":
                raise ValueError("Address '%s' doesn't have handler '%s' mapped to it" % (address, handler)) from e

    def handlers_for_address(self, address_pattern: str) -> Generator[None, Handler, None]:
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
        patterncompiled = re.compile(pattern)
        matched = False

        for addr, handlers in self._map.items():
            if (patterncompiled.match(addr)
                    or (('*' in addr) and re.match(addr.replace('*', '[^/]*?/*'), address_pattern))):
                yield from handlers
                matched = True

        if not matched and self._default_handler:
            logging.debug('No handler matched but default handler present, added it.')
            yield self._default_handler

    def call_handlers_for_packet(self, data, client_address) -> None:
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

    def set_default_handler(self, handler: FunctionType, needs_reply_address: bool = False) -> None:
        """Sets the default handler.

        Must be a function with the same constaints as with the self.map method
        or None to unset the default handler.
        """
        self._default_handler = None if (handler is None) else Handler(handler, [], needs_reply_address)
