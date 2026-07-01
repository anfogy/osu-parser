from pathlib import Path
from struct import unpack
from typing import Any

from .structs import *

@dataclass(init=False, slots=True, repr=False)
class Replay(object):
    #region __slots__
    path: Path
    game_mode: GameMode
    game_version: int
    beatmap_md5: str
    player_name: str
    replay_md5: str
    hit_data: HitData
    total_score: int
    max_combo: int
    perfect_fc: bool
    mods: ModData
    hp_graph: LifeData
    timestamp: DotNetTick
    replay_frames: ReplayData
    online_score_id: int
    target_practice_hits: int
    score_info: ScoreInfo | None

    __initialized: bool
    __buffer: BufferReader
    __LZMAStreamLength: int
    __ScoreInfoStreamLength: int
    # endregion

    def __init__(self, pathStr: str | Path) -> None:
        super(Replay, self).__setattr__("_Replay__initialized", False)

        pathObj = Path(pathStr).expanduser().resolve()
        if not pathObj.exists():
            raise FileNotFoundError(f"Replay file {pathStr} not found")
        self.path = pathObj

        with open(pathObj, "rb") as f:
            rawData = f.read()
        self.__buffer = BufferReader(rawData)

        #region Attributes initialization
        # Metadata
        self.game_mode              = GameMode(self.__read(DataType.Byte))
        self.game_version           = self.__read(DataType.Integer)
        self.beatmap_md5            = self.__read(DataType.String)
        self.player_name            = self.__read(DataType.String)
        self.replay_md5             = self.__read(DataType.String)
        # Score report
        self.hit_data               = HitData(*unpack("<6H", self.__read(12)))
        self.total_score            = self.__read(DataType.Integer)
        self.max_combo              = self.__read(DataType.Short)
        self.perfect_fc             = bool(self.__read(DataType.Byte))
        self.mods                   = ModData(self.__read(DataType.Integer))
        self.hp_graph               = LifeData(self.__read(DataType.String))
        self.timestamp              = DotNetTick(self.__read(DataType.Long))
        # Replay data
        self.__LZMAStreamLength     = self.__read(DataType.Integer)
        self.replay_frames          = ReplayData(self.__read(self.__LZMAStreamLength))
        # Online score ID
        if self.game_version >= 20140721:
            self.online_score_id = self.__read(DataType.Long)
        elif self.game_version >= 20121008:
            self.online_score_id = self.__read(DataType.Integer)
        if self.online_score_id == 0:
            self.online_score_id = -1
        # Target practice
        if self.mods.get_raw() & Mod.TargetPractice.value:
            self.target_practice_hits = self.__read(DataType.Integer)
        # osu!lazer score info
        if self.game_version >= 30000001:
            self.__ScoreInfoStreamLength = self.__read(DataType.Integer)
            self.score_info = ScoreInfo(self.__read(self.__ScoreInfoStreamLength))
        else:
            self.score_info = None
        #endregion

        super(Replay, self).__setattr__("_Replay__initialized", True)

    def __setattr__(self, name: str, value: Any) -> None:
        if not getattr(self, "_Replay__initialized", False):
            super(Replay, self).__setattr__(name, value)
            return

        if name == "path":
            if not isinstance(fieldToCheck, fieldType):
                raise TypeError(f"Replay.{name} must be a {fieldType.__name__} object")
            print(f"Replay path has been modified to {value}, the replay object will be reconstructed.")
            self.__init__(value)
            return

        super(Replay, self).__setattr__(name, value)

    def __repr__(self):
        return f"Replay(path={self.path}, mods={self.mods}, player_name={self.player_name}, beatmap_md5={self.beatmap_md5})"

    def __read(self, dataLength: DataType | int) -> bytes | int | str:
        if isinstance(dataLength, int):
            byte = self.__buffer.read(dataLength)
            if len(byte) != dataLength:
                raise EOFError(f"Unexpected data length while reading {dataLength} bytes")
            return byte

        if dataLength in (DataType.Byte, DataType.Short, DataType.Integer, DataType.Long):
            byte = self.__buffer.read(dataLength.value)
            if len(byte) != dataLength.value:
                raise EOFError(f"Unexpected EOF while reading {dataLength.name}")
            return int.from_bytes(byte, byteorder='little')
        elif dataLength == DataType.ULEB128:
            encoded = bytearray()
            while True:
                byte = self.__buffer.read(1)
                if not byte:
                    raise EOFError("Unexpected EOF while reading ULEB128")
                encoded.append(byte[0])
                if not (byte[0] & 0x80):
                    break
            return ULEB128(encoded).value
        elif dataLength == DataType.String:
            flagByte = self.__buffer.read(1)
            if not flagByte:
                raise EOFError("Unexpected EOF while reading String flag")
            flag = flagByte[0]

            if flag == 0x00:
                return ""
            elif flag == 0x0B:
                length = self.__read(DataType.ULEB128)
                rawBytes = self.__buffer.read(length)
                if len(rawBytes) != length:
                    raise EOFError(f"Expected {length} bytes for string, got {len(rawBytes)}")
                return rawBytes.decode('utf-8')
            else:
                raise ValueError(f"Invalid string flag: 0x{flag:02X} (expected 0x00 or 0x0B)")
        else:
            raise ValueError(f"Unsupported DataType: {dataLength}")

    def get_raw_data(self) -> bytearray:
        return self.__buffer.copy()
