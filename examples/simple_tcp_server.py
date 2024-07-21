"""Small example OSC server

This program listens to the specified address and port, and prints some information about
received packets.
"""
import argparse
import math

from pythonosc import osc_tcp_server
from pythonosc.dispatcher import Dispatcher


def print_volume_handler(unused_addr, args, volume):
    print("[{0}] ~ {1}".format(args[0], volume))


def print_compute_handler(unused_addr, args, volume):
    try:
        print("[{0}] ~ {1}".format(args[0], args[1](volume)))
    except ValueError:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip",
                        default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port",
                        type=int, default=5005, help="The port to listen on")
    parser.add_argument("--mode", default="1.1",
                        help="The OSC protocol version of the server (default is 1.1)")

    args = parser.parse_args()

    dispatcher = Dispatcher()
    dispatcher.map("/filter", print)
    dispatcher.map("/volume", print_volume_handler, "Volume")
    dispatcher.map("/logvolume", print_compute_handler, "Log volume", math.log)

    server = osc_tcp_server.ThreadingOSCTCPServer(
        (args.ip, args.port), dispatcher, mode=args.mode)
    print("Serving on {}".format(server.server_address))
    server.serve_forever()
