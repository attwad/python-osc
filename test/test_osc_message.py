import unittest

import osc_message


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
    self.assertAlmostEqual(0.0, msg.param(0))

  def test_switch_goes_on(self):
    msg = osc_message.OscMessage(_DGRAM_SWITCH_GOES_ON)
    self.assertEqual(b"/SYNC\x00\x00\x00", msg.address)
    self.assertEqual(1, msg.param_count)
    self.assertAlmostEqual(0.5, msg.param(0))


if __name__ == "__main__":
  unittest.main()
