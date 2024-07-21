import argparse
import asyncio
import sys

from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_tcp_server import AsyncOSCTCPServer


def filter_handler(address, *args):
    print(f"{address}: {args}")


dispatcher = Dispatcher()
dispatcher.map("/filter", filter_handler)


async def loop():
    """Example main loop that only runs for 10 iterations before finishing"""
    for i in range(10):
        print(f"Loop {i}")
        await asyncio.sleep(10)


async def init_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1",
                        help="The ip of the OSC server")
    parser.add_argument("--port", type=int, default=5005,
                        help="The port the OSC server is listening on")
    parser.add_argument("--mode", default="1.1",
                        help="The OSC protocol version of the server (default is 1.1)")
    args = parser.parse_args()

    async with AsyncOSCTCPServer(args.ip, args.port, dispatcher, mode=args.mode) as server:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(server.start())
            tg.create_task(loop())


if sys.version_info >= (3, 7):
    asyncio.run(init_main())
else:
    # TODO(python-upgrade): drop this once 3.6 is no longer supported
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(init_main())
    event_loop.close()
