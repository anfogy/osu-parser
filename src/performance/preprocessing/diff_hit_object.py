from beatmap_parser import HitObject
from ..hit_result import HitResult


class DifficultyHitObject(object):
    diff_hit_objects: list["DifficultyHitObject"]
    index: int

    base_object: HitObject
    last_object: HitObject

    delta_time: float
    start_time: float
    end_time: float

    clock_rate: float

    hit_window_great: float

    def __init__(self, hit_object: HitObject, last_object: HitObject, clock_rate: float, objects: list["DifficultyHitObject"], index: int) -> None:
        self.diff_hit_objects = objects
        self.index = index

        self.base_object = hit_object
        self.last_object = last_object

        self.delta_time = (hit_object.start_time - last_object.start_time) / clock_rate
        self.start_time = hit_object.start_time / clock_rate
        self.end_time = hit_object.get_end_time()

        self.clock_rate = clock_rate

        self.hit_window_great = 2 * hit_object.hit_windows.great / clock_rate

    def previous(self, skip_count: int):
        index = self.index - (skip_count + 1)
        return self.diff_hit_objects[index] if 0 <= index < len(self.diff_hit_objects) else None

    def next(self, skip_count: int):
        index = self.index + (skip_count + 1)
        return self.diff_hit_objects[index] if 0 <= index < len(self.diff_hit_objects) else None
