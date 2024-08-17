import struct
import unittest
import unittest.mock as mock

from pythonosc import dispatcher, osc_tcp_server
from pythonosc.slip import END

_SIMPLE_PARAM_INT_MSG = b"/SYNC\x00\x00\x00" b",i\x00\x00" b"\x00\x00\x00\x04"

LEN_SIMPLE_PARAM_INT_MSG = struct.pack("!I", len(_SIMPLE_PARAM_INT_MSG))
_SIMPLE_PARAM_INT_MSG_1_1 = END + _SIMPLE_PARAM_INT_MSG + END

# Regression test for a datagram that should NOT be stripped, ever...
_SIMPLE_PARAM_INT_9 = b"/debug\x00\x00,i\x00\x00\x00\x00\x00\t"
LEN_SIMPLE_PARAM_INT_9 = struct.pack("!I", len(_SIMPLE_PARAM_INT_9))

_SIMPLE_PARAM_INT_9_1_1 = END + _SIMPLE_PARAM_INT_9 + END

_SIMPLE_MSG_NO_PARAMS = b"/SYNC\x00\x00\x00"
LEN_SIMPLE_MSG_NO_PARAMS = struct.pack("!I", len(_SIMPLE_MSG_NO_PARAMS))
_SIMPLE_MSG_NO_PARAMS_1_1 = END + _SIMPLE_MSG_NO_PARAMS + END


