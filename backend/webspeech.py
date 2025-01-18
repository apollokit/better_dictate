import asyncio
import json
import logging
import threading
from typing import Dict
from queue import Queue
import websockets

from backend.manager import app_mngr

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def do_webspeech(
        raw_stt_output_q: Queue,
        host: str = 'localhost',
        port: int = 5678
        ):
    """ Thread for running webspeech server and communicating with that
    server
    
    Sets up the webspeech server, then handles back and forth with it. The web
    speech engine itself is within the browser, on a web page. We communicate
    with that. This thread receives speech to text output from the web page, and
    sends commands back and forth

    Args:
        raw_stt_output_q: contains output string text from the webspeech
            speech to text engine.
    """

    shutdown_event = asyncio.Event()

    async def webspeech_transact(websocket):
        logger.info("Webspeech server started")

        # whether or not webspeech in browser has been put to sleep
        # the thread will take action to keep these two aligned
        webspeech_sleeping = app_mngr.sleeping

        while not shutdown_event.is_set():
            try:
                # msg = json.loads(await websocket.recv())
                raw_msg = await asyncio.wait_for(websocket.recv(),
                    timeout=0.5)
                msg = json.loads(raw_msg)
                
                #  we receive "hello"  from the webspeech web
                if msg['cmd'] == "hello":
                    await websocket.send('{"cmd": "start"}')
                    logger.info("Sent start command to webspeech")
                # we hear from web speech that it has started
                elif msg['cmd'] == "start":
                    webspeech_sleeping = False
                # If we received stt content from web speech
                # Example: {'cmd': 'phrase', 'results': [{'final': True, 'transcript': ' what day', 'confidence': 0.9060565829277039}]}
                elif msg['cmd'] == "phrase":
                    # If we're asleep, don't do anything for now
                    # note that we shouldn't be receiving text from the
                    # browser anyway, if we're sleeping
                    if app_mngr.sleeping:
                        continue

                    app_mngr.user_interacted()

                    results = msg['results']
                    # not sure what it means if there is more than one result, so
                    # be defensive here
                    is_final = results[0]['final']
                    # For now, only use output that's final, not in mid
                    # transcription
                    if is_final:
                        # logger.info("saw: {}".format(msg))
                        assert len(results) == 1
                        text = results[0]['transcript']
                        conf = results[0]['confidence']
                        logger.info("Adding to output queue: %s", text)
                        raw_stt_output_q.put(text)


            # upon timeout of websocket.recv(), we can do any required houskeeping
            except asyncio.TimeoutError:
                if app_mngr.sleeping and not webspeech_sleeping:
                    await websocket.send('{"cmd": "stop"}')
                    webspeech_sleeping = True
                elif not app_mngr.sleeping and webspeech_sleeping:
                    await websocket.send('{"cmd": "start"}')
                    webspeech_sleeping = False

            # shutdown if we received the signal
            if app_mngr.quitting:
                # todo: this currently doesn't work on darwin because nothing calls
                #  app_mngr's signal_quit() method
                logger.info("saw shutdown") 
                shutdown_event.set()

    # Code to set up and tear down the server

    async def run_server():
        # Start the server
        async with websockets.serve(webspeech_transact, host, port):
            logger.info(f"Webspeech server listening on {host}:{port}")
            # Keep the server running until shutdown event seen
            await shutdown_event.wait()
            logger.info("Server event loop terminating")


    # Start the asyncio loop in a separate thread
    def start_event_loop():
        asyncio.run(run_server())

    thread = threading.Thread(target=start_event_loop, daemon=True)
    thread.start()
    thread.join()
    logger.info("Webspeech thread terminated")
