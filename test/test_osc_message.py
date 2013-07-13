import unittest
import logging

import osc_message


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


class TestOscMessage(unittest.TestCase):

  def test_switch_goes_off(self):
    msg = osc_message.OscMessage(_DGRAM_SWITCH_GOES_OFF)
    self.assertEqual(b"/SYNC\x00\x00\x00", msg.address)
    self.assertEqual(1, msg.param_count)
    self.assertTrue(type(msg.param(0)) == float)
    self.assertAlmostEqual(0.0, msg.param(0))

  def test_switch_goes_on(self):
    msg = osc_message.OscMessage(_DGRAM_SWITCH_GOES_ON)
    self.assertEqual(b"/SYNC\x00\x00\x00", msg.address)
    self.assertEqual(1, msg.param_count)
    self.assertTrue(type(msg.param(0)) == float)
    self.assertAlmostEqual(0.5, msg.param(0))

  def test_knob_rotates(self):
    msg = osc_message.OscMessage(_DGRAM_KNOB_ROTATES)
    self.assertEqual(b"/FB\x00", msg.address)
    self.assertEqual(1, msg.param_count)
    self.assertTrue(type(msg.param(0)) == float)

  def test_no_params(self):
    msg = osc_message.OscMessage(_DGRAM_NO_PARAMS)
    self.assertEqual(b"/SYNC\x00\x00\x00", msg.address)
    self.assertEqual(0, msg.param_count)

  def test_all_standard_types_off_params(self):
    msg = osc_message.OscMessage(_DGRAM_ALL_STANDARD_TYPES_OF_PARAMS)
    self.assertEqual(b"/SYNC\x00\x00\x00", msg.address)
    self.assertEqual(4, msg.param_count)
    self.assertEqual(3, msg.param(0))
    self.assertAlmostEqual(2.0, msg.param(1))
    self.assertEqual(b"ABC\x00", msg.param(2))
    self.assertEqual(b"stuff\x00\x00\x00", msg.param(3))

if __name__ == "__main__":
  unittest.main()
