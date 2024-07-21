# TODO: timeouts!


"""OSC Servers that receive TCP packets and invoke handlers accordingly.

Use like this:

dispatcher = dispatcher.Dispatcher()
# This will print all parameters to stdout.
dispatcher.map("/bpm", print)
server = ForkingOSCTCPServer((ip, port), dispatcher)
server.serve_forever()

or run the server on its own thread:
server = ForkingOSCTCPServer((ip, port), dispatcher)
server_thread = threading.Thread(target=server.serve_forever)
server_thread.start()
...
server.shutdown()


Those servers are using the standard socketserver from the standard library:
http://docs.python.org/library/socketserver.html


Alternatively, the AsyncIOOSCTCPServer server can be integrated with an
asyncio event loop:

loop = asyncio.get_event_loop()
server = AsyncIOOSCTCPServer(server_address, dispatcher)
server.serve()
loop.run_forever()

"""

import asyncio
import inspect
import logging
import os
import socketserver
import struct
import time

from pythonosc import osc_message_builder, osc_packet, slip

LOG = logging.getLogger()
MODE_1_0 = "1.0"
MODE_1_1 = "1.1"


def _call_handlers_for_packet(data, dispatcher):
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
    all_resp = []
    try:
        LOG.debug("_call_handlers_for_packet: data ", data)
        packet = osc_packet.OscPacket(data)
        for timed_msg in packet.messages:
            now = time.time()
            handlers = dispatcher.handlers_for_address(
                timed_msg.message.address)
            if not handlers:
                continue
            # If the message is to be handled later, then so be it.
            if timed_msg.time > now:
                time.sleep(timed_msg.time - now)
            for handler in handlers:
                if handler.args:
                    resp = handler.callback(
                        timed_msg.message.address, handler.args, *timed_msg.message)
                else:
                    resp = handler.callback(timed_msg.message.address, *timed_msg.message)
                if resp:
                    all_resp.append(resp)
    except osc_packet.ParseError:
        pass
    return all_resp


class _TCPHandler1_0(socketserver.BaseRequestHandler):
    """Handles correct OSC1.0 messages.

    Whether this will be run on its own thread, the server's or a whole new
    process depends on the server you instantiated, look at their documentation.

    This method is called after a basic sanity check was done on the datagram,
    basically whether this datagram looks like an osc message or bundle,
    if not the server won't even bother to call it and so no new
    threads/processes will be spawned.
    """
    def handle(self):
        LOG.debug("handle OSC 1.0 protocol")
        while True:
            lengthbuf = self.recvall(4)
            if lengthbuf is None:
                break
            length, = struct.unpack('!I', lengthbuf)
            data = self.recvall(length)
            if data is None:
                break

            resp = _call_handlers_for_packet(data, self.server.dispatcher)
            for r in resp:
                if r is not None:
                    if not isinstance(r, list):
                        r = [r]
                    msg = osc_message_builder.build_msg(r[0], r[1:])
                    b = struct.pack('!I', len(msg.dgram))
                    self.request.sendall(b + msg.dgram)

    def recvall(self, count):
        buf = b''
        while count > 0:
            newbuf = self.request.recv(count)
            if not newbuf:
                return None
            buf += newbuf
            count -= len(newbuf)
        return buf


class _TCPHandler1_1(socketserver.BaseRequestHandler):
    """Handles correct OSC1.1 messages.

    Whether this will be run on its own thread, the server's or a whole new
    process depends on the server you instantiated, look at their documentation.

    This method is called after a basic sanity check was done on the datagram,
    basically whether this datagram looks like an osc message or bundle,
    if not the server won't even bother to call it and so no new
    threads/processes will be spawned.
    """
    def handle(self):
        LOG.debug("handle OSC 1.1 protocol")
        while True:
            packets = self.recvall()
            if packets is None:
                break

            for p in packets:
                resp = _call_handlers_for_packet(p, self.server.dispatcher)
                for r in resp:
                    if not isinstance(r, list):
                        r = [r]
                    msg = osc_message_builder.build_msg(r[0], r[1:])
                    self.request.sendall(slip.encode(msg.dgram))

    def recvall(self):
        buf = self.request.recv(4096)
        if not buf:
            return None
        # If the last byte is not an END marker there could be more data coming
        while buf[-1] != 192:
            newbuf = self.request.recv(4096)
            if not newbuf:
                # Maybe should raise an exception here?
                break
            buf += newbuf

        packets = [slip.decode(p) for p in buf.split(slip.END_END)]
        return packets


class OSCTCPServer(socketserver.TCPServer):
    """Superclass for different flavors of OSCTCPServer"""

    def __init__(self, server_address, dispatcher, mode: str = MODE_1_1):
        self.request_queue_size = 300
        self.mode = mode
        if mode not in [MODE_1_0, MODE_1_1]:
            raise ValueError("OSC Mode must be '1.0' or '1.1'")
        if self.mode == MODE_1_0:
            super().__init__(server_address, _TCPHandler1_0)
        else:
            super().__init__(server_address, _TCPHandler1_1)
        self._dispatcher = dispatcher

    def verify_request(self, request, client_address):
        """Returns true if the data looks like a valid OSC TCP datagram."""
        # d = request.recv(9999).decode("utf-8")
        # print("d:type=%s d=%s" % (type(d), d))
        return True

    @property
    def dispatcher(self):
        """Dispatcher accessor for handlers to dispatch osc messages."""
        return self._dispatcher


