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

import hashlib
import math
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Self

from .objects import Position, Additions, Edge, TimingPoint, \
    HitObject, Circle, Spinner, Slider, \
    CurveType, ObjectType, OSU_FILE_HEADER, Color


@dataclass(init=False, slots=True, repr=False)
class OsuFile:
    path: Path | None
    file_version: int

    # [General]
    audio_filename: str
    audio_lead_in: int
    preview_time: int
    countdown: int
    sample_set: str
    stack_leniency: float
    mode: int
    letterbox_in_breaks: bool
    widescreen_storyboard: bool

    # [Editor]
    distance_spacing: float
    beat_divisor: int
    grid_size: int
    timeline_zoom: float

    # [Metadata]
    title: str
    title_unicode: str
    artist: str
    artist_unicode: str
    creator: str
    version: str
    source: str
    tags: str
    beatmap_id: int
    beatmap_set_id: int

    # [Difficulty]
    hp: float
    cs: float
    od: float
    ar: float
    slider_multiplier: float
    slider_tick_rate: int

    # [Events]
    has_video: bool
    video_file: str
    background_file: str
    break_times: list[tuple[int, int]]
    storyboards: list

    # [TimingPoints]
    timing_points: list[TimingPoint]

    # [Colours]
    colors: dict[str, Color]

    # [HitObjects]
    hit_objects: list[HitObject]

    # Calculated / extra
    md5: str
    max_combo: int
    bpm: int
    total_hits: int
    play_time: float
    drain_time: float
    ncircles: int
    nsliders: int
    nspinners: int

    __buffer: BytesIO

    def __init__(self, file_path: str | Path) -> None:
        self.path = Path(file_path).expanduser().resolve()
        if not self.path.exists():
            raise FileNotFoundError(f"Beatmap file not found: {self.path}")
        raw = self.path.read_bytes()
        self.__buffer = BytesIO(raw)
        self.__attr_init()

    @classmethod
    def from_bytes(cls, raw_data: bytes) -> Self:
        self = cls.__new__(cls)
        self.path = None
        self.__buffer = BytesIO(raw_data)
        self.__attr_init()
        return self

    def __attr_init(self) -> None:
        raw = self.__buffer.getvalue()
        self.md5 = hashlib.md5(raw).hexdigest()
        content = raw.decode("utf-8-sig")
        lines = [line.strip() for line in content.split("\n")]

        # Header
        if not lines or not lines[0].startswith(OSU_FILE_HEADER):
            raise ValueError(f"Invalid file header – expected {OSU_FILE_HEADER}")
        self.file_version = int(lines[0][len(OSU_FILE_HEADER):])

        #region Initialise fields
        self.audio_filename = ""
        self.audio_lead_in = 0
        self.preview_time = 0
        self.countdown = 0
        self.sample_set = ""
        self.stack_leniency = 0.0
        self.mode = 0
        self.letterbox_in_breaks = False
        self.widescreen_storyboard = False

        self.distance_spacing = 0.0
        self.beat_divisor = 0
        self.grid_size = 0
        self.timeline_zoom = 0.0

        self.title = ""
        self.title_unicode = ""
        self.artist = ""
        self.artist_unicode = ""
        self.creator = ""
        self.version = ""
        self.source = ""
        self.tags = ""
        self.beatmap_id = 0
        self.beatmap_set_id = 0

        self.hp = 0.0
        self.cs = 0.0
        self.od = 0.0
        self.ar = 0.0
        self.slider_multiplier = 0.0
        self.slider_tick_rate = 0

        self.has_video = False
        self.video_file = ""
        self.background_file = ""
        self.break_times = []
        self.storyboards = []

        self.timing_points = []
        self.colors = {}
        self.hit_objects = []

        # Counters that will be incremented during hit‑object parsing
        self.ncircles = 0
        self.nsliders = 0
        self.nspinners = 0
        self.total_hits = 0

        # Derived values
        self.bpm = -1
        self.max_combo = 0
        self.play_time = 0.0
        self.drain_time = 0.0
        #endregion

        # Parse sections
        current_section = ""
        for line in lines[1:]:
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                current_section = line[1:-1].lower()
                continue
            if current_section:
                parser = getattr(self, f"_parse_{current_section}", None)
                if parser:
                    parser(line)

        # Derived statistics
        self._calculate_derived()

    def _apply_key_mapping(self, line: str,
                           mapping: list[tuple[str, str, callable]]) -> None:
        for key, attr, convert in mapping:
            prefix = f"{key}:"
            if line.startswith(prefix):
                value_str = line[len(prefix):].strip()
                setattr(self, attr, convert(value_str))
                return

    def _parse_general(self, line: str) -> None:
        self._apply_key_mapping(line, [
            ("AudioFilename",       "audio_filename",       str),
            ("AudioLeadIn",         "audio_lead_in",        int),
            ("PreviewTime",         "preview_time",         int),
            ("Countdown",           "countdown",            int),
            ("SampleSet",           "sample_set",           str),
            ("StackLeniency",       "stack_leniency",       float),
            ("Mode",                "mode",                 int),
            ("LetterboxInBreaks",   "letterbox_in_breaks",  lambda v: v == "1"),
            ("WidescreenStoryboard","widescreen_storyboard",lambda v: v == "1"),
        ])

    def _parse_editor(self, line: str) -> None:
        self._apply_key_mapping(line, [
            ("DistanceSpacing", "distance_spacing", float),
            ("BeatDivisor",     "beat_divisor",     int),
            ("GridSize",        "grid_size",        int),
            ("TimelineZoom",    "timeline_zoom",    float),
        ])

    def _parse_metadata(self, line: str) -> None:
        self._apply_key_mapping(line, [
            ("Title",          "title",          str),
            ("TitleUnicode",   "title_unicode",  str),
            ("Artist",         "artist",         str),
            ("ArtistUnicode",  "artist_unicode", str),
            ("Creator",        "creator",        str),
            ("Version",        "version",        str),
            ("Source",         "source",         str),
            ("Tags",           "tags",           str),
            ("BeatmapID",      "beatmap_id",     int),
            ("BeatmapSetID",   "beatmap_set_id", int),
        ])

    def _parse_difficulty(self, line: str) -> None:
        self._apply_key_mapping(line, [
            ("HPDrainRate",       "hp",                float),
            ("CircleSize",        "cs",                float),
            ("OverallDifficulty", "od",                float),
            ("ApproachRate",      "ar",                float),
            ("SliderMultiplier",  "slider_multiplier", float),
            ("SliderTickRate",    "slider_tick_rate",  int),
        ])

    def _parse_events(self, line: str) -> None:
        if "//" in line:
            return
        data = line.split(",")
        if not data:
            return

        if data[0] == "Video":
            self.has_video = True
            self.video_file = data[2].strip('"')
        elif data[0] == "0" and data[1] == "0":
            self.background_file = data[2].strip('"')
        elif data[0] == "2":
            self.break_times.append((int(data[1]), int(data[2])))

    def _parse_timingpoints(self, line: str) -> None:
        parts = line.split(",")
        tp = TimingPoint(
            offset=float(parts[0]),
            beat_length=float(parts[1]),
            velocity=1,
            time_signature=int(parts[2]),
            sample_set_id=int(parts[3]),
            custom_sample_index=int(parts[4]),
            sample_volume=int(parts[5]),
            timing_change=None if len(parts) <= 6 else parts[6] == "1",
            kiai_time_active=None if len(parts) <= 7 else parts[7] == "1",
        )

        if tp.beat_length:
            if not self.timing_points:
                tp.bpm = round(60000 / tp.beat_length)
                self.bpm = tp.bpm
            else:
                tp.velocity = abs(100 / tp.beat_length)

        self.timing_points.append(tp)

    def _parse_colors(self, line: str) -> None:
        sep = " : " if self.file_version < 128 else ": "
        name, rgb_str = line.split(sep, 1)
        print(rgb_str.split(","))
        r, g, b = map(int, rgb_str.split(","))
        self.colors[name.strip()] = Color(r, g, b)

    def _parse_hitobjects(self, line: str) -> None:
        data = line.split(",")
        _type = int(data[3])
        sound = int(data[4])
        new_combo = (_type & ObjectType.NEW_COMBO) == 4
        pos = Position(int(data[0]), int(data[1]))

        if _type & ObjectType.CIRCLE:
            self.ncircles += 1
            obj = Circle(pos=pos, start_time=int(data[2]), new_combo=new_combo, sound_enum=sound)
            if len(data) > 5:
                obj.additions = self._parse_addition(data[5])

        elif _type & ObjectType.SPINNER:
            self.nspinners += 1
            obj = Spinner(pos=pos, start_time=int(data[2]), new_combo=new_combo,
                          sound_enum=sound, end_time=int(data[5]))
            if len(data) > 6:
                obj.additions = self._parse_addition(data[6])

        elif _type & ObjectType.SLIDER:
            self.nsliders += 1
            duration = 0
            points_list = []
            edges = []

            timing = self._get_last_inherited_timing_point(int(data[2]))
            if timing:
                px_per_beat = self.slider_multiplier * 100 * timing.velocity
                beats = (float(data[7]) * int(data[6])) / px_per_beat
                if timing.timing_change:
                    multiplier = timing.beat_length
                else:
                    uninherited = self._get_last_uninherited_timing_point(int(data[2]))
                    multiplier = uninherited.beat_length
                duration = beats * multiplier

            points = (data[5] if len(data) > 5 else "").split("|")
            curve_type = CurveType(points[0]) if points else None
            for pt in points[1:]:
                x, y = pt.split(":")
                points_list.append(Position(int(x), int(y)))

            edge_sounds = (data[8] if len(data) > 8 else "").split("|")
            edge_adds   = (data[9] if len(data) > 9 else "").split("|")
            for i in range(int(data[6]) + 1):
                adds = self._parse_addition(edge_adds[i]) if i < len(edge_adds) else None
                snd  = edge_sounds[i] if i < len(edge_sounds) else None
                edges.append(Edge(snd, adds))

            obj = Slider(
                pos=pos,
                start_time=int(data[2]),
                new_combo=new_combo,
                sound_enum=sound,
                repeat_count=int(data[6]),
                pixel_length=int(float(data[7])),
                edges=edges,
                points=points_list,
                duration=duration,
                end_time=int(data[2]) + duration,
                curve_type=curve_type,
                end_position=points_list[-1] if points_list else pos,
            )
            if len(data) > 10:
                obj.additions = self._parse_addition(data[10])
        else:
            obj = HitObject(pos=pos, start_time=int(data[2]), new_combo=new_combo, sound_enum=sound)

        self.total_hits += 1
        self.hit_objects.append(obj)

    @staticmethod
    def _parse_addition(raw: str) -> Additions | None:
        if not raw:
            return None
        samples = {"1": "Normal", "2": "Soft", "3": "Drum"}
        parts = raw.split(":")
        kwargs = {}
        if len(parts) > 0:
            kwargs["normal"] = samples.get(parts[0])
        if len(parts) > 1:
            kwargs["additional"] = samples.get(parts[1])
        if len(parts) > 2:
            kwargs["custom_sample_index"] = int(parts[2])
        if len(parts) > 3:
            kwargs["volume"] = max(0, int(parts[3]))
        if len(parts) > 4:
            kwargs["filename"] = parts[4]
        return Additions(**kwargs)

    def _get_last_inherited_timing_point(self, offset: int) -> TimingPoint | None:
        for tp in reversed(self.timing_points):
            if tp.offset <= offset and not tp.timing_change:
                return tp
        return self.timing_points[0] if self.timing_points else None

    def _get_last_uninherited_timing_point(self, offset: int) -> TimingPoint | None:
        for tp in reversed(self.timing_points):
            if tp.offset <= offset and tp.timing_change:
                return tp
        return self.timing_points[0] if self.timing_points else None

    def _calculate_derived(self) -> None:
        self._calculate_max_combo()
        self._calculate_map_duration()

    def _calculate_max_combo(self) -> None:
        combo = 0
        tps = self.timing_points
        idx = -1
        px_per_beat = None
        next_offset = float("-inf")

        for obj in self.hit_objects:
            if not isinstance(obj, Slider):
                combo += 1
                continue

            while next_offset is not None and obj.start_time >= next_offset:
                idx += 1
                if len(tps) > idx + 1:
                    next_offset = tps[idx + 1].offset
                else:
                    next_offset = None
                tp = tps[idx]
                sv = 1.0
                if not tp.timing_change and tp.beat_length < 0:
                    sv = -100.0 / tp.beat_length
                px_per_beat = self.slider_multiplier * 100.0 * sv
                if self.file_version < 8:
                    px_per_beat /= sv

            beats = (obj.pixel_length * obj.repeat_count) / px_per_beat
            ticks = math.ceil((beats - 0.1) / obj.repeat_count * self.slider_tick_rate)
            ticks = max(0, ticks - 1) * obj.repeat_count + obj.repeat_count + 1
            combo += ticks

        self.max_combo = combo

    def _calculate_map_duration(self) -> None:
        if not self.hit_objects:
            return
        first, last = self.hit_objects[0], self.hit_objects[-1]
        total_break = sum(end - start for start, end in self.break_times)
        self.play_time = math.floor(last.start_time / 1000)
        self.drain_time = math.floor((last.start_time - first.start_time - total_break) / 1000)
