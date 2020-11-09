import asyncio
import datetime
import random
import websockets
import threading

def run_websocket_server():
    asyncio.set_event_loop(asyncio.new_event_loop())

    async def time(websocket, path):
        while True:
            now = datetime.datetime.utcnow().isoformat() + "Z"
            await websocket.send(now)
            await asyncio.sleep(random.random() * 3)

    start_server = websockets.serve(time, "127.0.0.1", 5678)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

websocket_thread = threading.Thread(target=run_websocket_server, args=())
websocket_thread.start()
