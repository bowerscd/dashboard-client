from logging import (DEBUG, FileHandler, Formatter, Handler, Logger,
                     StreamHandler, getLogger, ERROR)
from typing import Callable, Awaitable, Dict, Any, Tuple, Type
from .packets import *
from aiohttp import ClientSession
import asyncio


def _create_default_logger(level: int, file: str | None = None) -> Logger:
    l: Logger

    l = getLogger("aoe2dashboard")

    l.setLevel(level)
    fmt = Formatter('[%(levelname)s:%(name)s]%(asctime)s - %(message)s')

    h: Handler
    if file is None:
        h = StreamHandler()
    else:
        h = FileHandler(file)
    h.setLevel(level)
    h.setFormatter(fmt)

    l.addHandler(h)

    return l

class Client(object):
    __DASHBOARD_API_ENDPOINT__ = "wss://aoe2recs.com/dashboard/api/"

    __PACKET_IDS__ : Dict[int, Tuple[str, Type]]= {
        -1: ("unknown", PacketBase),
         0: ("login", PacketBase), #?
         1: ("player_update", PlayerUpdate),
         2: ("game_in_progress", Game),
         3: ('sync', PacketBase),
         4: ("game_listing_update", PacketBase),
         5: ("recorded_game_update", PacketBase),
         6: ("histogram_update", PacketBase),
         7: ("chat_update", PacketBase),
         8: ('unanalyzed', PacketBase),
         9: ("unanalyzed", PacketBase),
        10: ("map_stats_update", PacketBase),
        11: ("tournament_update", PacketBase),
        12: ("win_streak", PacketBase),
        13: ("unanalyzed", PacketBase),
        14: ("unanalyzed", PacketBase),
        15: ("social_update", PacketBase),
        16: ("match_vods", PacketBase),
        17: ("unanalyzed", PacketBase),
        18: ("unanalyzed", PacketBase),
        19: ("unanalyzed", PacketBase),
        20: ("unanalyzed", PacketBase),
        21: ("maps", PacketBase),
        22: ("unanalyzed", PacketBase),
        23: ("eapm_update", PacketBase),
        24: ("leaderboard", PacketBase),
        24: ("unanalyzed", PacketBase),
        25: ("unanalyzed", PacketBase),
    }

    def __init__(self, **kwargs) -> None:
        """
        Create a new dashboard client. New clients should derive
        from this class and override event_* functions.

        kwargs:
            url:      url to connect to. primarily used for unit testing
                      using the offline-collected packets.

            collect: write any recieved packets to a directory structure.
                        Used primarily for development of the client, and
                        should not be set in consumers.

            logger: used to set a custom logger.
        """
        self.__tsk = None
        self.__url = kwargs.get('url', Client.__DASHBOARD_API_ENDPOINT__)
        self.__collect_data = kwargs.get('collect', False)
        self.__logger = kwargs.get('logger', _create_default_logger(ERROR))
        self.__done = asyncio.Event()

    def run(self) -> None:
        """
        Start the client in an synchronous manner. This will:
        
            1.) Create a new event loop based on the current policy

            2.) Execute the server endlessly, blocking the main thread.

        """
        loop : asyncio.AbstractEventLoop = asyncio.get_event_loop_policy().get_event_loop()
        try:
            loop.run_until_complete(loop.create_task(self.__connect()))
        except KeyboardInterrupt:
            pass
        finally:
            loop.run_until_complete(loop.create_task(self.close()))


    async def __aenter__(self) -> 'Client':
        await self.run_async()
        return self

    async def __aexit__(self, *a) -> None:
        await self.close()

    async def run_async(self, tg: asyncio.TaskGroup | None = None) -> None:
        """
        Start the client in an asynchronous manner. This will not block
        the main thread.
        """

        try:
            if tg is None:
                self.__tsk = asyncio.create_task(self.__connect(), name=f"connect-{self.__url}")
            else:
                tg.create_task(self.__connect())
        except KeyboardInterrupt:
            pass

    async def wait(self):
        await self.__done.wait()
        if (self.__tsk.exception() != None):
            raise self.__tsk.exception()

    async def close(self):
        if self.__tsk is not None:
            self.__tsk.cancel()

    async def __connect(self) -> None:
        """
        Starts a connection to the websocket and processes messages,
        endlessly.
        """
        from json import loads
        from aiohttp import ServerDisconnectedError, WSMsgType

        retry = 1
        try:
            async with ClientSession() as s:
                while True:
                    async with s.ws_connect(self.__url) as self.__ws:
                        try:
                            async for msg in self.__ws:
                                match msg.type:
                                    case WSMsgType.TEXT:
                                        await self.__handle__message(loads(msg.data))
                                    case WSMsgType.CLOSE:
                                        break
                                    case _:
                                        raise ValueError()

                            # I believe this is the server cleanly closed our
                            # connection
                            break
                        except ServerDisconnectedError as e:
                            self.__logger.error(f"closed connection: {e}")
                            retry = retry ** 2
                            await asyncio.sleep(retry)
        except asyncio.CancelledError:
            pass
        finally:
            self.__done.set()

    async def __handle__message(self, msg : dict) -> None:
        """
        Internal message router, called on every message
        """
        _cls = -1
        fn_id = f"unknown"
        event: Tuple[str, PacketBase] = ("unknown", PacketBase)
        if 'cls' in msg and msg['cls'] in Client.__PACKET_IDS__:
            _cls = msg['cls']
            event = Client.__PACKET_IDS__[msg['cls']]

        try:
            await self.event_raw(msg)
            _fn: Callable[['Client', dict], Awaitable[None]] = getattr(self, f"event_{event[0]}")
            obj = object.__new__(event[1])
            obj.__init__(**msg)
            await _fn(obj)
        except Exception as e:
            from traceback import format_exception
            if isinstance(e, AssertionError):
                raise e
            self.__logger.error(f"error in processing {fn_id}")
            self.__logger.error(f"called with {msg}")
            self.__logger.error("".join(format_exception(e)))

        if self.__collect_data:
            from datetime import datetime
            from json import dump
            from os import makedirs

            makedirs(f"./events/{_cls}", mod=0o755, exist_ok=True)
            with open(f"./events/{_cls}/{datetime.now().timestamp()}.json", 'w') as f:
                dump(msg, f, indent=2, sort_keys=True)


    async def event_raw(self, data: Dict[str, Any]) -> None:
        """
        Called on all message packets with the raw message.
        Can be used as a fallback for all message types.
        """
        pass

    async def event_unanalyzed(self, packet: PacketBase) -> None:
        self.__logger.debug(f"unanalyzed packet: '{packet.raw}'")
        # self.__logger.debug(f"unknown packet: {dumps(packet.raw, indent=2)}")

    async def event_unknown(self, packet: PacketBase) -> None:
        self.__logger.warning(f"unknown packet: '{packet.raw}'")
        # self.__logger.debug(f"unknown packet: {dumps(packet.raw, indent=2)}")

    async def event_login(self, packet: PacketBase) -> None:
        """
        Called on cls '0'. Seems to always be null for all values - and
        clients always send null back.

        Probably shouldn't be overridden.
        """
        pass

    async def event_player_update(self, packet: PlayerUpdate) -> None:
        """
        Called on cls '1'. Seems to be called when an individual
        players' row on the dashboard changes.

        Can be used to determine what state a player is in.
        """
        pass

    async def event_game_in_progress(self, packet: PacketBase) -> None:
        """
        Called on cls '2'. Called when a game is in progress with a
        variety of information, including builds and the like.
        """
        pass

    async def event_sync(self, packet: PacketBase) -> None:
        """
        Called to sync multiple packets in one message. Typically
        appears immediately after connecting.
        
        Probably shouldn't be overriden. 
        """
        packets : list[dict] = packet.raw_data

        # could be done in parallel
        for p in packets:
            await self.__handle__message(p)

    async def event_game_listing_update(self, packet: PacketBase) -> None:
        """
        Called on cls '4'. Called to update the list of completed games.
        Has a wide array of information.
        """
        pass

    async def event_recorded_game_update(self, packet: PacketBase) -> None:
        pass

    async def event_histogram_update(self, msg: PacketBase) -> None:
        pass

    async def event_chat_update(self, msg: PacketBase) -> None:
        pass

    async def event_map_stats_update(self, packet: PacketBase) -> None:
        pass

    async def event_tournament_update(self, packet: PacketBase) -> None:
        pass

    async def event_social_update(self, msg: PacketBase) -> None:
        pass

    async def event_win_streak(self, msg: PacketBase) -> None:
        pass

    async def event_match_vods(self, msg: PacketBase) -> None:
        pass

    async def event_maps(self, msg: PacketBase) -> None:
        pass

    async def event_eapm_update(self, packet: PacketBase) -> None:
        pass

    async def event_leaderboard(self, packet: PacketBase) -> None:
        pass
