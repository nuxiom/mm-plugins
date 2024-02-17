from datetime import datetime, timezone

from ABaseGato import ABaseGato, require_alive


class GuinaifenGato(ABaseGato):
    """
        > Fav Food: Shumai
        > Upon deployment Increases all allies’ energy and mood by 20 (daily limit of 2). After going under 100, decreases energy/mood consumption by 10%. 
        > Eidolons: e1->e5 (decreases mood/energy consumption by 2%)
        > E6: increases mood/energy gained upon deployment to 25.
    """

    # TODO: img & display name & animation
    IMAGE: str = "https://cdn.discordapp.com/attachments/1198010808672723075/1201435790845165658/nuxiom_gato.PNG"
    # ANIMATIONS: str = "guinaifengato"
    DISPLAY_NAME: str = "Guinaifen Gato"
    RARITY: int = 4
    VALUES_TO_SAVE = ABaseGato.VALUES_TO_SAVE + [
        "max_stats_buffs",
        "recent_stats_buff_ts"
    ]

    GUINAIFEN_STATS_UP_EVENT_TYPE: str = "guinaifen_stats_up"
    GUINAIFEN_STATS_LOSS_DOWN_EVENT_TYPE: str = "guinaifen_stats_loss_down"
    EVENT_DESCRIPTIONS: dict[str, str] = ABaseGato.EVENT_DESCRIPTIONS | {
        GUINAIFEN_STATS_UP_EVENT_TYPE: "increased energy and mood for all allies!",
        GUINAIFEN_STATS_LOSS_DOWN_EVENT_TYPE: "reduced energy and/or mood loss for allies! (x{count})",
    }
    GUINAIFEN_ENERGY_LOSS_REDUCTION_KEY: str = "guinaifen_energy_loss_reduction"
    GUINAIFEN_MOOD_LOSS_REDUCTION_KEY: str = "guinaifen_mood_loss_reduction"

    # Keep track of allies that received max energy and max mood buff at deploy time
    # [(gato, max_energy_buff, max_mood_buff)]
    max_stats_buffs: list[tuple["ABaseGato", int, int]] = []
    recent_stats_buff_ts: list[datetime] = []

    def deploy(self, team: list["ABaseGato"]):
        """Increase mood and energy for the team on deploy"""

        super().deploy(team)
        self.clear_max_stats_buffs()

        # Check if we've already buffed allies twice today (utc), skip if so
        now = datetime.now(timezone.utc)
        self.recent_stats_buff_ts = [
            ts for ts in self.recent_stats_buff_ts if ts.date() == now.date()]
        if len(self.recent_stats_buff_ts) >= 2:
            return
        
        # Otherwise, apply buff
        buff_amount = 20 if self.eidolon < 6 else 25
        for g in team:
            # incrase max energy and max mood as needed
            max_energy_buff = max(g.energy + buff_amount - g.max_energy, 0)
            max_mood_buff = max(g.mood + buff_amount - g.max_mood, 0)
            g.max_energy += max_energy_buff
            g.max_mood += max_mood_buff

            # record max stats increases so that we can reset them at claim time
            self.max_stats_buffs.append((g, max_energy_buff, max_mood_buff))

            # increase energy and mood
            g.add_energy(buff_amount)
            g.add_mood(buff_amount)

        # event
        self._events.append({self.GUINAIFEN_STATS_UP_EVENT_TYPE: None})

    def clear_max_stats_buffs(self):
        """Reset max mood and max energy from allies"""

        for (g, max_energy_buff, max_mood_buff) in self.max_stats_buffs:
            g.max_energy -= max_energy_buff
            g.max_mood -= max_mood_buff
            g.energy = min(g.energy, g.max_energy)
            g.mood = min(g.mood, g.max_mood)
        self.max_stats_buffs = []

    def claim(self):
        currency, objects = super().claim()
        self.clear_max_stats_buffs()
        return currency, objects

    def simulate(self, team: list["ABaseGato"], seconds: int = 1):
        """Delegates to base method"""

        reduction_amount = 0.1 + (0.02 * min(self.eidolon, 5))
        for g in team:
            if g.energy < 100 and self.GUINAIFEN_ENERGY_LOSS_REDUCTION_KEY not in g.energy_loss_reductions:
                g.energy_loss_reductions[self.GUINAIFEN_ENERGY_LOSS_REDUCTION_KEY] = reduction_amount
                self._events.append(
                    {self.GUINAIFEN_STATS_LOSS_DOWN_EVENT_TYPE: None})
            if g.mood < 100 and self.GUINAIFEN_MOOD_LOSS_REDUCTION_KEY not in g.mood_loss_reductions:
                g.mood_loss_reductions[self.GUINAIFEN_MOOD_LOSS_REDUCTION_KEY] = reduction_amount
                self._events.append(
                    {self.GUINAIFEN_STATS_LOSS_DOWN_EVENT_TYPE: None})
        super().simulate(team, seconds)
