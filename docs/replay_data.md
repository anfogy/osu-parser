# ReplayData and Frames

## ReplayData class

`ReplayData` (in `replay_parser.replay_data`) is a list of per‑frame actions, 
automatically decompressed from the LZMA stream found in the `.osr` file.

It is a subclass of `list` and only accepts `ReplayFrameBase` instances.

### Attributes

| Name        | Type  | Description                                                        |
|-------------|-------|--------------------------------------------------------------------|
| `rng_seed`  | `int` | Random seed used during the play, extracted from the last chunk.   |
| `get_raw()` | `str` | Returns the **original** decompressed LZMA string (for reference). |

### Parsing behaviour

During parsing:

- Absolute frame times are accumulated from the delta values.
- The first two frames with coordinates `(256, -500)` are skipped (osu! cursor
  initialisation).
- The final chunk with `deltaTime = -12345` is used to extract the `rng_seed`.

## Replay frames

The library provides one base class and four game‑mode specific subclasses:

```python
from replay_parser.replay_frames import (
    ReplayFrameBase,
    StandardReplayFrame,
    ManiaReplayFrame,
    TaikoReplayFrame,
    CTBReplayFrame
)
```

### Common field

All frames have:

- `frame_time` : absolute time in milliseconds since the start of the replay.

### Game‑mode specifics

- **StandardReplayFrame**  
  `x_coordinate`, `y_coordinate` (float) and `button_state` (`StandardButtonState` with M1, M2, K1, K2, Smoke).

- **ManiaReplayFrame**  
  `button_state` (`ManiaButtonState` with K1–K18).

- **TaikoReplayFrame**  
  `button_state` (`TaikoButtonState` with left/right don and kat).

- **CTBReplayFrame**  
  `x_position` and `button_state` (`CTBButtonState` with dash).

### Representation

All frames have a `__repr__` that outputs the classic osu! replay string format:

```python
>>> frame
2451|256.00000|192.00000|5
```

This is also the format used internally during reconstruction.

### Button states

Each frame’s button state is an object with boolean attributes.  
For standard mode:

```python
frame.button_state.M1   # True if left mouse is pressed
frame.button_state.K1   # True if keyboard key 1 is pressed
```

You can also obtain the raw mask with `frame.button_state.mask`.

### Example: Iterating through frames

```python
for frame in r.replay_frames:
    if isinstance(frame, StandardReplayFrame):
        print(f"t={frame.frame_time}ms, x={frame.x_coordinate:.1f}, y={frame.y_coordinate:.1f}")
```