class BlockingOSCTCPServer(OSCTCPServer):
    """Blocking version of the TCP server.

    Each message will be handled sequentially on the same thread.
    Use this is you don't care about latency in your message handling or don't
    have a multiprocess/multithread environment (really?).
    """


class ThreadingOSCTCPServer(socketserver.ThreadingMixIn, OSCTCPServer):
    """Threading version of the OSC TCP server.

    Each message will be handled in its own new thread.
    Use this when lightweight operations are done by each message handlers.
    """


if hasattr(os, "fork"):
    class ForkingOSCTCPServer(socketserver.ForkingMixIn, OSCTCPServer):
        """Forking version of the OSC TCP server.

        Each message will be handled in its own new process.
        Use this when heavyweight operations are done by each message handlers
        and forking a whole new process for each of them is worth it.
        """


class AsyncOSCTCPServer:
    """Asyncio version of the OSC TCP Server.
    Each TCP message is handled by _call_handlers_for_packet, the same method as in the
    OSCTCPServer family of blocking, threading, and forking servers
    """

    def __init__(self, server_address: str, port: int, dispatcher, mode: str = MODE_1_1):
        """
        :param server_address: tuple of (IP address to bind to, port)
        :param dispatcher: a pythonosc.dispatcher.Dispatcher
        """
        self._port = port
        self._server_address = server_address
        self._dispatcher = dispatcher
        self._server = None
        self._mode = mode

    # class _OSCProtocolFactory(asyncio.DatagramProtocol):
    #     """OSC protocol factory which passes datagrams to _call_handlers_for_packet"""
    #
    #     def __init__(self, dispatcher):
    #         self.dispatcher = dispatcher
    #
    #     def datagram_received(self, data, unused_addr):
    #         _call_handlers_for_packet(data, self.dispatcher)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self):
        """creates a socket endpoint and registers it with our event loop"""
        self._server = await asyncio.start_server(
            self.handle, self._server_address, self._port)

        addrs = ', '.join(str(sock.getsockname()) for sock in self._server.sockets)
        LOG.debug(f'Serving on {addrs}')

        async with self._server:
            await self._server.serve_forever()

    async def stop(self):
        await self._server.cancel()

    @property
    def dispatcher(self):
        return self._dispatcher

    async def handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        if self._mode == MODE_1_1:
            await self.handle_1_1(reader, writer)
        else:
            await self.handle1_0(reader, writer)
        writer.write_eof()
        LOG.debug("Close the connection")
        writer.close()
        await writer.wait_closed()

    async def handle1_0(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        LOG.debug("Incoming socket open 1.0")
        while True:
            try:
                buf = await reader.read(4)
            except Exception as e:
                LOG.exception("Read error", e)
                return
            if buf == b'':
                break
            length, = struct.unpack('!I', buf)
            buf = b''
            while length > 0:
                newbuf = await reader.read(length)
                if not newbuf:
                    break
                buf += newbuf
                length -= len(newbuf)

            result = await self._call_handlers_for_packet(buf)
            for r in result:
                if r is not None:
                    if not isinstance(r, list):
                        r = [r]
                    msg = osc_message_builder.build_msg(r[0], r[1:])
                    b = struct.pack('!I', len(msg.dgram))
                    writer.write(b + msg.dgram)
                    await writer.drain()

    async def handle_1_1(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        LOG.debug("Incoming socket open 1.1")
        while True:
            try:
                buf = await reader.read(4096)
            except Exception as e:
                LOG.exception("Read error", e)
                return
            if buf == b'':
                break
            while len(buf) > 0 and buf[-1] != 192:
                newbuf = await reader.read(4096)
                if not newbuf:
                    # Maybe should raise an exception here?
                    break
                buf += newbuf

            packets = [slip.decode(p) for p in buf.split(slip.END_END)]
            for p in packets:
                result = await self._call_handlers_for_packet(p)
                for r in result:
                    if r is not None:
                        if not isinstance(r, list):
                            r = [r]
                        msg = osc_message_builder.build_msg(r[0], r[1:])
                        writer.write(slip.encode(msg.dgram))
                        await writer.drain()

    async def _call_handlers_for_packet(self, data) -> list:
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
                handlers = self._dispatcher.handlers_for_address(
                    timed_msg.message.address)
                if not handlers:
                    continue
                # If the message is to be handled later, then so be it.
                if timed_msg.time > now:
                    time.sleep(timed_msg.time - now)
                for handler in handlers:
                    if inspect.iscoroutinefunction(handler.callback):
                        if handler.args:
                            result = await handler.callback(
                                timed_msg.message.address, handler.args, *timed_msg.message)
                        else:
                            result = await handler.callback(timed_msg.message.address,
                                                            *timed_msg.message)
                    else:
                        if handler.args:
                            result = handler.callback(
                                timed_msg.message.address, handler.args, *timed_msg.message)
                        else:
                            result = handler.callback(timed_msg.message.address, *timed_msg.message)
                    results.append(result)
        except osc_packet.ParseError as e:
            LOG.debug(f"Packet parse error: {str(e)}")
        return results
