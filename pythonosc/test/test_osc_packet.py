import unittest

from pythonosc import osc_packet

_DGRAM_TWO_MESSAGES_IN_BUNDLE = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    # First message.
    b"\x00\x00\x00\x10"
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00"
    # Second message, same.
    b"\x00\x00\x00\x10"
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00")

_DGRAM_EMPTY_BUNDLE = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01")

_DGRAM_NESTED_MESS = (
    b"#bundle\x00"
    b"\x10\x00\x00\x00\x00\x00\x00\x00"
    # First message.
    b"\x00\x00\x00\x10"  # 16 bytes
    b"/1111\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00"
    # Second message, same.
    b"\x00\x00\x00\x10"  # 16 bytes
    b"/2222\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00"
    # Now another bundle within it, oh my...
    b"\x00\x00\x00$"  # 36 bytes.
    b"#bundle\x00"
    b"\x20\x00\x00\x00\x00\x00\x00\x00"
    # First message.
    b"\x00\x00\x00\x10"
    b"/3333\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00"
    # And another final bundle.
    b"\x00\x00\x00$"  # 36 bytes.
    b"#bundle\x00"
    b"\x15\x00\x00\x00\x00\x00\x00\x01"  # Immediately this one.
    # First message.
    b"\x00\x00\x00\x10"
    b"/4444\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00")


class TestOscPacket(unittest.TestCase):
    def test_two_messages_in_a_bundle(self):
        packet = osc_packet.OscPacket(_DGRAM_TWO_MESSAGES_IN_BUNDLE)
        self.assertEqual(2, len(packet.messages))

    def test_empty_dgram_raises_exception(self):
        self.assertRaises(osc_packet.ParseError, osc_packet.OscPacket, b'')

    def test_empty_bundle(self):
        packet = osc_packet.OscPacket(_DGRAM_EMPTY_BUNDLE)
        self.assertEqual(0, len(packet.messages))

    def test_nested_mess_bundle(self):
        packet = osc_packet.OscPacket(_DGRAM_NESTED_MESS)
        self.assertEqual(4, len(packet.messages))
        self.assertTrue(packet.messages[0][0], packet.messages[1][0])
        self.assertTrue(packet.messages[1][0], packet.messages[2][0])
        self.assertTrue(packet.messages[2][0], packet.messages[3][0])


if __name__ == "__main__":
    unittest.main()