class TestTCP_1_1_Handler(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.dispatcher = dispatcher.Dispatcher()
        # We do not want to create real UDP connections during unit tests.
        self.server = unittest.mock.Mock(spec=osc_tcp_server.BlockingOSCTCPServer)
        # Need to attach property mocks to types, not objects... weird.
        type(self.server).dispatcher = unittest.mock.PropertyMock(
            return_value=self.dispatcher
        )
        self.client_address = ("127.0.0.1", 8080)
        self.mock_meth = unittest.mock.MagicMock()
        self.mock_meth.return_value = None

    def test_no_match(self):
        self.dispatcher.map("/foobar", self.mock_meth)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [
            _SIMPLE_MSG_NO_PARAMS_1_1,
            _SIMPLE_PARAM_INT_MSG_1_1,
            b"",
        ]
        osc_tcp_server._TCPHandler1_1(mock_sock, self.client_address, self.server)
        self.assertFalse(self.mock_meth.called)

    def test_match_with_args(self):
        self.dispatcher.map("/SYNC", self.mock_meth, 1, 2, 3)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [_SIMPLE_PARAM_INT_MSG_1_1, b""]
        osc_tcp_server._TCPHandler1_1(mock_sock, self.client_address, self.server)
        self.mock_meth.assert_called_with("/SYNC", [1, 2, 3], 4)

    def test_match_int9(self):
        self.dispatcher.map("/debug", self.mock_meth)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [_SIMPLE_PARAM_INT_9_1_1, b""]
        osc_tcp_server._TCPHandler1_1(mock_sock, self.client_address, self.server)
        self.assertTrue(self.mock_meth.called)
        self.mock_meth.assert_called_with("/debug", 9)

    def test_match_without_args(self):
        self.dispatcher.map("/SYNC", self.mock_meth)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [_SIMPLE_MSG_NO_PARAMS_1_1, b""]
        osc_tcp_server._TCPHandler1_1(mock_sock, self.client_address, self.server)
        self.mock_meth.assert_called_with("/SYNC")

    def test_match_default_handler(self):
        self.dispatcher.set_default_handler(self.mock_meth)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [_SIMPLE_MSG_NO_PARAMS_1_1, b""]
        osc_tcp_server._TCPHandler1_1(mock_sock, self.client_address, self.server)
        self.mock_meth.assert_called_with("/SYNC")

    def test_response_no_args(self):
        def respond(*args, **kwargs):
            return "/SYNC"

        self.dispatcher.map("/SYNC", respond)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [_SIMPLE_MSG_NO_PARAMS_1_1, b""]
        mock_sock.sendall = mock.Mock()
        mock_sock.sendall.return_value = None
        osc_tcp_server._TCPHandler1_1(mock_sock, self.client_address, self.server)
        mock_sock.sendall.assert_called_with(b"\xc0/SYNC\00\00\00,\00\00\00\xc0")

    def test_response_with_args(self):
        def respond(*args, **kwargs):
            return [
                "/SYNC",
                1,
                "2",
                3.0,
            ]

        self.dispatcher.map("/SYNC", respond)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [_SIMPLE_MSG_NO_PARAMS_1_1, b""]
        mock_sock.sendall = mock.Mock()
        mock_sock.sendall.return_value = None
        osc_tcp_server._TCPHandler1_1(mock_sock, self.client_address, self.server)
        mock_sock.sendall.assert_called_with(
            b"\xc0/SYNC\00\00\00,isf\x00\x00\x00\x00\x00\x00\x00\x012\x00\x00\x00@@\x00\x00\xc0"
        )


class TestTCP_1_0_Handler(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.dispatcher = dispatcher.Dispatcher()
        # We do not want to create real UDP connections during unit tests.
        self.server = unittest.mock.Mock(spec=osc_tcp_server.BlockingOSCTCPServer)
        # Need to attach property mocks to types, not objects... weird.
        type(self.server).dispatcher = unittest.mock.PropertyMock(
            return_value=self.dispatcher
        )
        self.client_address = ("127.0.0.1", 8080)
        self.mock_meth = unittest.mock.MagicMock()
        self.mock_meth.return_value = None

    def test_no_match(self):
        self.dispatcher.map("/foobar", self.mock_meth)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [
            LEN_SIMPLE_MSG_NO_PARAMS,
            _SIMPLE_MSG_NO_PARAMS,
            LEN_SIMPLE_PARAM_INT_MSG,
            _SIMPLE_PARAM_INT_MSG,
            b"",
        ]
        osc_tcp_server._TCPHandler1_0(mock_sock, self.client_address, self.server)
        self.assertFalse(self.mock_meth.called)

    def test_match_with_args(self):
        self.dispatcher.map("/SYNC", self.mock_meth, 1, 2, 3)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [
            LEN_SIMPLE_PARAM_INT_MSG,
            _SIMPLE_PARAM_INT_MSG,
            b"",
        ]
        osc_tcp_server._TCPHandler1_0(mock_sock, self.client_address, self.server)
        self.mock_meth.assert_called_with("/SYNC", [1, 2, 3], 4)

    def test_match_int9(self):
        self.dispatcher.map("/debug", self.mock_meth)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [LEN_SIMPLE_PARAM_INT_9, _SIMPLE_PARAM_INT_9, b""]
        osc_tcp_server._TCPHandler1_0(mock_sock, self.client_address, self.server)
        self.assertTrue(self.mock_meth.called)
        self.mock_meth.assert_called_with("/debug", 9)

    def test_match_without_args(self):
        self.dispatcher.map("/SYNC", self.mock_meth)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [
            LEN_SIMPLE_MSG_NO_PARAMS,
            _SIMPLE_MSG_NO_PARAMS,
            b"",
        ]
        osc_tcp_server._TCPHandler1_0(mock_sock, self.client_address, self.server)
        self.mock_meth.assert_called_with("/SYNC")

    def test_match_default_handler(self):
        self.dispatcher.set_default_handler(self.mock_meth)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [
            LEN_SIMPLE_MSG_NO_PARAMS,
            _SIMPLE_MSG_NO_PARAMS,
            b"",
        ]
        osc_tcp_server._TCPHandler1_0(mock_sock, self.client_address, self.server)
        self.mock_meth.assert_called_with("/SYNC")

    def test_response_no_args(self):
        def respond(*args, **kwargs):
            return "/SYNC"

        self.dispatcher.map("/SYNC", respond)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [
            LEN_SIMPLE_MSG_NO_PARAMS,
            _SIMPLE_MSG_NO_PARAMS,
            b"",
        ]
        mock_sock.sendall = mock.Mock()
        mock_sock.sendall.return_value = None
        osc_tcp_server._TCPHandler1_0(mock_sock, self.client_address, self.server)
        mock_sock.sendall.assert_called_with(
            b"\x00\x00\x00\x0c/SYNC\00\00\00,\00\00\00"
        )

    def test_response_with_args(self):
        def respond(*args, **kwargs):
            return [
                "/SYNC",
                1,
                "2",
                3.0,
            ]

        self.dispatcher.map("/SYNC", respond)
        mock_sock = mock.Mock()
        mock_sock.recv = mock.Mock()
        mock_sock.recv.side_effect = [
            LEN_SIMPLE_MSG_NO_PARAMS,
            _SIMPLE_MSG_NO_PARAMS,
            b"",
        ]
        mock_sock.sendall = mock.Mock()
        mock_sock.sendall.return_value = None
        osc_tcp_server._TCPHandler1_0(mock_sock, self.client_address, self.server)
        mock_sock.sendall.assert_called_with(
            b"\x00\x00\x00\x1c/SYNC\00\00\00,isf\x00\x00\x00\x00\x00\x00\x00\x012\x00\x00\x00@@\x00\x00"
        )


class TestAsync1_1Handler(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        super().setUp()
        self.dispatcher = dispatcher.Dispatcher()
        # We do not want to create real UDP connections during unit tests.
        self.server = unittest.mock.Mock(spec=osc_tcp_server.BlockingOSCTCPServer)
        # Need to attach property mocks to types, not objects... weird.
        type(self.server).dispatcher = unittest.mock.PropertyMock(
            return_value=self.dispatcher
        )
        self.client_address = ("127.0.0.1", 8080)
        self.mock_writer = mock.Mock()
        self.mock_writer.close = mock.Mock()
        self.mock_writer.write = mock.Mock()
        self.mock_writer.write_eof = mock.Mock()
        self.mock_writer.drain = mock.AsyncMock()
        self.mock_writer.wait_closed = mock.AsyncMock()
        self.mock_reader = mock.Mock()
        self.mock_reader.read = mock.AsyncMock()
        self.server = osc_tcp_server.AsyncOSCTCPServer(
            "127.0.0.1", 8008, self.dispatcher
        )
        self.mock_meth = unittest.mock.MagicMock()
        self.mock_meth.return_value = None

    async def test_no_match(self):
        self.dispatcher.map("/foobar", self.mock_meth)
        self.mock_reader.read.side_effect = [
            _SIMPLE_MSG_NO_PARAMS_1_1,
            _SIMPLE_PARAM_INT_MSG_1_1,
            b"",
        ]
        await osc_tcp_server.AsyncOSCTCPServer.handle(
            self.server, self.mock_reader, self.mock_writer
        )
        self.assertFalse(self.mock_meth.called)

    async def test_match_with_args(self):
        self.dispatcher.map("/SYNC", self.mock_meth, 1, 2, 3)
        self.mock_reader.read.side_effect = [_SIMPLE_PARAM_INT_MSG_1_1, b""]
        await osc_tcp_server.AsyncOSCTCPServer.handle(
            self.server, self.mock_reader, self.mock_writer
        )
        self.mock_meth.assert_called_with("/SYNC", [1, 2, 3], 4)

    async def test_match_int9(self):
        self.dispatcher.map("/debug", self.mock_meth)
        self.mock_reader.read.side_effect = [_SIMPLE_PARAM_INT_9_1_1, b""]
        await osc_tcp_server.AsyncOSCTCPServer.handle(
            self.server, self.mock_reader, self.mock_writer
        )
        self.assertTrue(self.mock_meth.called)
        self.mock_meth.assert_called_with("/debug", 9)

    async def test_match_without_args(self):
        self.dispatcher.map("/SYNC", self.mock_meth)
        self.mock_reader.read.side_effect = [_SIMPLE_MSG_NO_PARAMS_1_1, b""]
        await osc_tcp_server.AsyncOSCTCPServer.handle(
            self.server, self.mock_reader, self.mock_writer
        )
        self.mock_meth.assert_called_with("/SYNC")

    async def test_match_default_handler(self):
        self.dispatcher.set_default_handler(self.mock_meth)
        self.mock_reader.read.side_effect = [_SIMPLE_MSG_NO_PARAMS_1_1, b""]
        await osc_tcp_server.AsyncOSCTCPServer.handle(
            self.server, self.mock_reader, self.mock_writer
        )
        self.mock_meth.assert_called_with("/SYNC")

    async def test_response_no_args(self):
        def respond(*args, **kwargs):
            return "/SYNC"

        self.dispatcher.map("/SYNC", respond)
        self.mock_reader.read.side_effect = [_SIMPLE_MSG_NO_PARAMS_1_1, b""]
        await osc_tcp_server.AsyncOSCTCPServer.handle(
            self.server, self.mock_reader, self.mock_writer
        )
        self.mock_writer.write.assert_called_with(b"\xc0/SYNC\00\00\00,\00\00\00\xc0")

    async def test_response_with_args(self):
        def respond(*args, **kwargs):
            return [
                "/SYNC",
                1,
                "2",
                3.0,
            ]

        self.dispatcher.map("/SYNC", respond)
        self.mock_reader.read.side_effect = [_SIMPLE_MSG_NO_PARAMS_1_1, b""]
        await osc_tcp_server.AsyncOSCTCPServer.handle(
            self.server, self.mock_reader, self.mock_writer
        )
        self.mock_writer.write.assert_called_with(
            b"\xc0/SYNC\00\00\00,isf\x00\x00\x00\x00\x00\x00\x00\x012\x00\x00\x00@@\x00\x00\xc0"
        )

    async def test_async_response_with_args(self):
        async def respond(*args, **kwargs):
            return [
                "/SYNC",
                1,
                "2",
                3.0,
            ]

        self.dispatcher.map("/SYNC", respond)
        self.mock_reader.read.side_effect = [_SIMPLE_MSG_NO_PARAMS_1_1, b""]
        await osc_tcp_server.AsyncOSCTCPServer.handle(
            self.server, self.mock_reader, self.mock_writer
        )
        self.mock_writer.write.assert_called_with(
            b"\xc0/SYNC\00\00\00,isf\x00\x00\x00\x00\x00\x00\x00\x012\x00\x00\x00@@\x00\x00\xc0"
        )


if __name__ == "__main__":
    unittest.main()
