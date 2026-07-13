import hashlib
from datetime import datetime, timedelta, timezone


class DotNetTick(datetime):
    __slots__ = ("__ticks",)
    __ticks: int

    def __new__(cls, ticks: int, player_name: str, replay_md5: str, game_version: int):
        dt = datetime(1, 1, 1) + timedelta(microseconds=ticks // 10)
        tz = timezone.utc
        td = timedelta()
        if game_version >= 30000001:
            for offset_minutes in range(-12 * 60, 14 * 60 + 1, 15):
                td = timedelta(minutes=offset_minutes)
                tz = timezone(td)

                utc_naive = datetime(
                    dt.year, dt.month, dt.day,
                    dt.hour, dt.minute, dt.second, dt.microsecond
                )

                local_naive = utc_naive + td
                local_dt = local_naive.replace(tzinfo=tz)

                formatted = local_dt.strftime("%m/%d/%Y %H:%M:%S %:z")
                string = f"lazer-{player_name}-{formatted}"

                if hashlib.md5(string.encode("utf-8")).hexdigest() == replay_md5:
                    break

        dt += td
        self = super().__new__(
            cls,
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            dt.microsecond,
            tzinfo=tz
        )

        self.__ticks = ticks
        return self

    @property
    def ticks(self) -> int:
        return self.__ticks

    def __str__(self) -> str:
        return self.strftime("%m/%d/%Y %H:%M:%S %:z")
