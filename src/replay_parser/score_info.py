import json
import lzma
from dataclasses import dataclass


@dataclass(slots=True, init=False, repr=False)
class ScoreInfo(object):
    online_id: int
    statistics: dict
    maximum_statistics: dict
    mods: list[dict]
    client_version: str
    rank: str
    user_id: int
    total_score_without_mods: int
    pauses: list

    __empty: bool
    __decompressedLZMAStreamData: str

    def __init__(self, rawData: bytes) -> None:
        if not rawData:
            self.__empty = True
            return

        self.__empty = False
        self.__decompressedLZMAStreamData = lzma.decompress(rawData).decode("utf-8")
        JSONObject = json.loads(self.__decompressedLZMAStreamData)

        self.online_id = JSONObject.get("online_id", 0)
        self.statistics = JSONObject.get("statistics", {})
        self.maximum_statistics = JSONObject.get("maximum_statistics", {})
        self.mods = JSONObject.get("mods", [])
        self.client_version = JSONObject.get("client_version", "")
        self.rank = JSONObject.get("rank", "")
        self.user_id = JSONObject.get("user_id", 0)
        self.total_score_without_mods = JSONObject.get("total_score_without_mods", 0)
        self.pauses = JSONObject.get("pauses", [])

    def __repr__(self) -> str:
        if self.__empty:
            return ""

        data = {
            "online_id": self.online_id,
            "statistics": self.statistics,
            "maximum_statistics": self.maximum_statistics,
            "mods": self.mods,
            "client_version": self.client_version,
            "rank": self.rank,
            "user_id": self.user_id,
            "total_score_without_mods": self.total_score_without_mods,
            "pauses": self.pauses,
        }

        return json.dumps(data)
