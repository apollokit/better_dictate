import asyncio
import json
import logging
import threading
from typing import Dict
from queue import Queue
import websockets

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def webspeech_thread(
        raw_stt_output_q: Queue,
        events: Dict[str, threading.Event],
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
        events: dictionary of events for coordination between threads
    """
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)

    # whether or not webspeech is active in browser
    active = False
    shutdown_event = events['shutdown']
    sleep_event = events['sleep']

    async def webspeech_transact(websocket, path):
        # need this because of closure rules. See Fluent Python book, pg 201
        nonlocal active

        logger.info("Webspeech server started")
        shutdown = False
        while True and not shutdown:
            try:
                # msg = json.loads(await websocket.recv())
                raw_msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                msg = json.loads(raw_msg)
                
                #  we receive "hello"  from the webspeech web
                if msg['cmd'] == "hello":
                    await websocket.send('{"cmd": "start"}')
                    logger.info("Sent start command to webspeech")
                    active = True
                elif msg['cmd'] == "end":
                    logger.info("Saw end command from webspeech")
                    active = False
                # If we received stt content from web speech
                # Example: {'cmd': 'phrase', 'results': [{'final': True, 'transcript': ' what day', 'confidence': 0.9060565829277039}]}
                elif msg['cmd'] == "phrase":
                    # If we're asleep, don't do anything for now
                    if sleep_event.is_set():
                        continue

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
                        raw_stt_output_q.put(text)

            # upon timeout of websocket.recv(), we can do any required houskeeping
            except asyncio.TimeoutError:
                # shutdown if we received the signal
                if shutdown_event.is_set():
                    logger.info("saw shutdown") 
                    shutdown = True
                    stop_realtime_server()

    # Code to set up and tear down the server

    start_server = websockets.serve(webspeech_transact, host, port)

    # The method of stopping the server below is from https://www.programcreek.com/python/?code=aaugustin%2Fdjango-userlog%2Fdjango-userlog-master%2Fuserlog%2Ftests.py
    stop_server = asyncio.Future(loop=event_loop)
    stop_realtime_server = lambda: event_loop.call_soon_threadsafe(
        lambda: stop_server.set_result(True))

    realtime_server = event_loop.run_until_complete(start_server)
    event_loop.run_until_complete(stop_server)
    realtime_server.close()
    event_loop.run_until_complete(realtime_server.wait_closed())

    event_loop.close() 