"""Small example OSC server

This program listens to several addresses, and prints some information about
received packets.
"""

import argparse
import math

from pythonosc.dispatcher import Dispatcher
from pythonosc import osc_server


def echo_handler(client_addr, unused_addr, args):
    print(unused_addr, args)
    return (unused_addr, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port", type=int, default=5005, help="The port to listen on")
    args = parser.parse_args()

    dispatcher = Dispatcher()
    dispatcher.set_default_handler(echo_handler, True)

    server = osc_server.ThreadingOSCUDPServer((args.ip, args.port), dispatcher)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()
