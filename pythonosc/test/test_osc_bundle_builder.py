import unittest

from pythonosc import osc_bundle_builder
from pythonosc import osc_message_builder


class TestOscBundleBuilder(unittest.TestCase):
    def test_empty_bundle(self):
        bundle = osc_bundle_builder.OscBundleBuilder(
            osc_bundle_builder.IMMEDIATELY).build()
        self.assertEqual(0, bundle.num_contents)

    def test_raises_on_build(self):
        bundle = osc_bundle_builder.OscBundleBuilder(0.0)
        bundle.add_content(None)
        self.assertRaises(osc_bundle_builder.BuildError, bundle.build)

    def test_raises_on_invalid_timestamp(self):
        bundle = osc_bundle_builder.OscBundleBuilder("I am not a timestamp")
        self.assertRaises(osc_bundle_builder.BuildError, bundle.build)

    def test_build_complex_bundle(self):
        bundle = osc_bundle_builder.OscBundleBuilder(
            osc_bundle_builder.IMMEDIATELY)
        msg = osc_message_builder.OscMessageBuilder(address="/SYNC")
        msg.add_arg(4.0)
        # Add 4 messages in the bundle, each with more arguments.
        bundle.add_content(msg.build())
        msg.add_arg(2)
        bundle.add_content(msg.build())
        msg.add_arg("value")
        bundle.add_content(msg.build())
        msg.add_arg(b"\x01\x02\x03")
        bundle.add_content(msg.build())

        sub_bundle = bundle.build()
        # Now add the same bundle inside itself.
        bundle.add_content(sub_bundle)

        bundle = bundle.build()
        self.assertEqual(5, bundle.num_contents)


if __name__ == "__main__":
    unittest.main()
