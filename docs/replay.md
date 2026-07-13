# Replay class

## Overview

`Replay` is the central object that represents an entire osu! replay. You can create a `Replay` from a file or from raw bytes.

## Construction

```python
from replayparser import Replay

# From file
r = Replay("my_replay.osr")

# From bytes (e.g., downloaded from an API)
r = Replay.from_bytes(binary_data)
```

## Attributes

| Attribute              | Type                  | Description                                                       |
|------------------------|-----------------------|-------------------------------------------------------------------|
| `path`                 | `Path` or `None`      | Path to the original file (None if loaded from bytes).            |
| `game_mode`            | `GameMode`            | `Standard`, `Taiko`, `CTB`, or `Mania`.                           |
| `game_version`         | `int`                 | Numeric version (e.g., `30000018`).                               |
| `beatmap_md5`          | `str`                 | MD5 hash of the beatmap.                                          |
| `player_name`          | `str`                 | Player’s username.                                                |
| `replay_md5`           | `str`                 | MD5 hash of the replay data                                       |
| `hit_data`             | `HitData`             | Counts of 300s, 100s, 50s, misses, etc.                           |
| `total_score`          | `int`                 | Total score.                                                      |
| `max_combo`            | `int`                 | Maximum combo.                                                    |
| `perfect_fc`           | `bool`                | `True` if the play was a perfect full combo.                      |
| `mods`                 | `ModData`             | List of active mods (see [Mods](mods.md)).                        |
| `hp_graph`             | `LifeData`            | List of `LifeFrame` objects.                                      |
| `timestamp`            | `DotNetTick`          | Date/time of the play (UTC).                                      |
| `replay_frames`        | `ReplayData`          | List of per‑frame actions (see [ReplayData](replay_data.md)).     |
| `online_score_id`      | `int`                 | Online score ID, or `-1` if none.                                 |
| `target_practice_hits` | `int` or `None`       | Present only for TargetPractice mod.                              |
| `score_info`           | `ScoreInfo` or `None` | Additional osu!lazer score data (see [ScoreInfo](score_info.md)). |

## Methods

### `get_raw_data() -> bytes`

Returns the original binary content of the replay as it was read.

### `reconstruct_replay()`

Rebuilds the internal byte buffer from the current attribute values.  
This is useful if you have modified fields like `player_name` or `mods` and want
to obtain a new binary representation.  
After calling `reconstruct_replay()`, the `Replay` object is re‑initialised from
the new buffer (so all attributes reflect the updated data).

### `write_to_file(path=None, do_reconstruct=True)`

Writes the replay to a file.  
- If `path` is `None`, uses the original `path` attribute.  
- If `do_reconstruct` is `True` (default), calls `reconstruct_replay()` first.

Example:

```python
r = Replay("input.osr")
r.player_name = "NewName"          # Python allows attribute modification
r.write_to_file("output.osr")      # Automatically reconstructs, then saves
```

For now, reconstructions of osu!stable replays do **not** update the `replay_md5` hash.
