import sys
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import asyncio


def filter_handler(address, *args):
    print(f"{address}: {args}")


dispatcher = Dispatcher()
dispatcher.map("/filter", filter_handler)

ip = "127.0.0.1"
port = 1337


async def loop():
    """Example main loop that only runs for 10 iterations before finishing"""
    for i in range(10):
        print(f"Loop {i}")
        await asyncio.sleep(1)


async def init_main():
    server = AsyncIOOSCUDPServer((ip, port), dispatcher, asyncio.get_event_loop())
    transport, protocol = await server.create_serve_endpoint()  # Create datagram endpoint and start serving

    await loop()  # Enter main loop of program

    transport.close()  # Clean up serve endpoint


if sys.version_info >= (3, 7):
    asyncio.run(init_main())
else:
    # TODO(python-upgrade): drop this once 3.6 is no longer supported
    event_loop = asyncio.get_event_loop()
    event_loop.run_until_complete(init_main())
    event_loop.close()
