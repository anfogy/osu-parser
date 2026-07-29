from dataclasses import dataclass
from math import floor
from typing import List

from .objects import TimingPoint
from .osu_file import OsuFile


@dataclass(slots=True)
class MapSettings:
    circle_radius: float    # In osu!pixel
    preempt: int            # In ms. The time when hit objects starts fading in before the actual hit time
    stack_window: int       # In ms. preempt * stack leniency

@dataclass(init=False, slots=True)
class Map(object):
    ar: float
    od: float
    cs: float
    slider_tick_rate: int
    slider_multiplier: float
    map_settings: MapSettings
    timing_points: List[TimingPoint]

    _map_data: OsuFile
    _stack_leniency: float
    _preempt: int
    _timing_point_offsets: List[float]

    def __init__(self, map_path: str):
        self._map_data = OsuFile(map_path)

        self.ar = self._map_data.ar
        self.od = self._map_data.od
        self.cs = self._map_data.cs
        self.slider_tick_rate = self._map_data.slider_tick_rate
        self.slider_multiplier = self._map_data.slider_multiplier
        self._stack_leniency = self._map_data.stack_leniency
        self._preempt = 1200 + 120 * (5 - self.ar) if self.ar < 5 else 1200 - 150 * (self.ar - 5) if self.ar > 5 else 1200
        self.map_settings = MapSettings(
            circle_radius=(54.4 - 4.48 * self.cs) * 1.00041 * 0.9,
            # https://osu.ppy.sh/wiki/en/Beatmap/Approach_rate#animation-timing
            preempt=self._preempt,
            # https://osu.ppy.sh/wiki/en/Beatmap/Stack_leniency#behaviour
            stack_window=floor(self._preempt * self._stack_leniency),
        )

        # For fast look-ups
        self._timing_point_offsets = [pt.offset for pt in self._map_data.timing_points]

        self.timing_points = self._map_data.timing_points

    def get_hit_objects(self):
        return self._map_data.hit_objects

    def get_last_uninherited_timing_point(self, offset: int) -> TimingPoint:
        LUT = self.timing_points
        try:
            LUT = self.timing_points[self._timing_point_offsets.index(offset):]
        except ValueError:
            pass

        for timing in reversed(LUT):
            if timing.offset <= offset and timing.timing_change and timing.bpm is not None:
                return timing

        return self.timing_points[0]

    def change_ar(self, ar: float):
        self.ar = max(0.0, min(10.0, ar))
        self._preempt = 1200 + 120 * (5 - self.ar) if self.ar < 5 else 1200 - 150 * (
                    self.ar - 5) if self.ar > 5 else 1200
        self.map_settings.preempt = self._preempt
        self.map_settings.stack_window = floor(self._preempt * self._stack_leniency)

    def change_cs(self, cs: float):
        self.cs = max(0.0, min(10.0, cs))
        self.map_settings.circle_radius = (54.4 - 4.48 * self.cs) * 1.00041 * 0.9
