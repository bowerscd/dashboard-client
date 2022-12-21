from .client import Client
from .packets import PlayerStatusType
from typing import Dict, Any

if __name__ == "__main__":

    class _MainClient(Client):

        def __init__(self, **kwargs) -> None:
            from logging import getLogger, INFO
            self.__player_states = {}

            logger = getLogger()
            logger.setLevel(INFO)
            super().__init__(logger=logger)

        async def event_player_update(self, packet) -> None:
            if getattr(packet, 'name', None) == None:
                return

            if packet.name not in self.__player_states:
                self.__player_states[packet.name] = -1

            if packet.status != self.__player_states[packet.name]:
                from logging import info
                info(f"update: {packet.name} => ({self.__player_states.get(packet.name, None)} -> {packet.status})")
                self.__player_states[packet.name] = packet.status

            return await super().event_player_update(packet)

    try:
        m = _MainClient()
        m.run()
    except KeyboardInterrupt:
        print("interrupt")
        pass

