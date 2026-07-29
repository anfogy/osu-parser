# https://github.com/ppy/osu/blob/master/osu.Game/Rulesets/Scoring/HitResult.cs

from enum import Enum


class HitResult(Enum):
    Perfect = "perfect"
    Great = "great"
    Good = "good"
    Ok = "ok"
    Meh = "meh"
    Miss = "miss"

    LargeTickHit = "large_tick_hit"
    SmallTickHit = "small_tick_hit"

    SliderTailHit = "slider_tail_hit"

    LargeBonus = "large_bonus"
    SmallBonus = "small_bonus"

    LargeTickMiss = "large_tick_miss"
    SmallTickMiss = "small_tick_miss"

    IgnoreHit = "ignore_hit"
    IgnoreMiss = "ignore_miss"

    NONE = "none"
    ComboBreak = "combo_break"

