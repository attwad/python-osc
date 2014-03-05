import unittest

from pythonosc import osc_message


# Datagrams sent by Reaktor 5.8 by Native Instruments (c).
_DGRAM_KNOB_ROTATES = (
    b"/FB\x00"
    b",f\x00\x00"
    b">xca=q")

_DGRAM_SWITCH_GOES_OFF = (
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"\x00\x00\x00\x00")

_DGRAM_SWITCH_GOES_ON = (
    b"/SYNC\x00\x00\x00"
    b",f\x00\x00"
    b"?\x00\x00\x00")

_DGRAM_NO_PARAMS = b"/SYNC\x00\x00\x00"

_DGRAM_ALL_STANDARD_TYPES_OF_PARAMS = (
    b"/SYNC\x00\x00\x00"
    b",ifsb\x00\x00\x00"
    b"\x00\x00\x00\x03"  # 3
    b"@\x00\x00\x00"  # 2.0
    b"ABC\x00"  # "ABC"
    b"\x00\x00\x00\x08stuff\x00\x00\x00")  # b"stuff\x00\x00\x00"

_DGRAM_ALL_NON_STANDARD_TYPES_OF_PARAMS = (
    b"/SYNC\x00\x00\x00"
    b",T" # True
    b"F\x00") # False 

_DGRAM_UNKNOWN_PARAM_TYPE = (
    b"/SYNC\x00\x00\x00"
    b",fx\x00"  # x is an unknown param type.
    b"?\x00\x00\x00")


class TestOscMessage(unittest.TestCase):

  def test_switch_goes_off(self):
    msg = osc_message.OscMessage(_DGRAM_SWITCH_GOES_OFF)
    self.assertEqual("/SYNC", msg.address)
    self.assertEqual(1, len(msg.params))
    self.assertTrue(type(msg.params[0]) == float)
    self.assertAlmostEqual(0.0, msg.params[0])

  def test_switch_goes_on(self):
    msg = osc_message.OscMessage(_DGRAM_SWITCH_GOES_ON)
    self.assertEqual("/SYNC", msg.address)
    self.assertEqual(1, len(msg.params))
    self.assertTrue(type(msg.params[0]) == float)
    self.assertAlmostEqual(0.5, msg.params[0])

  def test_knob_rotates(self):
    msg = osc_message.OscMessage(_DGRAM_KNOB_ROTATES)
    self.assertEqual("/FB", msg.address)
    self.assertEqual(1, len(msg.params))
    self.assertTrue(type(msg.params[0]) == float)

  def test_no_params(self):
    msg = osc_message.OscMessage(_DGRAM_NO_PARAMS)
    self.assertEqual("/SYNC", msg.address)
    self.assertEqual(0, len(msg.params))

  def test_all_standard_types_off_params(self):
    msg = osc_message.OscMessage(_DGRAM_ALL_STANDARD_TYPES_OF_PARAMS)
    self.assertEqual("/SYNC", msg.address)
    self.assertEqual(4, len(msg.params))
    self.assertEqual(3, msg.params[0])
    self.assertAlmostEqual(2.0, msg.params[1])
    self.assertEqual("ABC", msg.params[2])
    self.assertEqual(b"stuff\x00\x00\x00", msg.params[3])
    self.assertEqual(4, len(list(msg)))

  def test_all_non_standard_params(self):
    msg = osc_message.OscMessage(_DGRAM_ALL_NON_STANDARD_TYPES_OF_PARAMS)
    self.assertEqual("/SYNC", msg.address)
    self.assertEqual(2, len(msg.params))
    self.assertEqual(True, msg.params[0])
    self.assertEqual(False, msg.params[1])
    self.assertEqual(2, len(list(msg)))

  def test_raises_on_empty_datargram(self):
    self.assertRaises(osc_message.ParseError, osc_message.OscMessage, b'')

  def test_ignores_unknown_param(self):
    msg = osc_message.OscMessage(_DGRAM_UNKNOWN_PARAM_TYPE)
    self.assertEqual("/SYNC", msg.address)
    self.assertEqual(1, len(msg.params))
    self.assertTrue(type(msg.params[0]) == float)
    self.assertAlmostEqual(0.5, msg.params[0])

  def test_raises_on_incorrect_datargram(self):
    self.assertRaises(
        osc_message.ParseError, osc_message.OscMessage, b'foobar')

if __name__ == "__main__":
  unittest.main()
