"""Small example OSC client

This program sends 10 random values between 0.0 and 1.0 to the /filter address,
and listens for incoming messages for 1 second between each value.
"""

import argparse
import random

from pythonosc import tcp_client

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1", help="The ip of the OSC server")
    parser.add_argument(
        "--port", type=int, default=5005, help="The port the OSC server is listening on"
    )
    parser.add_argument(
        "--mode",
        default="1.1",
        help="The OSC protocol version of the server (default is 1.1)",
    )
    args = parser.parse_args()

    with tcp_client.SimpleTCPClient(args.ip, args.port, mode=args.mode) as client:
        for x in range(10):
            n = random.random()
            print(f"Sending /filter {n}")
            client.send_message("/filter", n)
            resp = client.get_messages(1)
            for r in resp:
                try:
                    print(r)
                except Exception as e:
                    print(f"oops {str(e)}: {r}")
