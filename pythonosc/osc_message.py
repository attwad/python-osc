"""Representation of an OSC message in a pythonesque way."""

import logging

from pythonosc.parsing import osc_types


class ParseError(Exception):
  """Base exception raised when a datagram parsing error occurs."""


class OscMessage(object):
  """Representation of a parsed datagram representing an OSC message.

  An OSC message consists of an OSC Address Pattern followed by an OSC
  Type Tag String followed by zero or more OSC Arguments.
  """

  def __init__(self, dgram):
    self._dgram = dgram
    self._parameters = []
    self._parse_datagram()

  def _parse_datagram(self):
    try:
      self._address_regexp, index = osc_types.get_string(self._dgram, 0)
      if not self._dgram[index:]:
        # No params is legit, just return now.
        return

      # Get the parameters types.
      type_tag, index = osc_types.get_string(self._dgram, index)
      if type_tag.startswith(','):
        type_tag = type_tag[1:]

      params = []
      param_stack = [params]
      # Parse each parameter given its type.
      for param in type_tag:
        if param == "i":  # Integer.
          val, index = osc_types.get_int(self._dgram, index)
        elif param == "f":  # Float.
          val, index = osc_types.get_float(self._dgram, index)
        elif param == "s":  # String.
          val, index = osc_types.get_string(self._dgram, index)
        elif param == "b":  # Blob.
          val, index = osc_types.get_blob(self._dgram, index)
        elif param == "r":  # RGBA.
          val, index = osc_types.get_rgba(self._dgram, index)
        elif param == "T": # True.
          val = True
        elif param == "F": # False.
          val = False
        elif param == "N": # Nil (None)
          val = None
        elif param == 'I': # Infinitum (no data)
          val = None
        elif param == "[": # Array start.
          array = []
          param_stack[-1].append(array)
          param_stack.append(array)
        elif param == "]": # Array stop.
          if len(param_stack) < 2:
            raise ParseError('Unexpected closing bracket in type tag: {0}'.format(type_tag))
          param_stack.pop()
        # TODO: Support more exotic types as described in the specification.
        else:
          logging.warning('Unhandled parameter type: {0}'.format(param))
          continue
        if param not in "[]I":
          param_stack[-1].append(val)
      if len(param_stack) != 1:
        raise ParseError('Missing closing bracket in type tag: {0}'.format(type_tag))
      self._parameters = params
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
  def size(self):
    """Returns the length of the datagram for this message."""
    return len(self._dgram)

  @property
  def dgram(self):
    """Returns the datagram from which this message was built."""
    return self._dgram

  @property
  def params(self):
    """Convenience method for list(self) to get the list of parameters."""
    return list(self)

  def __iter__(self):
    """Returns an iterator over the parameters of this message."""
    return iter(self._parameters)
