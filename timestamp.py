from datetime import datetime, timedelta, timezone


class DotNetTick(datetime):
    __slots__ = ("__ticks",)
    __ticks: int

    def __new__(cls, ticks: int):
        dt = datetime(1, 1, 1) + timedelta(microseconds=ticks // 10)
        self = super().__new__(
            cls,
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            tzinfo=timezone.utc
        )

        self.__ticks = ticks
        return self

    @property
    def ticks(self) -> int:
        return 621355968000000000 + int(self.timestamp() * 10_000_000)

    def __str__(self) -> str:
        return self.strftime("%m/%d/%Y %H:%M:%S %:z")
