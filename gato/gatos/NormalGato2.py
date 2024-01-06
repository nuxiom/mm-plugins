from ABaseGato import ABaseGato, require_alive

class NormalGato2(ABaseGato):
    """
        > A gato with 140 base HP.
    """

    IMAGE = "https://media.discordapp.net/attachments/435078369852260353/1192962311330205766/emigato.png"
    ANIMATIONS = "3star"
    DISPLAY_NAME = "Cocoa Melon"
    RARITY = 3

    max_health: float = 140.0   # Create custom attributes for this gato class


    def simulate(self, team: list["ABaseGato"], seconds: int = 1):
        return super().simulate(team, seconds)