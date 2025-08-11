"""Maps OSC addresses to handler functions"""

import collections
import inspect
import logging
import re
import time
from pythonosc import osc_packet
from typing import (
    overload,
    List,
    Union,
    Any,
    AnyStr,
    Generator,
    Tuple,
    Callable,
    Optional,
    DefaultDict,
)
from pythonosc.osc_message import OscMessage
from pythonosc.osc_message_builder import ArgValue


class Handler(object):
    """Wrapper for a callback function that will be called when an OSC message is sent to the right address.

    Represents a handler callback function that will be called whenever an OSC message is sent to the address this
    handler is mapped to. It passes the address, the fixed arguments (if any) as well as all osc arguments from the
    message if any were passed.
    """

    def __init__(
        self,
        _callback: Callable,
        _args: Union[Any, List[Any]],
        _needs_reply_address: bool = False,
    ) -> None:
        """
        Args:
            _callback Function that is called when handler is invoked
            _args: Message causing invocation
            _needs_reply_address Whether the client's ip address shall be passed as an argument or not
        """
        self.callback = _callback
        self.args = _args
        self.needs_reply_address = _needs_reply_address

    # needed for test module
    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(self, type(other))
            and self.callback == other.callback
            and self.args == other.args
            and self.needs_reply_address == other.needs_reply_address
        )

    def invoke(
        self, client_address: Tuple[str, int], message: OscMessage
    ) -> Union[None, AnyStr, Tuple[AnyStr, ArgValue]]:
        """Invokes the associated callback function

        Args:
            client_address: Address match that causes the invocation
            message: Message causing invocation
        Returns:
            The result of the handler function can be None, a string OSC address, or a tuple of the OSC address
            and arguments.
        """
        if self.needs_reply_address:
            if self.args:
                return self.callback(
                    client_address, message.address, self.args, *message
                )
            else:
                return self.callback(client_address, message.address, *message)
        else:
            if self.args:
                return self.callback(message.address, self.args, *message)
            else:
                return self.callback(message.address, *message)


