# https://github.com/ppy/osu/blob/master/osu.Game/Rulesets/Difficulty/Utils/DiffUtils.cs

import math

clamp = lambda value, min_val, max_val: max(min_val, min(value, max_val))
sign = lambda x: 1 if x >= 0 else -1

SQRT2 = 1.4142135623730950

def bpm_to_ms(bpm: float, delimiter: int = 4) -> float:
    return 60000.0 / delimiter / bpm

def ms_to_bpm(ms: float, delimiter: int = 4) -> float:
    return 60000.0 / (delimiter * ms)

def logistic(x: float, midpoint_offset: float, multiplier: float = 1.0, max_value: float = 1.0) -> float:
    return max_value / (1 + math.exp(multiplier * (midpoint_offset - x)))

def logistic_max(exponent: float, max_value: float = 1.0) -> float:
    return max_value / (1 + math.exp(exponent))

def norm(p: float, values: list[float]):
    _sum = 0
    for v in values:
        _sum += math.pow(v, p)

    return math.pow(_sum, 1.0 / p)

def bell_curve(x: float, mean: float, width: float, multiplier: float = 1.0) -> float:
    return multiplier * math.exp(math.e * -(math.pow(x - mean, 2) / math.pow(width, 2)))

def smoothstep_bell_curve(x: float, mean: float, width: float) -> float:
    x -= mean
    x = (width - x) if x > 0 else (width + x)
    return smoothstep(x, 0, width)

def smoothstep_bell_curve2(x: float) -> float:
    x = 0.5 - math.fabs(x - 0.5)
    x = clamp(x * 2.0, 0.0, 1.0)

    return x * x * (3.0 - 2.0 * x)

def smoothstep(x: float, start: float, end: float) -> float:
    x = clamp((x - start) / (end - start), 0.0, 1.0)

    return x * x * (3.0 - 2.0 * x)

def smootherstep(x: float, start: float, end: float) -> float:
    x = clamp((x - start) / (end - start), 0.0, 1.0);

    return x * x * x * (x * (6.0 * x - 15.0) + 10.0)

def reverse_lerp(x: float, start: float, end: float) -> float:
    return clamp((x - start) / (end - start), 0.0, 1.0)

def erf(x: float) -> float:
    return math.erf(x)

def erfc(x: float) -> float:
    return math.erfc(x)

def erfInv(x: float) -> float:
    if x < -1.0:
        return -math.inf
    elif x > 1.0:
        return math.inf
    elif x == 0:
        return 0

    a = 0.147
    sgn = sign(x)
    x = math.fabs(x)

    ln = math.log(1 - x * x)
    t1 = 2 / (math.pi * a) + ln / 2
    t2 = ln / a
    baseApprox = math.sqrt(t1 * t1 - t2) - t1

    c = math.pow((x - 0.85) / 0.293, 8) if x >= 0.85 else 0.0
    return sgn * (math.sqrt(baseApprox) + c)
