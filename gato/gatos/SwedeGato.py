from ABaseGato import ABaseGato, require_alive

class SwedeGato(ABaseGato):
    """
        > A gato with 500% base efficiency.
    """

    IMAGE = "https://media.discordapp.net/attachments/435078369852260353/1197974365439021176/swede_gato.png"
    ANIMATIONS = "swedegato"
    DISPLAY_NAME = "Pistachio Sesame"
    RARITY = 6

    base_efficiency: float = 5.0


    def simulate(self, team: list["ABaseGato"], seconds: int = 1):
        super().simulate(team, seconds)