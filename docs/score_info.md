# ScoreInfo

## Overview

Starting from game version `30000001` (osu!lazer), replays contain an additional
LZMA‑compressed JSON block with detailed score information.  
`ScoreInfo` (in `replayparser.score_info`) parses this data.

## Attributes

| Attribute                  | Type         | Description                                                   |
|----------------------------|--------------|---------------------------------------------------------------|
| `online_id`                | `int`        | Online score ID (redundant with `Replay.online_score_id`).    |
| `statistics`               | `dict`       | Per‑hit object counts (e.g., `{"great": 150, "ok": 5, ...}`). |
| `maximum_statistics`       | `dict`       | Maximum possible statistics on the map.                       |
| `mods`                     | `list[dict]` | List of mod objects with their settings.                      |
| `client_version`           | `str`        | Version string of the client.                                 |
| `rank`                     | `str`        | Letter rank (e.g., "S", "A").                                 |
| `user_id`                  | `int`        | osu! user ID.                                                 |
| `total_score_without_mods` | `int`        | Score before mod multipliers. (In Score V2)                   |
| `pauses`                   | `list`       | List of pause events (if any).                                |

## Example

```python
r = Replay("lazer_replay.osr")
if r.score_info is not None:
    print(r.score_info.statistics)
    # {'perfect': 320, 'miss': 1, ...}
    print(r.score_info.mods[0]['acronym'])  # e.g. 'HD'
```

## Empty score info

If the replay was created by an older client or the data is missing,
`r.score_info` will be `None`. When `ScoreInfo` is initialised with empty
bytes, its `__empty` flag is set and its `repr()` returns an empty string.

## Reconstruction

During reconstruction, the `ScoreInfo` object is serialised back to JSON
(using `repr()`) and re‑compressed with LZMA. This preserves the content but
may alter the exact byte representation (key ordering, whitespace).
For most use‑cases this is acceptable.
