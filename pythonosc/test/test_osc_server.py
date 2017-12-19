import unittest
import unittest.mock

from pythonosc import dispatcher
from pythonosc import osc_server


_SIMPLE_PARAM_INT_MSG = (
    b"/SYNC\x00\x00\x00"
    b",i\x00\x00"
    b"\x00\x00\x00\x04")

# Regression test for a datagram that should NOT be stripped, ever...
_SIMPLE_PARAM_INT_9 = b'/debug\x00\x00,i\x00\x00\x00\x00\x00\t'

_SIMPLE_MSG_NO_PARAMS = b"/SYNC\x00\x00\x00"


class TestOscServer(unittest.TestCase):

  def test_is_valid_request(self):
    self.assertTrue(
        osc_server._is_valid_request([b'#bundle\x00foobar']))
    self.assertTrue(
        osc_server._is_valid_request([b'/address/1/2/3,foobar']))
    self.assertFalse(
        osc_server._is_valid_request([b'']))


class TestUDPHandler(unittest.TestCase):

  def setUp(self):
    super().setUp()
    self.dispatcher = dispatcher.Dispatcher()
    # We do not want to create real UDP connections during unit tests.
    self.server = unittest.mock.Mock(spec=osc_server.BlockingOSCUDPServer)
    # Need to attach property mocks to types, not objects... weird.
    type(self.server).dispatcher = unittest.mock.PropertyMock(
        return_value=self.dispatcher)
    self.client_address = ("127.0.0.1", 8080)

  def test_no_match(self):
    mock_meth = unittest.mock.MagicMock()
    self.dispatcher.map("/foobar", mock_meth)
    osc_server._UDPHandler(
        [_SIMPLE_PARAM_INT_MSG, None], self.client_address, self.server)
    self.assertFalse(mock_meth.called)

  def test_match_with_args(self):
    mock_meth = unittest.mock.MagicMock()
    self.dispatcher.map("/SYNC", mock_meth, 1, 2, 3)
    osc_server._UDPHandler(
        [_SIMPLE_PARAM_INT_MSG, None], self.client_address, self.server)
    mock_meth.assert_called_with("/SYNC", [1, 2, 3], 4)

  def test_match_int9(self):
    mock_meth = unittest.mock.MagicMock()
    self.dispatcher.map("/debug", mock_meth)
    osc_server._UDPHandler(
        [_SIMPLE_PARAM_INT_9, None], self.client_address, self.server)
    self.assertTrue(mock_meth.called)
    mock_meth.assert_called_with("/debug", 9)

  def test_match_without_args(self):
    mock_meth = unittest.mock.MagicMock()
    self.dispatcher.map("/SYNC", mock_meth)
    osc_server._UDPHandler(
        [_SIMPLE_MSG_NO_PARAMS, None], self.client_address, self.server)
    mock_meth.assert_called_with("/SYNC")

  def test_match_default_handler(self):
    mock_meth = unittest.mock.MagicMock()
    self.dispatcher.set_default_handler(mock_meth)
    osc_server._UDPHandler(
        [_SIMPLE_MSG_NO_PARAMS, None], self.client_address, self.server)
    mock_meth.assert_called_with("/SYNC")


if __name__ == "__main__":
  unittest.main()
