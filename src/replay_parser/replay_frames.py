from dataclasses import dataclass

from replayparser.src.replay_parser.button_states import StandardButtonState, ManiaButtonState, TaikoButtonState, CTBButtonState


@dataclass(slots=True)
class ReplayFrameBase(object):
    frame_time: int  # Frame time elapsed in millisecond


@dataclass(slots=True, repr=False)
class StandardReplayFrame(ReplayFrameBase):
    x_coordinate: float  # 0 ~ 512
    y_coordinate: float  # 0 ~ 384
    button_state: StandardButtonState

    def __repr__(self) -> str:
        return f"{self.frame_time}|{self.x_coordinate:.5f}|{self.y_coordinate:.5f}|{self.button_state}"


@dataclass(slots=True, repr=False)
class ManiaReplayFrame(ReplayFrameBase):
    button_state: ManiaButtonState

    def __repr__(self) -> str:
        return f"{self.frame_time}|{self.button_state}|0|0"


@dataclass(slots=True, repr=False)
class TaikoReplayFrame(ReplayFrameBase):
    button_state: TaikoButtonState

    def __repr__(self) -> str:
        return f"{self.frame_time}|0|0|{self.button_state}"


@dataclass(slots=True, repr=False)
class CTBReplayFrame(ReplayFrameBase):
    x_position: float # 0 ~ 512
    button_state: CTBButtonState

    def __repr__(self) -> str:
        return f"{self.frame_time}|{self.x_position:.5f}|0|{self.button_state}"
