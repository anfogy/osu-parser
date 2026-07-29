import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import total_ordering
from typing import NamedTuple

from .. import diff_utils
from ..preprocessing import DifficultyHitObject
from replay_parser import ModData

# https://github.com/ppy/osu/blob/master/osu.Game/Rulesets/Difficulty/Skills/Skill.cs
class Skill(ABC):
    _mods: ModData
    _object_diff: list[float]

    def __init__(self, mods: ModData):
        self._mods = mods

    def get_mods(self):
        return self._mods

    def get_object_diffs(self) -> list[float]:
        return self._object_diff

    def process(self, current):
        diff_value = self._process_internal(current)
        self._object_diff.append(diff_value)

    @abstractmethod
    def _process_internal(self, current: DifficultyHitObject) -> float:
        pass

    @abstractmethod
    def difficulty_value(self) -> float:
        pass


# https://github.com/ppy/osu/blob/master/osu.Game/Rulesets/Difficulty/Skills/VariableLengthStrainSkill.cs
class VariableLengthStrainSkill(Skill, ABC):
    @total_ordering
    @dataclass(init=False, eq=False)
    class StrainPeak(object):
        value: float
        section_length: float

        def __init__(self, value: float, section_length: float):
            self.value = value
            self.section_length = round(section_length)

        def __eq__(self, other):
            return self.value == other.value

        def __lt__(self, other):
            return self.value < other.value
    class StrainData(NamedTuple):
        strain_value: float
        start_time: float

    _decay_weight: float
    _max_section_length: int

    __current_section_peak: float
    __current_section_begin: float
    __current_section_end: float

    __max_stored_length: float
    __strain_peaks: list[StrainPeak]
    __total_length: float

    __queued_strains: list[StrainData]

    __final_peak: StrainPeak | None

    def __init__(self, mods: ModData, decay_weight: float = 0.9, max_section_length: int = 400):
        super().__init__(mods)
        self._decay_weight = decay_weight
        self.max_section_length = max_section_length

        self.max_stored_length = 11 / (1 - decay_weight)

    @abstractmethod
    def _strain_value_at(self, current: DifficultyHitObject) -> float:
        pass

    def _process_internal(self, current: DifficultyHitObject) -> float:
        if current.index == 0:
            self.__current_section_begin = current.start_time
            self.__current_section_end = current.end_time

            self.__current_section_peak = self._strain_value_at(current)
            return self.__current_section_peak

        self.__backfill_peaks(current)

        current_strain = self._strain_value_at(current)
        if current_strain > self.__current_section_peak:
            self.__queued_strains.clear()

            self.__save_current_peak(current.start_time - self.__current_section_begin)

            self.__current_section_begin = current.start_time
            self.__current_section_end = current.end_time
            self.__current_section_peak = current_strain
        else:
            while self.__queued_strains and self.__queued_strains[-1].strain_value < current_strain:
                self.__queued_strains.pop()

            self.__queued_strains.append(self.StrainData(current_strain, current.start_time))

        return current_strain

    def __backfill_peaks(self, current: DifficultyHitObject) -> None:
        while current.start_time > self.__current_section_end:
            self.__save_current_peak(self.__current_section_end - self.__current_section_begin)
            self.__current_section_begin = self.__current_section_end

            if self.__queued_strains:
                current_queue = self.__queued_strains.pop(0)

                self.__current_section_end = current_queue.start_time + self.max_section_length
                self.__start_new_section_from(self.__current_section_begin, current)

                self.__current_section_peak = max(self.__current_section_peak, current_queue.strain_value)
            else:
                self.__current_section_end = self.__current_section_begin + self.max_section_length
                self.__start_new_section_from(self.__current_section_begin, current)

    def __save_current_peak(self, section_length: float) -> None:
        if self.__final_peak:
            self.__strain_peaks.remove(self.__final_peak)
            self.__final_peak = None

        peak = self.StrainPeak(self.__current_section_peak, section_length)
        self.__strain_peaks.append(peak)
        self.__total_length += section_length

        while self.__total_length > self.max_stored_length * self.max_section_length:
            self.__total_length -= self.__strain_peaks[-1].section_length
            self.__strain_peaks.pop()

    def __start_new_section_from(self, time: float, current: DifficultyHitObject) -> None:
        self.__current_section_peak = self._calculate_initial_strain(time, current)

    @abstractmethod
    def _calculate_initial_strain(self, time: float, current: DifficultyHitObject) -> float:
        pass

    def get_current_strain_peaks(self) -> list[StrainPeak]:
        if self.__final_peak:
            final_peak = self.StrainPeak(self.__current_section_peak, self.__current_section_end - self.__current_section_begin)
            self.__strain_peaks.append(final_peak)

        return self.__strain_peaks

    @abstractmethod
    def count_top_weighted_strains(self, diff_value: float) -> float:
        if not self._object_diff:
            return 0.0

        consistent_top_strain = diff_value * (1 - self._decay_weight)
        if consistent_top_strain == 0:
            return len(self._object_diff)

        return sum([diff_utils.logistic(s / consistent_top_strain, 0.88, 10, 1.1) for s in self._object_diff])


