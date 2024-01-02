class ABaseGato:

    mood: float = 100.0
    hunger: float = 100.0
    energy: float = 100.0
    health: float = 100.0

    efficiency: float = 1.0

    _fainted: bool = False


    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        if self.health <= 0.0:
            self._fainted = True

    def to_json(self):
        return {
            "type": self.__class__.__name__,
            "stats": {
                "mood": self.mood,
                "hunger": self.hunger,
                "energy": self.energy,
                "health": self.health,
                "efficiency": self.efficiency
            }
        }


    def affect_health(self, hp: float):
        if not self._fainted:
            self.health += hp

            if self.health > 100.0:
                self.health = 100.0
            elif self.health <= 0.0:
                self.health = 0.0
                self._fainted = True
