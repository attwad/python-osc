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
    self._parse_datagram()

  def _parse_datagram(self):
    try:
      self._address_regexp, index = osc_types.get_string(self._dgram, 0)
      logging.debug('Found address {0}, index now {1}', self._address_regexp, index)
      if not self._dgram[index:]:
        # No params is legit, just return now.
        return

      # Get the parameters types.
      type_tag, index = osc_types.get_string(self._dgram, index)
      logging.debug('Found type tag {0}, index now {1}', type_tag, index)
      if type_tag.startswith(','):
        type_tag = type_tag[1:]

      # Parse each parameter given its type.
      for i, param in enumerate(type_tag):
        if param == "i":  # Integer.
          self._parameters[i], index = osc_types.get_int(self._dgram, index)
        elif param == "f":  # Float.
          self._parameters[i], index = osc_types.get_float(self._dgram, index)
        elif param == "s":  # String.
          self._parameters[i], index = osc_types.get_string(self._dgram, index)
        elif param == "b":  # Blob.
          self._parameters[i], index = osc_types.get_blob(self._dgram, index)
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

  @staticmethod
  def dgram_is_message(dgram):
    """Returns whether this datagram starts as an OSC message."""
    return dgram.startswith(b'/')

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

  def __iter__(self):
    """Returns an iterator over the parameters of this message."""
    return iter(self._parameters.values())