class Dispatcher(object):
    """Maps Handlers to OSC addresses and dispatches messages to the handler on matched addresses

    Maps OSC addresses to handler functions and invokes the correct handler when a message comes in.
    """

    def __init__(self) -> None:
        self._map: DefaultDict[str, List[Handler]] = collections.defaultdict(list)
        self._default_handler: Optional[Handler] = None

    def map(
        self,
        address: str,
        handler: Callable,
        *args: Union[Any, List[Any]],
        needs_reply_address: bool = False,
    ) -> Handler:
        """Map an address to a handler

        The callback function must have one of the following signatures:

        ``def some_cb(address: str, *osc_args: List[Any]) -> Union[None, AnyStr, Tuple(str, ArgValue)]:``
        ``def some_cb(address: str, fixed_args: List[Any], *osc_args: List[Any]) -> Union[None, AnyStr,
                                                                                          Tuple(str, ArgValue)]:``

        ``def some_cb(client_address: Tuple[str, int], address: str, *osc_args: List[Any]) -> Union[None, AnyStr,
                                                                                                    Tuple(str, ArgValue)]:``
        ``def some_cb(client_address: Tuple[str, int], address: str, fixed_args: List[Any], *osc_args: List[Any]) -> Union[None, AnyStr, Tuple(str, ArgValue)]:``

        The callback function can return None, or a string representing an OSC address to be returned to the client,
        or a tuple that includes the address and ArgValue which will be converted to an OSC message and returned to
        the client.

        Args:
            address: Address to be mapped
            handler: Callback function that will be called as the handler for the given address
            *args: Fixed arguements that will be passed to the callback function
            needs_reply_address: Whether the IP address from which the message originated from shall be passed as
                an argument to the handler callback

        Returns:
            The handler object that will be invoked should the given address match

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
            address (str): Address to be unmapped
            handler (Handler): A Handler object as returned from map().
        """
        pass

    @overload
    def unmap(
        self,
        address: str,
        handler: Callable,
        *args: Union[Any, List[Any]],
        needs_reply_address: bool = False,
    ) -> None:
        """Remove an already mapped handler from an address

        Args:
            address: Address to be unmapped
            handler: A function that will be run when the address matches with
                the OscMessage passed as parameter.
            args: Any additional arguments that will be always passed to the
                handlers after the osc messages arguments if any.
            needs_reply_address: True if the handler function needs the
                originating client address passed (as the first argument).
        """
        pass

    def unmap(self, address, handler, *args, needs_reply_address=False):
        try:
            if isinstance(handler, Handler):
                self._map[address].remove(handler)
            else:
                self._map[address].remove(
                    Handler(handler, list(args), needs_reply_address)
                )
        except ValueError as e:
            if str(e) == "list.remove(x): x not in list":
                raise ValueError(
                    f"Address '{address}' doesn't have handler '{handler}' mapped to it"
                ) from e

    def handlers_for_address(
        self, address_pattern: str
    ) -> Generator[Handler, None, None]:
        """Yields handlers matching an address


        Args:
            address_pattern: Address to match

        Returns:
            Generator yielding Handlers matching address_pattern
        """
        # First convert the address_pattern into a matchable regexp.
        # '?' in the OSC Address Pattern matches any single character.
        # Let's consider numbers and _ "characters" too here, it's not said
        # explicitly in the specification but it sounds good.
        escaped_address_pattern = re.escape(address_pattern)
        pattern = escaped_address_pattern.replace("\\?", "\\w?")
        # '*' in the OSC Address Pattern matches any sequence of zero or more
        # characters.
        pattern = pattern.replace("\\*", "[\\w|\\+]*")
        # The rest of the syntax in the specification is like the re module so
        # we're fine.
        pattern = f"{pattern}$"
        patterncompiled = re.compile(pattern)
        matched = False

        for addr, handlers in self._map.items():
            if patterncompiled.match(addr) or (
                ("*" in addr)
                and re.match(addr.replace("*", "[^/]*?/*"), address_pattern)
            ):
                yield from handlers
                matched = True

        if not matched and self._default_handler:
            logging.debug("No handler matched but default handler present, added it.")
            yield self._default_handler

    def call_handlers_for_packet(
        self, data: bytes, client_address: Tuple[str, int]
    ) -> List:
        """Invoke handlers for all messages in OSC packet

        The incoming OSC Packet is decoded and the handlers for each included message is found and invoked.

        Args:
            data: Data of packet
            client_address: Address of client this packet originated from
        Returns: A list of strings or tuples to be converted to OSC messages and returned to the client
        """
        results = list()
        # Get OSC messages from all bundles or standalone message.
        try:
            packet = osc_packet.OscPacket(data)
            for timed_msg in packet.messages:
                now = time.time()
                handlers = self.handlers_for_address(timed_msg.message.address)
                if not handlers:
                    continue
                # If the message is to be handled later, then so be it.
                if timed_msg.time > now:
                    time.sleep(timed_msg.time - now)
                for handler in handlers:
                    result = handler.invoke(client_address, timed_msg.message)
                    if result is not None:
                        results.append(result)
        except osc_packet.ParseError:
            pass
        return results

    async def async_call_handlers_for_packet(
        self, data: bytes, client_address: Tuple[str, int]
    ) -> List:
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
        results = []
        try:
            packet = osc_packet.OscPacket(data)
            for timed_msg in packet.messages:
                now = time.time()
                handlers = self.handlers_for_address(timed_msg.message.address)
                if not handlers:
                    continue
                # If the message is to be handled later, then so be it.
                if timed_msg.time > now:
                    time.sleep(timed_msg.time - now)
                for handler in handlers:
                    if inspect.iscoroutinefunction(handler.callback):
                        if handler.needs_reply_address:
                            result = await handler.callback(
                                client_address,
                                timed_msg.message.address,
                                handler.args,
                                *timed_msg.message,
                            )
                        elif handler.args:
                            result = await handler.callback(
                                timed_msg.message.address,
                                handler.args,
                                *timed_msg.message,
                            )
                        else:
                            result = await handler.callback(
                                timed_msg.message.address, *timed_msg.message
                            )
                    else:
                        if handler.needs_reply_address:
                            result = handler.callback(
                                client_address,
                                timed_msg.message.address,
                                handler.args,
                                *timed_msg.message,
                            )
                        elif handler.args:
                            result = handler.callback(
                                timed_msg.message.address,
                                handler.args,
                                *timed_msg.message,
                            )
                        else:
                            result = handler.callback(
                                timed_msg.message.address, *timed_msg.message
                            )
                    if result:
                        results.append(result)
        except osc_packet.ParseError as e:
            pass
        return results

    def set_default_handler(
        self, handler: Callable, needs_reply_address: bool = False
    ) -> None:
        """Sets the default handler

        The default handler is invoked every time no other handler is mapped to an address.

        Args:
            handler: Callback function to handle unmapped requests
            needs_reply_address: Whether the callback shall be passed the client address
        """
        self._default_handler = (
            None if (handler is None) else Handler(handler, [], needs_reply_address)
        )
