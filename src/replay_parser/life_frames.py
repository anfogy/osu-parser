from dataclasses import dataclass


@dataclass(repr=False)
class LifeFrame(object):
    frame_time: int
    percentage: float

    def __repr__(self):
        return f"{self.frame_time}|{self.percentage}"


class LifeData(list):
    def __init__(self, rawLifeFrameData: str):
        super().__init__()
        self.__rawLifeFrameData = rawLifeFrameData

        split = rawLifeFrameData.split(",")
        for chunk in split:
            if chunk:
                t, p = chunk.split("|", 2)
                self.append(LifeFrame(int(t), float(p)))

    def get_raw(self) -> str:
        return self.__rawLifeFrameData
