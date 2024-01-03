def require_alive(function):
    def new_function(gato: ABaseGato, *args, **kwargs):
        if not gato._fainted:
            return function(gato, *args, **kwargs)

    return new_function



class ABaseGato:

    max_mood: float = 100.0
    max_hunger: float = 100.0
    max_energy: float = 100.0
    max_health: float = 100.0

    mood: float
    hunger: float
    energy: float
    health: float

    base_efficiency: float = 1.0
    efficiency: float

    _fainted: bool = False

    name: str


    def __init__(self, **kwargs):
        self.mood = self.max_mood
        self.hunger = self.max_hunger
        self.energy = self.max_energy
        self.health = self.max_health
        self.efficiency = self.base_efficiency

        self.name = self.__class__.__name__

        for k, v in kwargs.items():
            setattr(self, k, v)

        if self.health <= 0.0:
            self._fainted = True

    def to_json(self):
        return {
            "name": self.name,
            "type": self.__class__.__name__,
            "stats": {
                "mood": self.mood,
                "hunger": self.hunger,
                "energy": self.energy,
                "health": self.health,
                "efficiency": self.efficiency
            }
        }

    @classmethod
    def from_json(cls, json: dict):
        return cls(name=json["name"], **json["stats"])


    @require_alive
    def affect_health(self, hp: float):
        self.health += hp

        if self.health > self.max_health:
            self.health = self.max_health
        elif self.health <= 0.0:
            self.health = 0.0
            self._fainted = True
