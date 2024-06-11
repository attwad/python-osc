""" Simple example code for communicating with OSC devices over a serial port
with SLIP wrapping. It will send a random value to the /filter address and then
block until it receives a message back.
"""
import argparse
import random

from pythonosc.osc_message_builder import OscMessageBuilder

from pythonosc import slip_client

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('device', help='TTY device to connect to', default='/dev/ttyACM0')
    parser.add_argument('--baudrate', type=int, help='Set baudrate for serial port', default=115200)
    args = parser.parse_args()

    client = slip_client.SLIPClient(args.device, baudrate=args.baudrate)

    # Send a message to /filter with a random value
    builder = OscMessageBuilder("/filter")
    builder.add_arg(random.random())
    client.send(builder.build())

    # Receive a message
    message = client.receive()
    if message is None:
        print("Disconnected")
    else:
        print(message.address, message.params)
