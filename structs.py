from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, fields
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


class ULEB128(object):
    def __init__(self, value: int | bytes | bytearray):
        if isinstance(value, int):
            self.value = value
            self.bytes = self.__encode_int()
        elif isinstance(value, (bytes, bytearray)):
            self.bytes = bytes(value)
            self.value = self.__decode_bytes()
        else:
            raise TypeError("Value must be an int, bytes, or bytearray")

    def __encode_int(self) -> bytes:
        if self.value < 0:
            raise ValueError("ULEB128 value cannot be negative")

        buffer = []
        while True:
            byte = self.value & 0x7F
            self.value >>= 7
            if self.value != 0:
                byte |= 0x80
            buffer.append(byte)
            if self.value == 0:
                break
        return bytes(buffer)

    def __decode_bytes(self) -> int:
        result = 0
        shift = 0
        for byte in self.bytes:
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

    def __iter__(self):
        return (getattr(self, field.name) for field in fields(self))


class Mod(Enum):
    NoFail = 1 << 0
    Easy = 1 << 1
    TouchDevice = 1 << 2
    Hidden = 1 << 3
    HardRock = 1 << 4
    SuddenDeath = 1 << 5
    DoubleTime = 1 << 6
    Relax = 1 << 7
    HalfTime = 1 << 8
    Nightcore = 1 << 9
    Flashlight = 1 << 10
    Autoplay = 1 << 11
    SpunOut = 1 << 12
    Autopilot = 1 << 13
    Perfect = 1 << 14
    Key4 = 1 << 15
    Key5 = 1 << 16
    Key6 = 1 << 17
    Key7 = 1 << 18
    Key8 = 1 << 19
    FadeIn = 1 << 20
    Random = 1 << 21
    Cinema = 1 << 22
    TargetPractice = 1 << 23
    Key9 = 1 << 24
    KeyCoop = 1 << 25
    Key1 = 1 << 26
    Key3 = 1 << 27
    Key2 = 1 << 28
    ScoreV2 = 1 << 29
    Mirror = 1 << 30


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


class DotNetTick(datetime):
    __slots__ = ("__ticks",)
    __ticks: int

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
            dt.microsecond,
            tzinfo=timezone.utc
        )

        self.__ticks = ticks
        return self

    @property
    def ticks(self) -> int:
        return 621355968000000000 + int(self.timestamp() * 10_000_000)

    def __str__(self) -> str:
        return self.strftime("%m/%d/%Y %H:%M:%S %:z")


class ButtonState:
    _buttons = ()

    def __init__(self, raw_states: int):
        for i, name in enumerate(self._buttons):
            setattr(self, name, bool(raw_states & (1 << i)))

    @property
    def mask(self) -> int:
        value = 0
        for i, name in enumerate(self._buttons):
            if getattr(self, name):
                value |= 1 << i
        return value

    def __repr__(self) -> str:
        return f"{self.mask}"


class StandardButtonState(ButtonState):
    _buttons = ("M1", "M2", "K1", "K2", "Smoke")
    __slots__ = _buttons

    M1: bool
    M2: bool
    K1: bool
    K2: bool
    Smoke: bool


class ManiaButtonState(ButtonState):
    _buttons = (
        "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9",
        "K10", "K11", "K12", "K13", "K14", "K15", "K16", "K17", "K18"
    )
    __slots__ = _buttons

    K1: bool
    K2: bool
    K3: bool
    K4: bool
    K5: bool
    K6: bool
    K7: bool
    K8: bool
    K9: bool
    K10: bool
    K11: bool
    K12: bool
    K13: bool
    K14: bool
    K15: bool
    K16: bool
    K17: bool
    K18: bool


class TaikoButtonState(ButtonState):
    _buttons = ("left_don", "left_kat", "right_don", "right_kat")
    __slots__ = _buttons

    left_don: bool
    left_kat: bool
    right_don: bool
    right_kat: bool


class CTBButtonState(ButtonState):
    _buttons = "dash"
    __slots__ = _buttons

    dash: bool


@dataclass(slots=True)
class ReplayFrameBase(object):
    frame_time: int  # Frame time elapsed in millisecond


@dataclass(slots=True, repr=False)
class StandardReplayFrame(ReplayFrameBase):
    x_coordinate: float  # 0 ~ 512
    y_coordinate: float  # 0 ~ 384
    button_state: StandardButtonState

    def __repr__(self) -> str:
        return f"{self.frame_time}|{self.x_coordinate:.5f}|{self.y_coordinate:.5f}|{self.button_state}"


@dataclass(slots=True, repr=False)
class ManiaReplayFrame(ReplayFrameBase):
    button_state: ManiaButtonState

    def __repr__(self) -> str:
        return f"{self.frame_time}|{self.button_state}|0|0"


@dataclass(slots=True, repr=False)
class TaikoReplayFrame(ReplayFrameBase):
    button_state: TaikoButtonState

    def __repr__(self) -> str:
        return f"{self.frame_time}|0|0|{self.button_state}"


@dataclass(slots=True, repr=False)
class CTBReplayFrame(ReplayFrameBase):
    x_position: float # 0 ~ 512
    button_state: CTBButtonState

    def __repr__(self) -> str:
        return f"{self.frame_time}|{self.x_position:.5f}|0|{self.button_state}"


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
            if deltaTime == -12345:
                self.rng_seed = buttonStates
                continue

            lastTime += deltaTime
            if i < 2 and mouseX == 256 and mouseY == -500:
                continue

            self.append(
                StandardReplayFrame(
                    lastTime,
                    float(mouseX),
                    float(mouseY),
                    StandardButtonState(buttonStates)
                )
            )

        if len(self) >= 2 and self[1].frame_time < self[0].frame_time:
            self[1].frame_time, self[0].frame_time = self[0].frame_time, 0
        if len(self) >= 3 and self[0].frame_time > self[2].frame_time:
            self[0].frame_time = self[1].frame_time = self[2].frame_time

    def append(self, frame) -> None:
        if isinstance(frame, ReplayFrameBase):
            super().append(frame)
        else:
            raise TypeError(f"Frame must be of type ReplayFrameBase, not {type(frame)}")

    def get_raw(self) -> str:
        return self.__decompressedLZMAStreamData


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


@dataclass(repr=False)
class LifeFrame(object):
    frame_time: int
    percentage: float

    def __repr__(self):
        return f"{self.frame_time}|{self.percentage}"


class LifeData(list):
    def __init__(self, rawLifeFrameData: str):
        super().__init__()
        self.__rawLifeFrameData = rawLifeFrameData

        split = rawLifeFrameData.split(",")
        for chunk in split:
            if chunk:
                t, p = chunk.split("|", 2)
                self.append(LifeFrame(int(t), float(p)))

    def get_raw(self) -> str:
        return self.__rawLifeFrameData
