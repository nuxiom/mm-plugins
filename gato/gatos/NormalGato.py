from ABaseGato import ABaseGato, require_alive

class NormalGato(ABaseGato):
    """
        > A gato with 140 base HP.
    """

    max_health: float = 140.0   # Create custom attributes for this gato class


    def simulate(self, team: list["ABaseGato"], seconds: int = 1):
        return super().simulate(team, seconds)