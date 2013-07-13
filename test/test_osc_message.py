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


if __name__ == "__main__":
  unittest.main()
