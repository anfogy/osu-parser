from replayparser.src.replay_parser.enums import Mod


class ModData(list):
    __slots__ = ("__raw",)
    __raw: int

    def __init__(self, raw: int) -> None:
        self.__raw = raw
        activeMods = [mod for mod in Mod if raw & mod.value]
        super().__init__(activeMods)

    def is_no_mod(self) -> bool:
        return self.__raw == 0

    def get_raw(self) -> int:
        return self.__raw

    def __repr__(self) -> str:
        return f"ModData({super().__repr__()}, raw={self.__raw:b})"
