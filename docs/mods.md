# ModData and Mod enum

## The `Mod` enum

The `Mod` enum (in `replay_parser.enums`) contains all osu! mods stated on [osu!api v1 docs](https://github.com/ppy/osu-api/wiki#mods) with their
**correct** bitmask values (e.g., `NoFail = 1`, `Easy = 2`, etc.).

```python
from replayparser.enums import Mod

print(Mod.HardRock)          # Mod.HardRock
print(Mod.HardRock.value)    # 16 (1 << 4)
```

You can combine mods as usual bit flags:

```python
raw = Mod.Hidden.value | Mod.HardRock.value
```

## The `ModData` class

`ModData` is a list of active `Mod` enums, plus the underlying raw integer.

```python
from replayparser.mod_data import ModData

m = ModData(24)              # 16 (HR) + 8 (HD)
print(m)                     # ModData([<Mod.Hidden: 8>, <Mod.HardRock: 16>], raw=11000)
```

### Properties / Methods

| Name          | Description                                      |
|---------------|--------------------------------------------------|
| `is_no_mod()` | Returns `True` if no mod is active (`raw == 0`). |
| `get_raw()`   | Returns the raw integer bitmask.                 |

### Iteration and membership

You can iterate over `ModData` and use `in` as with any list:

```python
if Mod.HardRock in r.mods:
    print("Hard Rock is active")
```

### Modifying mods for reconstruction

When you want to change the mods of a replay before writing, you must create a
new `ModData` with the desired raw value:

```python
new_raw = Mod.Hidden.value | Mod.DoubleTime.value
r.mods = ModData(new_raw)
```

The reconstruction will then use the new mods.

## List of all mods

| Name               | Value (bit)       |
|--------------------|-------------------|
| NoFail             | 1 << 0            |
| Easy               | 1 << 1            |
| TouchDevice        | 1 << 2            |
| Hidden             | 1 << 3            |
| HardRock           | 1 << 4            |
| SuddenDeath        | 1 << 5            |
| DoubleTime         | 1 << 6            |
| Relax              | 1 << 7            |
| HalfTime           | 1 << 8            |
| Nightcore          | 1 << 9            |
| Flashlight         | 1 << 10           |
| Autoplay           | 1 << 11           |
| SpunOut            | 1 << 12           |
| Autopilot          | 1 << 13           |
| Perfect            | 1 << 14           |
| Key1–Key9, KeyCoop | 1 << 26 … 1 << 15 |
| FadeIn             | 1 << 20           |
| Random             | 1 << 21           |
| Cinema             | 1 << 22           |
| TargetPractice     | 1 << 23           |
| ScoreV2            | 1 << 29           |
| Mirror             | 1 << 30           |

Key mods are mapped correctly even for the unusual order in the enum.
