import unittest

import osc_message_builder


class TestOscMessageBuilder(unittest.TestCase):
  
  def test_just_address(self):
    msg = osc_message_builder.OscMessageBuilder("/a/b/c").build()
    self.assertEqual("/a/b/c", msg.address)
    self.assertEqual([], msg.params)

  def test_no_address_raises(self):
    msg = osc_message_builder.OscMessageBuilder("")
    self.assertRaises(osc_message_builder.BuildError, msg.build)

  def test_wrong_param_raise(self):
    msg = osc_message_builder.OscMessageBuilder("")
    self.assertRaises(ValueError, msg.add_arg, "what?", 1)

  def test_all_param_types(self):
    msg = osc_message_builder.OscMessageBuilder(address = "/SYNC")
    msg.add_arg(msg.ARG_TYPE_FLOAT, 4.0)
    msg.add_arg(msg.ARG_TYPE_INT, 2)
    msg.add_arg(msg.ARG_TYPE_STRING, "value")
    msg.add_arg(msg.ARG_TYPE_BLOB, b"\x01\x02\x03")
    msg = msg.build()
    self.assertEqual("/SYNC", msg.address)
    self.assertSequenceEqual([4.0, 2, "value", b"\x01\x02\x03"], msg.params)


if __name__ == "__main__":
  unittest.main()
