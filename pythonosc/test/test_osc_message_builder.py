import unittest

from pythonosc import osc_message_builder


class TestOscMessageBuilder(unittest.TestCase):

  def test_just_address(self):
    msg = osc_message_builder.OscMessageBuilder("/a/b/c").build()
    self.assertEqual("/a/b/c", msg.address)
    self.assertEqual([], msg.params)

  def test_no_address_raises(self):
    builder = osc_message_builder.OscMessageBuilder("")
    self.assertRaises(osc_message_builder.BuildError, builder.build)

  def test_wrong_param_raise(self):
    builder = osc_message_builder.OscMessageBuilder("")
    self.assertRaises(ValueError, builder.add_arg, "what?", 1)

  def test_all_param_types(self):
    builder = osc_message_builder.OscMessageBuilder(address="/SYNC")
    builder.add_arg(4.0)
    builder.add_arg(2)
    builder.add_arg("value")
    builder.add_arg(True)
    builder.add_arg(False)
    builder.add_arg(b"\x01\x02\x03")
    # The same args but with explicit types.
    builder.add_arg(4.0, builder.ARG_TYPE_FLOAT)
    builder.add_arg(2, builder.ARG_TYPE_INT)
    builder.add_arg("value", builder.ARG_TYPE_STRING)
    builder.add_arg(True)
    builder.add_arg(False)
    builder.add_arg(b"\x01\x02\x03", builder.ARG_TYPE_BLOB)
    self.assertEqual(12, len(builder.args))
    self.assertEqual("/SYNC", builder.address)
    builder.address = '/SEEK'
    msg = builder.build()
    self.assertEqual("/SEEK", msg.address)
    self.assertSequenceEqual(
        [4.0, 2, "value", True, False, b"\x01\x02\x03"] * 2, msg.params)

  def test_build_wrong_type_raises(self):
    builder = osc_message_builder.OscMessageBuilder(address="/SYNC")
    builder.add_arg('this is not a float', builder.ARG_TYPE_FLOAT)
    self.assertRaises(osc_message_builder.BuildError, builder.build)


if __name__ == "__main__":
  unittest.main()
