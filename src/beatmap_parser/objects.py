# MIT License
#
# Copyright (c) 2021 Lenforiee
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# The following code based on Lenforiee's work (osupyparser), modified by caibi
# https://github.com/lenforiee/osupyparser/

from enum import Enum
from typing import List
from typing import Optional
from typing import Any
from dataclasses import dataclass

OSU_FILE_HEADER = "osu file format v"

@dataclass
class CurveType(Enum):
    Catmull = "C"
    Bezier = "B"
    Linear = "L"
    PassThrough = "P"

@dataclass
class ObjectType(int):
  CIRCLE = 1
  SLIDER = 1 << 1
  NEW_COMBO = 1 << 2
  SPINNER = 1 << 3
  COMBO_OFFSET = (1 << 4) | (1 << 5) | (1 << 6)
  HOLD = 1 << 7

@dataclass
class HitWindows(object):
    great: float    # Hit window for 300s
    ok: float       # Hit window for 100s
    meh: float      # Hit window for 50s
    miss: int       # Hit window for miss
    min_spins_per_sec: int

    @staticmethod
    def diff_range(od: float, val_min: float, val_mid: float, val_max: float) -> float:
        if od > 5:
            return val_mid + (val_max - val_mid) * ((od - 5) / 5)
        elif od < 5:
            return val_mid + (val_mid - val_min) * ((od - 5) / 5)
        else:
            return val_mid

@dataclass
class Position:
    """A (x, y) coordinates class."""
    x: int
    y: int

    def __getitem__(self, item):
        if item == 0:
            return self.x
        elif item == 1:
            return self.y

        raise IndexError


@dataclass
class Additions:
    """Represents a additions to hitobject class."""
    normal: Optional[str] = ""
    additional: Optional[str] = ""
    custom_sample_index: Optional[int] = ""
    volume: Optional[int] = 0
    filename: Optional[Any] = None

@dataclass
class Edge:
    """An additional class for slider edges."""
    sound_types: List[str]
    additions: Optional[Additions]

@dataclass
class TimingPoint:
    """Represents a standalone timing point."""
    offset: float
    beat_length: float
    time_signature: int
    sample_set_id: int
    custom_sample_index: int
    sample_volume: int
    timing_change: Optional[bool]
    kiai_time_active: Optional[bool]
    velocity: Optional[float] = None
    bpm: Optional[float] = None

@dataclass
class HitObject:
    """Subclass representing standalone hitobject."""
    pos: Position
    stacked_position: Optional[Position]
    start_time: int
    new_combo: bool
    sound_enum: int
    hit_windows: HitWindows

    def get_end_time(self):
        return self.end_time if hasattr(self, "end_time") else self.start_time

@dataclass
class Circle(HitObject):
    """Represents one circle object."""
    additions: Optional[Additions] = None

@dataclass
class Spinner(HitObject):
    """Represents one spinner object."""
    end_time: int
    additions: Optional[Additions] = None

@dataclass
class Slider(HitObject):
    """Represents one slider object."""
    repeat_count: int
    pixel_length: int
    edges: list[Edge]
    points: List[Position]
    duration: int
    end_time: int
    curve_type: CurveType
    end_position: Optional[Position]
    stacked_points: Optional[List[Position]] = None
    stacked_end_position: Optional[Position] = None
    additions: Optional[Additions] = None

@dataclass
class Color(object):
    r: int
    g: int
    b: int

    def __getitem__(self, item):
        if item == 0:
            return self.r
        elif item == 1:
            return self.g
        elif item == 2:
            return self.b

        raise IndexError