from dataclasses import dataclass, fields


@dataclass(slots=True)
class HitData(object):
    i300: int
    i100: int  # Number of 100s in osu!, 150s in osu!taiko, 100s in osu!catch, 100s in osu!mania
    i50: int  # Number of 50s in osu!, small fruit in osu!catch, 50s in osu!mania
    iGekis: int  # Number of Gekis in osu!, Max 300s in osu!mania
    iKatus: int  # Number of Katus in osu!, 200s in osu!mania
    iMisses: int

    def __iter__(self):
        return (getattr(self, field.name) for field in fields(self))
