import unittest

import osc_bundle

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


class TestOscBundle(unittest.TestCase):

  def test_switch_goes_off(self):
    bundle = osc_bundle.OscBundle(_DGRAM_SWITCH_GOES_OFF)
    self.assertEqual(1, bundle.num_contents)

  def test_switch_goes_on(self):
    bundle = osc_bundle.OscBundle(_DGRAM_SWITCH_GOES_ON)
    self.assertEqual(1, bundle.num_contents)

  def test_datagram_length(self):
    bundle = osc_bundle.OscBundle(_DGRAM_KNOB_ROTATES_BUNDLE)
    self.assertEqual(len(_DGRAM_KNOB_ROTATES_BUNDLE), bundle.size)



if __name__ == "__main__":
  unittest.main()
