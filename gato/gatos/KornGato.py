from random import random

from ABaseGato import ABaseGato, require_alive

class KornGato(ABaseGato):
    # Kit parameters
    STATS_RESTORE_UPON_DEPLOYMENT: int = 10
    MAX_STATS_LOSS_DECREASE: float = 50
    MIN_STATS_LOSS_DECREASE: float = 20
    ADDITIONAL_DECREASE_PERCENTAGE_PER_EIDOLON: int = 2
    STATS_RESTORE_THRESHOLD: int = 20
    STATS_RESTORE_AMOUNT: int = 20
    STATS_RESTORE_E6_BOOST: int = 10

    IMAGE = "https://i.ibb.co/XSNVThW/korn-gato.png"
    ANIMATIONS = "korngato"
    DISPLAY_NAME = "Mocha Caramel"
    RARITY = 5
    VALUES_TO_SAVE = ABaseGato.VALUES_TO_SAVE + [
        "triggered_stats_restore"
    ]

    KORN_SELF_STATS_RESTORED_EVENT_TYPE = "korn_self_stats"
    KORN_TEAM_STATS_RESTORED_EVENT_TYPE = "korn_team_stats"
    EVENT_DESCRIPTIONS = ABaseGato.EVENT_DESCRIPTIONS | {
        KORN_SELF_STATS_RESTORED_EVENT_TYPE: "increased its own energy and hunger!",
        KORN_TEAM_STATS_RESTORED_EVENT_TYPE: "restored energy and hunger to the team!"
    }

    # Kit description
    __doc__ = f"""
        > Upon deployment, increases own hunger and energy by {STATS_RESTORE_AMOUNT}.
        > Decrease all allies hunger and energy consumption depending on {DISPLAY_NAME}'s own current energy and hunger,
        > starting at {MAX_STATS_LOSS_DECREASE}% at full hunger/energy, down to {MIN_STATS_LOSS_DECREASE} at minimum.
        > Once per deployment, when hunger __and__ energy go under {STATS_RESTORE_THRESHOLD}, restore {STATS_RESTORE_AMOUNT} hunger and energy to the team.
        > Eidolons: E1 -> E5: stats loss further decreases by {ADDITIONAL_DECREASE_PERCENTAGE_PER_EIDOLON}% for each eidolon.
        > E6: hunger and energy restore now trigger at {STATS_RESTORE_THRESHOLD+STATS_RESTORE_E6_BOOST} and restore {STATS_RESTORE_AMOUNT+STATS_RESTORE_E6_BOOST} hunger and energy.
    """

    # Custom variables used for this gato
    STATS_RED_KEY: str = "KG_stats_red" # dict key to keep track of this gato's stats reduction
    triggered_stats_restore: bool = False # whether stats restore was triggered for this expedition


    def deploy(self, team: list["ABaseGato"]):
        """Increase self hunger and energy on deploy"""
        self.add_energy(self.STATS_RESTORE_AMOUNT)
        self.add_hunger(self.STATS_RESTORE_AMOUNT)
        self._events.append({self.KORN_SELF_STATS_RESTORED_EVENT_TYPE: None})

        self.triggered_stats_restore = False


    @require_alive
    def stats_loss_reduction(self, team: list["ABaseGato"]):
        # Decrease stats loss for team
        min_reduction = self.MIN_STATS_LOSS_DECREASE + self.ADDITIONAL_DECREASE_PERCENTAGE_PER_EIDOLON*self.eidolon
        hunger_loss_reduction =  min_reduction + (self.MAX_STATS_LOSS_DECREASE - self.MIN_STATS_LOSS_DECREASE) * self.hunger / self.max_hunger
        energy_loss_reduction = min_reduction + (self.MAX_STATS_LOSS_DECREASE - self.MIN_STATS_LOSS_DECREASE) * self.energy / self.max_energy

        for gato in team:
            gato.hunger_reductions[self.STATS_RED_KEY] = hunger_loss_reduction / 100
            gato.energy_loss_reductions[self.STATS_RED_KEY] = energy_loss_reduction / 100

        # Trigger energy and hunger restoration
        if not self.triggered_stats_restore and self.hunger <= self.STATS_RESTORE_THRESHOLD and self.energy <= self.STATS_RESTORE_THRESHOLD:
            self.triggered_stats_restore = True

            total_restore = self.STATS_RESTORE_AMOUNT
            if self.eidolon >= 6:
                total_restore += self.STATS_RESTORE_E6_BOOST
            for gato in team:
                gato.add_hunger(total_restore)
                gato.add_energy(total_restore)
            self._events.append({self.KORN_TEAM_STATS_RESTORED_EVENT_TYPE: None})


    def simulate(self, team: list["ABaseGato"], seconds: int = 1):
        # We calculate its efficiency boost before its actions
        self.stats_loss_reduction(team)

        # Then call the parent simulation (VERY IMPORTANT)
        super().simulate(seconds)
