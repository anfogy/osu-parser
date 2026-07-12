class ButtonStateBase:
    _buttons = ()

    def __init__(self, raw_states: int):
        for i, name in enumerate(self._buttons):
            setattr(self, name, bool(raw_states & (1 << i)))

    @property
    def mask(self) -> int:
        value = 0
        for i, name in enumerate(self._buttons):
            if getattr(self, name):
                value |= 1 << i
        return value

    def __repr__(self) -> str:
        return f"{self.mask}"


class StandardButtonState(ButtonStateBase):
    _buttons = ("M1", "M2", "K1", "K2", "Smoke")
    __slots__ = _buttons

    M1: bool
    M2: bool
    K1: bool
    K2: bool
    Smoke: bool


class ManiaButtonState(ButtonStateBase):
    _buttons = (
        "K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9",
        "K10", "K11", "K12", "K13", "K14", "K15", "K16", "K17", "K18"
    )
    __slots__ = _buttons

    K1: bool
    K2: bool
    K3: bool
    K4: bool
    K5: bool
    K6: bool
    K7: bool
    K8: bool
    K9: bool
    K10: bool
    K11: bool
    K12: bool
    K13: bool
    K14: bool
    K15: bool
    K16: bool
    K17: bool
    K18: bool


class TaikoButtonState(ButtonStateBase):
    _buttons = ("left_don", "left_kat", "right_don", "right_kat")
    __slots__ = _buttons

    left_don: bool
    left_kat: bool
    right_don: bool
    right_kat: bool


class CTBButtonState(ButtonStateBase):
    _buttons = "dash"
    __slots__ = _buttons

    dash: bool
