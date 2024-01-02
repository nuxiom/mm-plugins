from ABaseGato import ABaseGato, require_alive

class StrongGato(ABaseGato):

    health: float = 140.0       # Override initial values for stats

    max_health: float = 140.0   # Create custom attributes for this gato class


    # Override default methods to use custom parameters and change behaviors
    @require_alive
    def affect_health(self, hp: float):
        self.health += hp

        if self.health > self.max_health:
            self.health = self.max_health
        elif self.health <= 0.0:
            self.health = 0.0
            self._fainted = True
