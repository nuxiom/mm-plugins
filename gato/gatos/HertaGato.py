from collections import Counter
from enum import Enum
import random

from ABaseGato import ABaseGato, require_alive


class HertaGato(ABaseGato):
    """
        > Fav Food: Ice Cream
        > Increases efficiency by 20% for 20 minutes after every hour.
        > Eidolons: e1->e5 (increases efficiency boost by 2%)
        > E6: (increases time to 30 minutes)
    """

    IMAGE = "https://cdn.discordapp.com/attachments/1198010808672723075/1198011033130901665/herta_gato.png"
    ANIMATIONS = "hertagato"
    DISPLAY_NAME = "Wisteria Cake"
    RARITY = 4
    VALUES_TO_SAVE = ABaseGato.VALUES_TO_SAVE + [
        "buff_duration",
        "buff_cooldown",
        "has_buff",
    ]

    HERTA_EVENT_TYPE_KURU_KURU = "herta_kuru_kuru"
    EVENT_DESCRIPTIONS = ABaseGato.EVENT_DESCRIPTIONS | {
        HERTA_EVENT_TYPE_KURU_KURU: "kuru kuru! x{count}"
    }

    # Custom variables used for this gato
    buff_duration: int = 0              # Remaining duration for its buff
    buff_cooldown: int = 0              # Remaining cooldown for its buff
    BUFF_KEY: str = "Herta_eff_buff"    # dict key to keep track of this gato's buffs

    @require_alive
    def efficiency_buff(self, seconds):
        # Update buff duration and cooldown
        self.buff_duration -= seconds
        self.buff_cooldown -= seconds

        # Apply buff if cooldown is over
        if self.buff_cooldown <= 0 or self.buff_duration > 0:
            # Apply efficiency boost
            eidolon_buff_increase = 0.02 * min(self.eidolon, 5)
            self.efficiency_boosts[self.BUFF_KEY] = 0.2 + eidolon_buff_increase

            # Set base cooldown and duration
            self.buff_duration += 20*60 if self.eidolon < 6 else 30*60
            self.buff_cooldown += 60*60

            # Fire event
            self._events.append({self.HERTA_EVENT_TYPE_KURU_KURU: None})

        # Remove buff if duration is over
        if self.buff_duration <= 0 and self.has_buff:
            self.efficiency_boosts.pop(self.BUFF_KEY)

    def simulate(self, team: list["ABaseGato"], seconds: int = 1):
        # We calculate its efficiency boost before its actions
        self.efficiency_buff(seconds)

        # Then call the parent simulation
        return super().simulate(team, seconds)
