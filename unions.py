from dataclasses import dataclass
@dataclass
class Union:
    clubs: dict
    rebate: float
    user_id: int
    name: str

@dataclass
class Club:
    jackpot: int
    comission: float
    name: str

@dataclass
class User:
    user_id: str