# https://github.com/ppy/osu/blob/master/osu.Game/Rulesets/Difficulty/Skills/HarmonicSkill.cs
class HarmonicSkill(Skill, ABC):
    _object_weight_sum: float
    _harmonic_scale: float = 1.0
    _decay_exponent: float = 0.9

    def _process_internal(self, current: DifficultyHitObject) -> float:
        return self._object_diff_of(current)

    @abstractmethod
    def _object_diff_of(self, current: DifficultyHitObject) -> float:
        pass

    @abstractmethod
    def _get_transformed_diffs(self, diffs: list[float]) -> list[float]:
        pass

    def difficulty_value(self) -> float:
        self._object_weight_sum = 0
        if self._object_diff:
            return 0.0

        difficulties = self._get_transformed_diffs(self._object_diff)
        difficulty = 0.0
        for i, obj in enumerate(sorted([o for o in difficulties if o > 0], reverse=True)):
            weight = (1 + (self._harmonic_scale / (1 + i))) / (math.pow(i, self._decay_exponent) + 1 + (self._harmonic_scale / (1 + i)))

            self._object_weight_sum += weight
            difficulty += obj * weight

        return difficulty

    @abstractmethod
    def count_top_weighted_object_diffs(self, diff_value: float) -> float:
        if not self._object_diff:
            return 0.0

        if self._object_weight_sum == 0:
            return 0.0

        consistent_top_object = diff_value / self._object_weight_sum
        if consistent_top_object == 0:
            return 0.0

        return sum([diff_utils.logistic(d / consistent_top_object, 0.88, 10, 1.1) for d in self._object_diff])

    @staticmethod
    def diff_to_performance(diff: float) -> float:
        return 4.0 * (diff ** 3)


# https://github.com/ppy/osu/blob/master/osu.Game/Rulesets/Difficulty/Skills/StrainSkill.cs
@abstractmethod
class StrainSkill(Skill, ABC):
    _decay_weight: float = 0.9
    _section_length: float = 400

    __current_section_peak: float
    __current_section_end: float

    __strain_peaks: list[float]

    @abstractmethod
    def _strain_value_at(self, current: DifficultyHitObject) -> float:
        pass

    def _process_internal(self, current: DifficultyHitObject) -> float:
        if current.index == 0:
            self.__current_section_end = math.ceil(current.start_time / self._section_length) * self._section_length

        while current.start_time > self.__current_section_end:
            self.__save_current_peak()
            self.__start_new_section_from(self.__current_section_end, current)
            self.__current_section_end += self._section_length

        strain = self._strain_value_at(current)
        self.__current_section_peak = max(strain, self.__current_section_peak)

        return strain

    def count_top_weighted_strains(self, diff_value: float) -> float:
        if not self._object_diff:
            return 0.0

        consistent_top_strain = diff_value * (1 - self._decay_weight)
        if consistent_top_strain == 0:
            return len(self._object_diff)

        return sum([diff_utils.logistic(s / consistent_top_strain, 0.88, 10, 1.1) for s in self._object_diff])

    def __save_current_peak(self) -> None:
        self.__strain_peaks.append(self.__current_section_peak)

    def __start_new_section_from(self, time: float, current: DifficultyHitObject) -> None:
        self.__current_section_peak = self._calculate_initial_strain(time, current)

    @abstractmethod
    def _calculate_initial_strain(self, time: float, current: DifficultyHitObject) -> float:
        pass

    def get_current_strain_peaks(self) -> list[float]:
        return self.__strain_peaks + [self.__current_section_peak]

    def difficulty_value(self) -> float:
        difficulty = 0.0
        weight = 1.0

        peaks = self.get_current_strain_peaks()
        for strain in sorted([o for o in peaks if o > 0], reverse=True):
            difficulty += strain * weight
            weight *= self._decay_weight

        return difficulty