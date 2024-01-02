class ABaseGato:

    mood: float = 100.0
    hunger: float = 100.0
    energy: float = 100.0
    health: float = 100.0

    efficiency = 1.0

    def to_json(self):
        return {
            "class": self.__class__.__name__,
            "mood": self.mood,
            "hunger": self.hunger,
            "energy": self.energy,
            "health": self.health,
            "efficiency": self.efficiency
        }
