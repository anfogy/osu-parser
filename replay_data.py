import lzma

from replayparser.button_states import StandardButtonState
from replayparser.replay_frames import StandardReplayFrame, ReplayFrameBase


class ReplayData(list):
    __slots__ = ("rng_seed", "__decompressedLZMAStreamData")
    rng_seed: int
    __decompressedLZMAStreamData: str

    def __init__(self, rawLZMAStreamData: bytes):
        super().__init__()
        self.rng_seed = 0
        self.__decompressedLZMAStreamData = lzma.decompress(rawLZMAStreamData).decode("utf-8")

        streamDataChunks: list[str] = self.__decompressedLZMAStreamData.split(",")
        lastTime: int = 0
        for i, chunk in enumerate(streamDataChunks):
            _chunkData = chunk.split("|")
            if len(_chunkData) < 4:
                continue

            deltaTime = int(_chunkData[0])
            mouseX = float(_chunkData[1])
            mouseY = float(_chunkData[2])
            buttonStates = int(_chunkData[3])
            if deltaTime == -12345:
                self.rng_seed = buttonStates
                continue

            lastTime += deltaTime
            if i < 2 and mouseX == 256 and mouseY == -500:
                continue

            self.append(
                StandardReplayFrame(
                    lastTime,
                    float(mouseX),
                    float(mouseY),
                    StandardButtonState(buttonStates)
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
