"""Representation of an OSC message in a pythonesque way."""

import logging

from parsing import osc_types


class ParseError(Exception):
  """Base exception raised when a datagram parsing error occurs."""


class OscMessage(object):
  """Representation of a parsed datagram representing an OSC message.

  An OSC message consists of an OSC Address Pattern followed by an OSC
  Type Tag String followed by zero or more OSC Arguments.
  """

  def __init__(self, dgram):
    self._dgram = dgram
    self._parameters = {}
    self._ParseDatagram()

  def _ParseDatagram(self):
    try:
      self._address_regexp, index = osc_types.GetString(self._dgram, 0)
      print("addr", self._address_regexp, index)
      if not self._dgram[index:]:
        # No params is legit, just return now.
        return

      # Get the parameters types.
      type_tag, index = osc_types.GetString(self._dgram, index)
      print("params ", type_tag, index)
      if type_tag.startswith(b','):
        type_tag = type_tag[1:]

      # Parse each parameter given its type.
      for i, param in enumerate(type_tag):
        if param == ord("i"):  # Integer.
          self._parameters[i], index = osc_types.GetInteger(self._dgram, index)
        elif param == ord("f"):  # Float.
          self._parameters[i], index = osc_types.GetFloat(self._dgram, index)
        elif param == ord("s"):  # String.
          self._parameters[i], index = osc_types.GetString(self._dgram, index)
        elif param == ord("b"):  # Blob.
          self._parameters[i], index = osc_types.GetBlob(self._dgram, index)
        # TODO: Support more exotic types as described in the specification.
        elif param == 0:
          # We've reached the end of the param string, finish now.
          return
        else:
          logging.warning('Unhandled parameter type: {0}'.format(param))
    except osc_types.ParseError as pe:
      raise ParseError('Found incorrect datagram, ignoring it', pe)

  @property
  def address(self):
    """Returns the OSC address regular expression."""
    return self._address_regexp

  @property
  def param_count(self):
    """Returns the number of parameters."""
    return len(self._parameters)

  @property
  def size(self):
    """Returns the length of the datagram for this message."""
    return len(self._dgram)

  def param(self, i):
    """Access parameters by 0-based index."""
    return self._parameters[i]
