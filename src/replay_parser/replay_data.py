import lzma

from replayparser.src.replay_parser.button_states import StandardButtonState, TaikoButtonState, CTBButtonState, ManiaButtonState
from replayparser.src.replay_parser.enums import GameMode
from replayparser.src.replay_parser.replay_frames import StandardReplayFrame, ReplayFrameBase, TaikoReplayFrame, CTBReplayFrame, \
    ManiaReplayFrame


class ReplayData(list):
    __slots__ = ("rng_seed", "__decompressedLZMAStreamData")
    rng_seed: int
    __decompressedLZMAStreamData: str

    def __init__(self, rawLZMAStreamData: bytes, gameMode: GameMode) -> None:
        super().__init__()
        self.rng_seed = 0
        self.__decompressedLZMAStreamData = lzma.decompress(rawLZMAStreamData).decode("utf-8")

        streamDataChunks: list[str] = self.__decompressedLZMAStreamData.rstrip(",").split(",")
        lastTime: int = 0
        for i, chunk in enumerate(streamDataChunks):
            _chunkData = chunk.split("|")
            if len(_chunkData) < 4:
                continue

            deltaTime = int(_chunkData[0])
            x = float(_chunkData[1])
            y = float(_chunkData[2])
            buttonStates = int(_chunkData[3])
            if deltaTime == -12345:
                self.rng_seed = buttonStates
                continue

            lastTime += deltaTime
            if i < 2 and x == 256 and y == -500:
                continue

            if gameMode is GameMode.Standard:
                self.append(
                    StandardReplayFrame(
                        lastTime,
                        x,
                        y,
                        StandardButtonState(buttonStates)
                    )
                )
            elif gameMode is GameMode.Taiko:
                self.append(
                    TaikoReplayFrame(
                        lastTime,
                        TaikoButtonState(buttonStates)
                    )
                )
            elif gameMode is GameMode.CTB:
                self.append(
                    CTBReplayFrame(
                        lastTime,
                        x,
                        CTBButtonState(buttonStates)
                    )
                )
            elif gameMode is GameMode.Mania:
                self.append(
                    ManiaReplayFrame(
                        lastTime,
                        ManiaButtonState(int(x))
                    )
                )

        if len(self) >= 2 and self[1].frame_time < self[0].frame_time:
            self[1].frame_time, self[0].frame_time = self[0].frame_time, 0
        if len(self) >= 3 and self[0].frame_time > self[2].frame_time:
            self[0].frame_time = self[1].frame_time = self[2].frame_time

    def append(self, frame) -> None:
        if isinstance(frame, ReplayFrameBase):
            super().append(frame)
        else:
            raise TypeError(f"Frame must be of type ReplayFrameBase, not {type(frame)}")

    def get_raw(self) -> str:
        return self.__decompressedLZMAStreamData
