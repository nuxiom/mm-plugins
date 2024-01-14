from collections import Counter
from enum import Enum
import random

from ABaseGato import ABaseGato, require_alive


class RecoverableStat(Enum):
    MOOD = 1
    HUNGER = 2
    ENERGY = 3
    HEALTH = 4
    EFFICIENCY = 5

    def __str__(self):
        return self.name.lower()


class EfficiencyBoost:
    def __init__(self, duration_s, amount, is_active=False):
        self.duration_s = duration_s
        self.amount = amount
        self.is_active = is_active


class HertaGato(ABaseGato):
    """
        > Fav Food: Ice Cream
        > Increases efficiency by 20% for 20 minutes after every hour.
        > Eidolons: e1->e5 (increases efficiency boost by 2%)
        > E6: (increases time to 30 minutes)
    """

    IMAGE = "https://media.discordapp.net/attachments/435078369852260353/1192961669467488307/cyx_gato.png"
    ANIMATIONS = "4star"
    DISPLAY_NAME = "Herta Gato"
    RARITY = 4
    # VALUES_TO_SAVE = ABaseGato.VALUES_TO_SAVE + [
    #     "_buff_duration",
    #     "_buff_cooldown",
    #     "_has_buff",
    # ]

    EVENT_DESCRIPTIONS = ABaseGato.EVENT_DESCRIPTIONS | {
        "herta_efficiency_buff": "kuru kuru! x{count}"
    }

    # Custom variables used for this gato
    _buff_duration: int = 0
    _buff_cooldown: int = 0
    _has_buff: bool = False

    @require_alive
    def efficiency_buff(self, seconds):
        self._buff_duration -= seconds
        self._buff_cooldown -= seconds

        if self._buff_cooldown <= 0:
            # enable buff
            self.efficiency_boost += 0.2 + (0.02 * min(self.eidolon, 5))
            self._buff_duration = 20*60 if self.eidolon < 6 else 30*60 
            self._has_buff = True
            # reset cd to 1 hour
            self._buff_cooldown += 60*60
            # fire event
            self._events.append({"herta_efficiency_buff": None})

        if self._buff_duration <= 0 and self._has_buff:
            self.efficiency_boost -= 0.2 + (0.02 * min(self.eidolon, 5))
            self._has_buff = False

    def simulate(self, team: list["ABaseGato"], seconds: int = 1):
        # We calculate its efficiency boost before its actions
        self.efficiency_buff(seconds)
        # Then call the parent simulation
        return super().simulate(team, seconds)
