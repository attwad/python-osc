import unittest

from pythonosc import osc_message
from pythonosc import osc_bundle
from pythonosc.parsing import osc_types

_DGRAM_KNOB_ROTATES_BUNDLE = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x14"
    b"/LFO_Rate\x00\x00\x00"
    b",f\x00\x00"
    b">\x8c\xcc\xcd")

_DGRAM_SWITCH_GOES_OFF = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x10"
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"\x00\x00\x00\x00")

_DGRAM_SWITCH_GOES_ON = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x10"
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00")

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

_DGRAM_BUNDLE_IN_BUNDLE = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00("  # length of sub bundle: 40 bytes.
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x10"
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00")

_DGRAM_INVALID = (
    b"#bundle\x00"
    b"\x00\x00\x00")

_DGRAM_INVALID_INDEX = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x20"
    b"/SYNC\x00\x00\x00\x00")

_DGRAM_UNKNOWN_TYPE = (
    b"#bundle\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x10"
    b"iamnotaslash")


class TestOscBundle(unittest.TestCase):

  def test_switch_goes_off(self):
    bundle = osc_bundle.OscBundle(_DGRAM_SWITCH_GOES_OFF)
    self.assertEqual(1, bundle.num_contents)
    self.assertEqual(len(_DGRAM_SWITCH_GOES_OFF), bundle.size)
    self.assertEqual(osc_types.IMMEDIATELY, bundle.timestamp)

  def test_switch_goes_on(self):
    bundle = osc_bundle.OscBundle(_DGRAM_SWITCH_GOES_ON)
    self.assertEqual(1, bundle.num_contents)
    self.assertEqual(len(_DGRAM_SWITCH_GOES_ON), bundle.size)
    self.assertEqual(osc_types.IMMEDIATELY, bundle.timestamp)

  def test_datagram_length(self):
    bundle = osc_bundle.OscBundle(_DGRAM_KNOB_ROTATES_BUNDLE)
    self.assertEqual(1, bundle.num_contents)
    self.assertEqual(len(_DGRAM_KNOB_ROTATES_BUNDLE), bundle.size)
    self.assertEqual(osc_types.IMMEDIATELY, bundle.timestamp)

  def test_two_messages_in_bundle(self):
    bundle = osc_bundle.OscBundle(_DGRAM_TWO_MESSAGES_IN_BUNDLE)
    self.assertEqual(2, bundle.num_contents)
    self.assertEqual(osc_types.IMMEDIATELY, bundle.timestamp)
    for content in bundle:
      self.assertEqual(osc_message.OscMessage, type(content))

  def test_empty_bundle(self):
    bundle = osc_bundle.OscBundle(_DGRAM_EMPTY_BUNDLE)
    self.assertEqual(0, bundle.num_contents)
    self.assertEqual(osc_types.IMMEDIATELY, bundle.timestamp)

  def test_bundle_in_bundle_we_must_go_deeper(self):
    bundle = osc_bundle.OscBundle(_DGRAM_BUNDLE_IN_BUNDLE)
    self.assertEqual(1, bundle.num_contents)
    self.assertEqual(osc_types.IMMEDIATELY, bundle.timestamp)
    self.assertEqual(osc_bundle.OscBundle, type(bundle.content(0)))

  def test_dgram_is_bundle(self):
    self.assertTrue(osc_bundle.OscBundle.dgram_is_bundle(
        _DGRAM_SWITCH_GOES_ON))
    self.assertFalse(osc_bundle.OscBundle.dgram_is_bundle(b'junk'))

  def test_raises_on_invalid_datagram(self):
    self.assertRaises(
        osc_bundle.ParseError, osc_bundle.OscBundle, _DGRAM_INVALID)
    self.assertRaises(
        osc_bundle.ParseError, osc_bundle.OscBundle, _DGRAM_INVALID_INDEX)

  def test_unknown_type(self):
    bundle = osc_bundle.OscBundle(_DGRAM_UNKNOWN_TYPE)

if __name__ == "__main__":
  unittest.main()
