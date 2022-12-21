from dataclasses import dataclass
from typing import Any

class PacketBase(object):

    def __init__(self, **kwargs) -> None:
        self.raw: dict = kwargs
        self._class: str = kwargs.get('cls')
        self.target_id: Any | None = kwargs.get('target_id', None)
        self.raw_data: dict | None = kwargs.get('data', None)

    def __contains__(self, item: str) -> bool:
        return item in self.raw

class WatchingElement(object):
    def __init__(self, **kwargs):
        self.url = kwargs.get('url')
        self.name = kwargs.get('name')

class Packet1(PacketBase):

    def __init__(self, **kwargs):
        from datetime import datetime

        super().__init__(**kwargs)

        if self.raw.data is not None:
            self.country_code: str = self.raw_data['country_code']
            self.id: int = self.raw_data['id']
            self.last_match: datetime = datetime.fromtimestamp(self.raw_data['last_match'])
            self.match_count: int = self.raw_data['match_count']
            self.match_lobby: str = self.raw_data['match_lobby']
            self.rm_1v1_mmr: int = self.raw_data['mmr_rm_1v1']
            self.name: str = self.raw_data['name']
            self.on_dashboard: bool = self.raw_data['on_dashboard']
            self.online: bool = self.raw_data['online']
            self.playing: bool = self.raw_data['playing']
            self.queue_num: int = self.raw_data['queue_num']
            self.rank_rm_1v1: int = self.raw_data['rank_rm_1v1']
            self.rank_tournament: int = self.raw_data['rank_tournament']

            # actually a URL
            self.spectate_link: str = self.raw_data['spectate_link']

            self.status: str = self.raw_data['status']
            self.streaming: bool = self.raw_data['streaming']
            self.team: str = self.raw_data['team']
            self.verified: bool = self.raw_data['verified']
            self.warning: bool = self.raw_data['warning']
            self.watching: list[WatchingElement] = [WatchingElement(**x) for x in self.raw_data['watching']]

