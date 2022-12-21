from dataclasses import dataclass
from typing import *
from enum import Enum

class PacketBase(object):

    def __init__(self, **kwargs) -> None:
        self.raw: dict = kwargs
        self._class: str = kwargs.get('cls')
        self.target_id: Any | None = kwargs.get('target_id', None)
        self.raw_data: dict | None = kwargs.get('data', None)

    def __contains__(self, item: str) -> bool:
        return item in self.raw

    def __str__(self) -> str:
        from json import dumps
        return dumps(self.raw_data, indent=2, sort_keys=True)


class WatchingElement(object):
    def __init__(self, **kwargs):
        self.url = kwargs.get('url')
        self.name = kwargs.get('name')

class PlayerStatusType(Enum):
    UNDEFINED  = None
    RECORDING  = "rec"
    QUEUING    = "queuing"
    BANNED     = "banned"
    PLAYING    = "playing"
    CAPTUREAGE = "captureage"
    MATCHED    = "matched"
    SPECTATING = "spectating"
    LOBBY      = "lobby"
    DASHBOARD  = "dashboard"
    DODGED     = "dodged"

class PlayerUpdate(PacketBase):

    def __init__(self, **kwargs):
        from datetime import datetime
        from urllib.parse import urlparse, ParseResult

        super().__init__(**kwargs)

        if self.raw_data is None:
            return

        # Identifiers
        self.name: str = self.raw_data['name']
        self.country_code: str = self.raw_data.get('country_code', None)
        self.aoe_2id: int = self.raw_data['id']
        self.team: str = self.raw_data.get('team', None)

        self.last_match: datetime = datetime.fromtimestamp(self.raw_data.get('last_match', 0))

        # Game Info:
        self.match_count: int = self.raw_data['match_count']
        self.match_lobby_id: str | None = self.raw_data.get('match_lobby', None)
        self.rm_1v1_mmr: int = self.raw_data.get('mmr_rm_1v1', -1)
        self.rank_rm_1v1: int = self.raw_data.get('rank_rm_1v1', -1)
        self.rank_tournament: int | None = self.raw_data.get('rank_tournament', None)

        # States/Statuses
        self.online: bool = self.raw_data['online']
        self.playing: bool = self.raw_data['playing']

        self.status: PlayerStatusType = PlayerStatusType(self.raw_data.get('status', None))
        self.queue_num: int | None = self.raw_data.get('queue_num', None)

        self.streaming: bool = self.raw_data.get('streaming', False)
        if 'watching' in self.raw_data:
            self.watching: list[WatchingElement] = [WatchingElement(**x) for x in self.raw_data['watching']]

        self.spectate_link: ParseResult | None = urlparse(self.raw_data.get('spectate_link', None))

        # Internal to spec dashboard?
        self.on_dashboard: bool = self.raw_data.get('on_dashboard', False)
        self.verified: bool = self.raw_data['verified']
        self.warning: bool = self.raw_data['warning']

class Caster(object):

    def __init__(self, **kwargs):
        from urllib.parse import urlparse
        self.name: str = kwargs.get("name")
        self.aoe2id: int = kwargs.get("id")
        self.verified: bool = kwargs.get("verified")
        self.country: str = kwargs.get("country_code", None)
        self.stream_link = urlparse(kwargs.get('stream_link', None))
        self.stream_title: str = kwargs.get("stream_title", None)
        self.stream_viewers: int = kwargs.get("stream_viewers", 0)

class Game(PacketBase):

    class GameChat(object):
        pass

    class GameType(Enum):
        RM_TG = "TG"
        RM_1V1 = "1v1"

    def __init__(self, **kwargs):
        from datetime import datetime
        from urllib.parse import urlparse

        super().__init__(**kwargs)

        if self.raw_data is None:
            return

        # Game Metadata (ID, Link, TG v 1v1, RM v EW, Diplo, etc)
        self.game_id = self.raw_data.get('id')
        self.game_format = self.raw_data.get("diplomacy")
        self.team_size = self.raw_data.get("team_size")
        self.game_link = urlparse(self.raw_data.get("link"))
        self.game_ruleset = self.raw_data.get('game_type')
        self.map = self.raw_data.get("map")
        self.server = self.raw_data.get("server")
        self.rematch = self.raw_data.get("rematch")

        self.start_time : datetime = datetime.fromtimestamp(self.raw_data['start_timestamp'])
        self.countdown: datetime = datetime.fromtimestamp(self.raw_data.get('countdown', 0))

        self.can_spectate = self.raw_data.get("specs_allowed")

        # Live Game States
        self.paused = self.raw_data.get("paused")
        self.players = []
        self.teams = []

        # unfinished fields
        self.team_names = {}
        self.drafts = []
        self.casters: List[Caster] = [Caster(**x) for x in self.raw_data['casters']]


