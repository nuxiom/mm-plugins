from abc import ABC, abstractmethod
from random import random


def require_alive(function):
    def new_function(gato: "ABaseGato", *args, **kwargs):
        if not gato._fainted:
            return function(gato, *args, **kwargs)

    return new_function



class ABaseGato(ABC):

    max_mood: float = 100.0
    max_hunger: float = 100.0
    max_energy: float = 100.0
    max_health: float = 100.0

    mood: float
    hunger: float
    energy: float
    health: float

    base_efficiency: float = 1.0
    luck: float = 1.0
    efficiency_boost: float = 0.0

    _fainted: bool = False
    _events: list[dict] = []
    _time_deployed: int = 0

    name: str
    eidolon: int

    IMAGE: str = "https://cdn.discordapp.com/emojis/1173895764087414855.webp"
    EVENT_DESCRIPTIONS = {
        "fainted": "fainted.",
        "bitten": "is angry and bites you (x{count}). You lose **{amount}** {currency} in total"
    }
    BASE_EARN_RATE: float = 0.25
    BITE_CHANCE: float = 1/200


    def __init__(self, **kwargs):
        self.mood = self.max_mood
        self.hunger = self.max_hunger
        self.energy = self.max_energy
        self.health = self.max_health
        self.efficiency = self.base_efficiency

        self.name = self.__class__.__name__
        self.eidolon = 0

        for k, v in kwargs.items():
            setattr(self, k, v)

        if self.health <= 0.0:
            self._fainted = True

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "values": {
                "name": self.name,
                "mood": self.mood,
                "hunger": self.hunger,
                "energy": self.energy,
                "health": self.health,
                "efficiency_boost": self.efficiency_boost,
                "eidolon": self.eidolon
            }
        }

    @classmethod
    def from_json(cls, json: dict):
        return cls(**json["values"])


    def deploy(self):
        self._events = []
        self._time_deployed = 0

        if self.health > 0:
            self._fainted = False


    @require_alive
    def lose_stats_over_time(self, seconds):
        self.add_hunger(-0.01 * seconds)
        self.add_energy(-0.02 * seconds)

        if self._time_deployed >= 30*60:
            self.add_mood(-0.01 * seconds)

        if self.hunger < 10:
            self.add_health(-0.02 * seconds)

        if self.mood < 10:
            if random() < self.BITE_CHANCE:
                self._events.append({"bitten": None})


    @require_alive
    def compute_currency(self, seconds):
        total_efficiency = self.base_efficiency + self.efficiency_boost
        if self.energy < 10:
            total_efficiency -= 0.2
        elif self.energy < 20:
            total_efficiency -= 0.1

        return seconds * self.BASE_EARN_RATE * total_efficiency


    @require_alive
    def random_object(self, seconds):
        objects = []
        if self._time_deployed % 60 == 0 and self.efficiency >= 1:
            if random() < self.luck / 100:
                objects.append("Shiny thing")

        return objects


    @abstractmethod
    def simulate(self, team: list["ABaseGato"], seconds: int = 1):
        if self.health > 0:
            self._time_deployed += seconds

            self.lose_stats_over_time(seconds)

            currency = self.compute_currency(seconds)

            objects = self.random_object(seconds)

            return currency, objects
        else:
            return 0.0, []


    @require_alive
    def add_health(self, amount: float):
        self.health += amount

        if self.health > self.max_health:
            self.health = self.max_health
        elif self.health <= 0.0:
            self.health = 0.0
            self._fainted = True
            self._events.append({"fainted": None})


    @require_alive
    def add_mood(self, amount: float):
        self.mood += amount

        if self.mood > self.max_mood:
            self.mood = self.max_mood
        elif self.mood <= 0.0:
            self.mood = 0.0


    @require_alive
    def add_hunger(self, amount: float):
        self.hunger += amount

        if self.hunger > self.max_hunger:
            self.hunger = self.max_hunger
        elif self.hunger <= 0.0:
            self.hunger = 0.0


    @require_alive
    def add_energy(self, amount: float):
        self.energy += amount

        if self.energy > self.max_energy:
            self.energy = self.max_energy
        elif self.energy <= 0.0:
            self.energy = 0.0
