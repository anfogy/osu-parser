# osu!parser
osu!parser is a Python library for reading, inspecting, modifying, and
writing [osu!](https://osu.ppy.sh) replay files (`.osr`).

## Installation
Drop the `replay_parser` folder into your project.

## Quick Start
```python
from replay_parser import Replay

# Load from file
r = Replay("path/to/replay.osr")

# Access basic info
print(r.player_name)
print(r.mods)                # e.g. ModData([Hidden, HardRock], raw=...)
print(r.game_mode)           # GameMode.Standard, .Taiko, .CTB, or .Mania

# Inspect replay frames
for frame in r.replay_frames:
    print(frame)            # e.g. -144|233.88046|195.02953|0
```

You could also load a replay file from bytes:
```python
with open("replay.osr", "rb") as f:
    data = f.read()

r = Replay.from_bytes(data)
```

## Documentations
Detailed explanations of the main objects are available in separate guides:
* [Replay](docs/replay.md) – the main class, parsing, reconstruction, and writing.
* [ModData & Mods](docs/mods.md) – mods and their bitmask.
* [ReplayData & Frames](docs/replay_data.md) – frame data for all game modes.
* [ScoreInfo](docs/score_info.md) – osu!lazer extended score information.

## Acknowledgements

Based on the [osu! file format documentation](https://osu.ppy.sh/wiki/en/Client/File_formats/osr_%28file_format%29).
