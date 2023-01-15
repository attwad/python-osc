import unittest

from pythonosc import osc_message_builder


class TestOscMessageBuilder(unittest.TestCase):
    def test_just_address(self):
        msg = osc_message_builder.OscMessageBuilder("/a/b/c").build()
        self.assertEqual("/a/b/c", msg.address)
        self.assertEqual([], msg.params)
        # Messages with just an address should still contain the ",".
        self.assertEqual(b'/a/b/c\x00\x00,\x00\x00\x00', msg.dgram)

    def test_no_address_raises(self):
        builder = osc_message_builder.OscMessageBuilder("")
        self.assertRaises(osc_message_builder.BuildError, builder.build)

    def test_wrong_param_raise(self):
        builder = osc_message_builder.OscMessageBuilder("")
        self.assertRaises(ValueError, builder.add_arg, "what?", 1)

    def test_add_arg_invalid_infered_type(self):
        builder = osc_message_builder.OscMessageBuilder('')
        self.assertRaises(ValueError, builder.add_arg, {'name': 'John'})

    def test_all_param_types(self):
        builder = osc_message_builder.OscMessageBuilder(address="/SYNC")
        builder.add_arg(4.0)
        builder.add_arg(2)
        builder.add_arg(1099511627776)
        builder.add_arg("value")
        builder.add_arg(True)
        builder.add_arg(False)
        builder.add_arg(b"\x01\x02\x03")
        builder.add_arg([1, ["abc"]])
        builder.add_arg(None)
        # The same args but with explicit types.
        builder.add_arg(4.0, builder.ARG_TYPE_FLOAT)
        builder.add_arg(2, builder.ARG_TYPE_INT)
        builder.add_arg(1099511627776, builder.ARG_TYPE_INT64)
        builder.add_arg("value", builder.ARG_TYPE_STRING)
        builder.add_arg(True)
        builder.add_arg(False)
        builder.add_arg(b"\x01\x02\x03", builder.ARG_TYPE_BLOB)
        builder.add_arg([1, ["abc"]], [builder.ARG_TYPE_INT, [builder.ARG_TYPE_STRING]])
        builder.add_arg(None, builder.ARG_TYPE_NIL)
        builder.add_arg(4278255360, builder.ARG_TYPE_RGBA)
        builder.add_arg((1, 145, 36, 125), builder.ARG_TYPE_MIDI)
        builder.add_arg(1e-9, builder.ARG_TYPE_DOUBLE)
        self.assertEqual(len("fihsTFb[i[s]]N") * 2 + 3, len(builder.args))
        self.assertEqual("/SYNC", builder.address)
        builder.address = '/SEEK'
        msg = builder.build()
        self.assertEqual("/SEEK", msg.address)
        self.assertSequenceEqual(
            [4.0, 2, 1099511627776, "value", True, False, b"\x01\x02\x03", [1, ["abc"]], None] * 2 +
            [4278255360, (1, 145, 36, 125), 1e-9],
            msg.params)

    def test_long_list(self):
        huge_list = list(range(512))
        builder = osc_message_builder.OscMessageBuilder(address="/SYNC")
        builder.add_arg(huge_list)
        msg = builder.build()
        print(msg._dgram)
        self.assertSequenceEqual([huge_list], msg.params)

    def test_build_wrong_type_raises(self):
        builder = osc_message_builder.OscMessageBuilder(address="/SYNC")
        builder.add_arg('this is not a float', builder.ARG_TYPE_FLOAT)
        self.assertRaises(osc_message_builder.BuildError, builder.build)

    def test_build_noarg_message(self):
        msg = osc_message_builder.OscMessageBuilder(address='/SYNC').build()
        # This reference message was generated with Cycling 74's Max software
        # and then was intercepted with Wireshark
        reference = bytearray.fromhex('2f53594e430000002c000000')
        self.assertSequenceEqual(msg._dgram, reference)

    def test_bool_encoding(self):
        builder = osc_message_builder.OscMessageBuilder('')
        builder.add_arg(0)
        builder.add_arg(1)
        builder.add_arg(False)
        builder.add_arg(True)
        self.assertEqual(builder.args, [("i", 0), ("i", 1), ("F", False), ("T", True)])


if __name__ == "__main__":
    unittest.main()
