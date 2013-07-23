"""Build OSC messages for client applications."""

import pythonosc
from pythonosc import osc_message
from pythonosc.parsing import osc_types


class BuildError(Exception):
  """Error raised when an incomplete message is trying to be built."""


class OscMessageBuilder(object):
  """Builds arbitrary OscMessage instances."""

  ARG_TYPE_FLOAT = "f"
  ARG_TYPE_INT = "i"
  ARG_TYPE_STRING = "s"
  ARG_TYPE_BLOB = "b"

  _SUPPORTED_ARG_TYPES = (
      ARG_TYPE_FLOAT, ARG_TYPE_INT, ARG_TYPE_BLOB, ARG_TYPE_STRING)

  def __init__(self, address=None):
    """Initialize a new builder for a message.

    Args:
      - address: The osc address to send this message to.
    """
    self._address = address
    self._args = []

  @property
  def address(self):
    """Returns the OSC address this message will be sent to."""
    return self._address

  @address.setter
  def address(self, value):
    """Sets the OSC address this message will be sent to."""
    self._address = address

  @property
  def args(self):
    """Returns the (type, value) arguments list of this message."""
    return self._args

  # TODO: Make the arg type optional, use type() to determine what it is.
  def add_arg(self, arg_type, arg_value):
    """Add a typed argument to this message.

    Args:
      - arg_type: A value in ARG_TYPE_* defined in this class.
      - arg_value: The corresponding value for the argument.
    Raises:
      - ValueError: if the type is not supported.
    """
    if arg_type not in self._SUPPORTED_ARG_TYPES:
      raise ValueError(
          'arg_type must be one of {}'.format(self._SUPPORTED_ARG_TYPES))
    self._args.append((arg_type, arg_value))

  def build(self):
    """Builds an OscMessage from the current state of this builder.

    Raises:
      - BuildError: if the message could not be build or if the address
                    was empty.

    Returns:
      - an osc_message.OscMessage instance.
    """
    if not self._address:
      raise BuildError('OSC addresses cannot be empty')
    dgram = b''
    try:
      # Write the address.
      dgram += osc_types.write_string(self._address)
      if not self._args:
        return osc_message.OscMessage(dgram)

      # Write the parameters.
      arg_types = "".join([arg[0] for arg in self._args])
      dgram += osc_types.write_string(',' + arg_types)
      for arg_type, value in self._args:
        if arg_type == self.ARG_TYPE_STRING:
          dgram += osc_types.write_string(value)
        elif arg_type == self.ARG_TYPE_INT:
          dgram += osc_types.write_int(value)
        elif arg_type == self.ARG_TYPE_FLOAT:
          dgram += osc_types.write_float(value)
        elif arg_type == self.ARG_TYPE_BLOB:
          dgram += osc_types.write_blob(value)
        else:
          raise BuildError('Incorrect parameter type found {}'.format(arg_type))

      return osc_message.OscMessage(dgram)
    except osc_types.BuildError as be:
      raise BuildError('Could not build the message: {}'.format(be))
