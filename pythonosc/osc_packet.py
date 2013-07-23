"""Use OSC packets to parse incoming UDP packets.

It gives easy access to OscMessage and OscBundle instances in the packet.
"""

import pythonosc
from pythonosc.parsing import osc_types
from pythonosc import osc_bundle
from pythonosc import osc_message

def _timed_msg_of_bundle(bundle):
  """Returns messages contained in nested bundles."""
  msgs = []
  for content in bundle:
    if type(content) == osc_message.OscMessage:
      msgs.append((bundle.timestamp, content))
    else:
      msgs.extend(_timed_msg_of_bundle(content))
  return msgs


class ParseError(Exception):
  """Base error thrown when a packet could not be parsed."""


class OscPacket(object):
  """Unit of transmission of the OSC protocol.

  Any application that sends OSC Packets is an OSC Client.
  Any application that receives OSC Packets is an OSC Server.
  """

  def __init__(self, dgram):
    """Initialize an OdpPacket with the given UDP datagram.

    Args:
      - dgram: the raw UDP datagram holding the OSC packet.

    Raises:
      - ParseError if the datagram could not be parsed.
    """
    try:
      if osc_bundle.OscBundle.dgram_is_bundle(dgram):
        # TODO: Handle the IMMEDIATELY case.
        self._messages = sorted(
            _timed_msg_of_bundle(osc_bundle.OscBundle(dgram)),
            key=lambda x: x[0])  # Sort by time, which is the first element.
      elif osc_message.OscMessage.dgram_is_message(dgram):
        self._messages = ((osc_types.IMMEDIATELY, osc_message.OscMessage(dgram)),)
      else:
        # Empty packet, should not happen as per the spec.
        raise ParseError(
            'OSC Packet should at least contain an OscMessage or an OscBundle.')
    except (osc_bundle.ParseError, osc_message.ParseError) as pe:
      raise ParseError('Could not parse packet %s' % pe)

  @property
  def messages(self):
    """Returns asc-time-sorted tuples of all the messages in this OscPacket."""
    return self._messages
