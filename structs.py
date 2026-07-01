from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import lzma
import json


class BufferReader(bytearray):
    __slots__ = ("__pointer",)

    def __init__(self, source=None) -> None:
        super().__init__(source)
        self.__pointer = 0

    def read(self, n: int) -> bytes:
        chunk = self[self.__pointer:self.__pointer + n]
        self.__pointer += len(chunk)
        return bytes(chunk)

    def tell(self) -> int:
        return self.__pointer

    def insert_bytes_at(self, pos: int, data: bytes) -> None:
        self[pos:pos] = data

    def delete_bytes_at(self, pos: int, length: int) -> None:
        del self[pos:pos + length]

    def overwrite_bytes_at(self, pos: int, data: bytes) -> None:
        self[pos:pos + len(data)] = data


class ULEB128(object):
    def __init__(self, value):
        if isinstance(value, int):
            self.value = value
            self.bytes = self.__encode_int(value)
        elif isinstance(value, (bytes, bytearray)):
            self.bytes = bytes(value)
            self.value = self.__decode_bytes(self.bytes)
        else:
            raise TypeError("Value must be an int, bytes, or bytearray")

    def __encode_int(self, number: int) -> bytes:
        if number < 0:
            raise ValueError("ULEB128 value cannot be negative")

        buffer = []
        while True:
            byte = number & 0x7F
            number >>= 7
            if number != 0:
                byte |= 0x80
            buffer.append(byte)
            if number == 0:
                break
        return bytes(buffer)

    def __decode_bytes(self, byte_array: bytes) -> int:
        result = 0
        shift = 0
        for byte in byte_array:
            result |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                break
            shift += 7
        return result

    def __repr__(self):
        return f"ULEB128(int={self.value}, bytes={self.bytes!r})"


class DataType(Enum):
    Byte = 1
    Short = 2
    Integer = 4
    Long = 8
    ULEB128 = -1
    String = -2


class GameMode(Enum):
    Standard = 0
    Taiko = 1
    CTB = 3
    Mania = 4


@dataclass(slots=True)
class HitData(object):
    i300: int
    i100: int  # Number of 100s in osu!, 150s in osu!taiko, 100s in osu!catch, 100s in osu!mania
    i50: int  # Number of 50s in osu!, small fruit in osu!catch, 50s in osu!mania
    iGekis: int  # Number of Gekis in osu!, Max 300s in osu!mania
    iKatus: int  # Number of Katus in osu!, 200s in osu!mania
    iMisses: int


class Mod(Enum):
    NoFail = 1
    Easy = 2
    TouchDevice = 4
    Hidden = 8
    HardRock = 16
    SuddenDeath = 32
    DoubleTime = 64
    Relax = 128
    HalfTime = 256
    Nightcore = 512
    Flashlight = 1024
    Autoplay = 2048
    SpunOut = 4096
    Autopilot = 8192
    Perfect = 16384
    Key4 = 32768
    Key5 = 65536
    Key6 = 131072
    Key7 = 262144
    Key8 = 524288
    FadeIn = 1048576
    Random = 2097152
    Cinema = 4194304
    TargetPractice = 8388608
    Key9 = 16777216
    KeyCoop = 33554432
    Key1 = 67108864
    Key3 = 134217728
    Key2 = 268435456
    ScoreV2 = 536870912
    Mirror = 1073741824


class ModData(list):
    __slots__ = ("__raw",)

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


class DotNetTick(datetime):
    __slots__ = ("ticks",)

    def __new__(cls, ticks: int):
        dt = datetime(1, 1, 1) + timedelta(microseconds=ticks // 10)

        self = super().__new__(
            cls,
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond
        )

        self.ticks = ticks
        return self


@dataclass(slots=True, repr=False)
class ButtonState(object):
    M1: bool
    M2: bool
    K1: bool
    K2: bool
    Smoke: bool

    __rawStates: int

    def __init__(self, rawStates: int) -> None:
        self.__rawStates = rawStates

        self.M1 = bool(rawStates & 1)
        self.M2 = bool(rawStates & 2)
        self.K1 = bool(rawStates & 4)
        self.K2 = bool(rawStates & 8)
        self.Smoke = bool(rawStates & 16)

    def __repr__(self):
        return f"{self.__rawStates:05b}"


@dataclass(slots=True, repr=False)
class ReplayFrame(object):
    frame_time: int      # in millisecond
    x_coordinate: float  # 0 ~ 512
    y_coordinate: float  # 0 ~ 384
    button_state: ButtonState

    def __repr__(self) -> str:
        return f"{self.frame_time}|{self.x_coordinate}|{self.y_coordinate}|{self.button_state}"


class ReplayData(list):
    __slots__ = ("rng_seed", "__decompressedLZMAStreamData")
    rng_seed: int
    __decompressedLZMAStreamData: str

    def __init__(self, rawLZMAStreamData: bytes):
        super().__init__()
        self.rng_seed = 0
        self.__decompressedLZMAStreamData = lzma.decompress(rawLZMAStreamData).decode("utf-8")

        streamDataChunks: list[str] = self.__decompressedLZMAStreamData.split(",")
        lastTime: int = 0
        for i, chunk in enumerate(streamDataChunks):
            _chunkData = chunk.split("|")
            if len(_chunkData) < 4:
                continue

            deltaTime = int(_chunkData[0])
            mouseX = float(_chunkData[1])
            mouseY = float(_chunkData[2])
            buttonStates = int(_chunkData[3])
            if deltaTime == "-12345":
                self.rng_seed = buttonStates
                continue

            lastTime += deltaTime
            if i < 2 and mouseX == 256 and mouseY == -500:
                continue

            if deltaTime < 0:
                continue

            self.append(
                ReplayFrame(
                    lastTime,
                    float(mouseX),
                    float(mouseY),
                    ButtonState(buttonStates)
                )
            )

        if len(self) >= 2 and self[1].frame_time < self[0].frame_time:
            self[1].frame_time, self[0].frame_time = self[0].frame_time, 0
        if len(self) >= 3 and self[0].frame_time > self[2].frame_time:
            self[0].frame_time = self[1].frame_time = self[2].frame_time


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

    __decompressedLZMAStreamData: str

    def __init__(self, rawData: bytes) -> None:
        if not rawData:
            return

        self.__decompressedLZMAStreamData = lzma.decompress(rawData).decode("utf-8")
        JSONObject = json.loads(self.__decompressedLZMAStreamData)

        self.online_id = JSONObject["online_id"]
        self.statistics = JSONObject["statistics"]
        self.maximum_statistics = JSONObject["maximum_statistics"]
        self.mods = JSONObject["mods"]
        self.client_version = JSONObject["client_version"]
        self.rank = JSONObject["rank"]
        self.user_id = JSONObject["user_id"]
        self.total_score_without_mods = JSONObject["total_score_without_mods"]
        self.pauses = JSONObject["pauses"]

    def __repr__(self):
        return f"{self.__decompressedLZMAStreamData}"


@dataclass(repr=False)
class LifeFrame(object):
    frame_time: int
    percentage: float

    def __repr__(self):
        return f"{self.frame_time}|{self.percentage}"

class LifeData(list):
    def __init__(self, rawLifeFrameData: str):
        super().__init__()

        split = rawLifeFrameData.split(",")
        for chunk in split:
            if chunk:
                t, p = chunk.split("|", 2)
                self.append(LifeFrame(int(t), float(p)))
