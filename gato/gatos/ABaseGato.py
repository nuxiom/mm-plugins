from abc import ABC, abstractmethod
from random import random


def require_alive(function):
    """Decorator that only executes a function if the gato has not fainted. **Warning:** Don't add that to functions that shouldn't return `None`."""
    def new_function(gato: "ABaseGato", *args, **kwargs):
        if not gato._fainted:
            return function(gato, *args, **kwargs)

    return new_function



class ABaseGato(ABC):
    """**Abstract class** to implement for every gato.

    Attributes starting with a `_` should not be modified manually.
    Attributes in CAPS are constants."""

    IMAGE: str = "https://cdn.discordapp.com/emojis/1173895764087414855.webp"
    """Sprite of the gato. **OVERRIDE IT!**"""

    ANIMATIONS: str = "mooncake"
    """A reference to a key in `animations.json`. **OVERRIDE IT!**"""

    DISPLAY_NAME: str = "Base Gato"
    """Display name of this gato class. **OVERRIDE IT!**"""

    EVENT_DESCRIPTIONS = {
        "fainted": "fainted.",
        "bitten": "is angry and bites you (x{count}). You lose **{amount}** {currency} in total"
    }
    """Description for the gato's events. *Can be overriden or completed with custom events.*
    For example, `SkellyGato` has a custom event called `"resurrect"` with a custom description."""

    BASE_EARN_RATE: float = 0.25
    """Number of currency per second the gato earns. **DON'T OVERRIDE IT**, rather override :py:attr:`base_efficiency`."""

    BITE_CHANCE: float = 1/100
    """Base chance to get bitten."""

    VALUES_TO_SAVE = [
        "name",
        "mood",
        "health",
        "hunger",
        "energy",
        "health",
        "efficiency_boost",
        "eidolon",
        "friendship",
        "deployed_today"
    ]
    """Attributes that will be saved when exporting the gato to JSON. *Can be overriden or completed with custom attributes.*"""


    max_mood: float = 100.0
    """Maximum value for the :py:attr:`mood` stat. *You can override that.*"""

    max_hunger: float = 100.0
    """Maximum value for the :py:attr:`hunger` stat. *You can override that.*"""

    max_energy: float = 100.0
    """Maximum value for the :py:attr:`energy` stat. *You can override that.*"""

    max_health: float = 100.0
    """Maximum value for the :py:attr:`health` stat. *You can override that.*"""


    mood: float
    """Current value for the :py:attr:`mood` stat. Chances to get bitten when :py:attr:`mood` is low. Updated in real time by the :py:meth:`lose_stats_over_time` method when deployed."""

    hunger: float
    """Current value for the :py:attr:`hunger` stat. Loses health when :py:attr:`hunger` is low. Updated in real time by the :py:meth:`lose_stats_over_time` method when deployed."""

    energy: float
    """Current value for the :py:attr:`energy` stat. Reduces efficiency when :py:attr:`energy` is low. Updated in real time by the :py:meth:`lose_stats_over_time` method when deployed."""

    health: float
    """Current value for the :py:attr:`health` stat. Faints when :py:attr:`health` reaches **0**. Updated in real time by the :py:meth:`lose_stats_over_time` method when deployed."""


    efficiency: float
    """Current value for efficiency stat. Updated in real time by the :py:meth:`compute_currency` method when deployed."""

    base_efficiency: float = 1.0
    """Base efficiency stat. *You can override that.*"""

    luck: float = 1.0
    """Multiplier for the chance to find treasures. *You can override that.*"""

    efficiency_boost: float = 0.0
    """Boost of the efficiency stat. Can be affected by the gato or other gatos."""

    friendship: float = 1.0
    """Friendship stat, starts at 1, max 10."""

    claimed_today: int = 0
    """Number of times the rewards of this gato have been claimed today."""


    _fainted: bool = False
    """Becomes :keyword:`True` if the gato's health is 0. Updated by :py:meth:`add_health`"""

    _events: list[dict] = []
    """List of events. Cleared everytime the rewards are claimed. An event is a dict like `{"event_name": "optional value (can be any type)"}`"""

    _time_deployed: int = 0
    """Number of seconds since the gato has been deployed. Updated in real-time by :py:meth:`simulate`"""


    name: str
    """Name of the gato. Choosen by the owner."""

    eidolon: int
    """Eidolon level of the gato. Starts at 0, max 6."""


    def __init__(self, **kwargs):
        """Constructor."""
        self.mood = self.max_mood
        self.hunger = self.max_hunger
        self.energy = self.max_energy
        self.health = self.max_health
        self.efficiency = self.base_efficiency

        self.name = self.__class__.__name__
        self.eidolon = 0

        for k, v in kwargs.items():
            setattr(self, k, v)

        if self.health <= 0.0:
            self._fainted = True

    def to_json(self):
        """Exports a gato to JSON.

        :return: A dict containing the gato's class name, and all the values specified in :py:attr:`VALUES_TO_SAVE`.
        :rtype: dict
        """
        return {
            "type": self.__class__.__name__,
            "values": dict((val, getattr(self, val)) for val in self.VALUES_TO_SAVE)
        }

    @classmethod
    def from_json(cls, json: dict):
        """Class method to import a gato from JSON.

        :classmethod:
        :param json: A dict exported by :py:meth:`to_json`.
        :type json: dict
        :return: The imported gato
        :rtype: :py:class:`ABaseGato`
        """
        return cls(**json["values"])


    def deploy(self):
        """Called when a gato is deployed."""

        self._time_deployed = 0
        self.efficiency_boost = 0.0

        if self.health > 0:
            self._fainted = False

    def claim(self):
        """Called everytime the owner claims the rewards of this gato."""
        self._events = []

        if self.friendship < 10 and self.claimed_today < 5:
            self.friendship += 0.1

        self.claimed_today += 1


    def lose_stats_over_time(self, seconds):
        """Computes stat loss over time. Called by :py:meth:`simulate`. *Can be overriden.*"""
        self.add_hunger(-0.01 * seconds)
        self.add_energy(-0.02 * seconds)

        if self._time_deployed >= 30*60:
            self.add_mood(-0.01 * seconds)

        if self.hunger < 10:
            self.add_health(-0.02 * seconds)

        if self.mood < 10:
            if random() < self.BITE_CHANCE / self.friendship:
                self._events.append({"bitten": None})


    def compute_currency(self, seconds):
        """Computes efficiency and currency gain over time. Called by :py:meth:`simulate`. *Can be overriden.*"""
        self.efficiency = self.base_efficiency + self.efficiency_boost
        if self.energy < 10:
            self.efficiency -= 0.2
        elif self.energy < 20:
            self.efficiency -= 0.1

        return seconds * self.BASE_EARN_RATE * self.efficiency


    def random_object(self, seconds):
        """Computes random reward findings. Called by :py:meth:`simulate`. *Can be overriden.*"""
        objects = []
        if self._time_deployed % 60 == 0 and self.efficiency >= 1:
            if random() < self.luck / 100:
                objects.append("Shiny thing")

        return objects


    @abstractmethod
    def simulate(self, team: list["ABaseGato"], seconds: int = 1):
        """Runs a simulation of the gato over a certain amount of time.
        Abstract method, **needs to be overriden**. Overriding method should still call superclass method (see :py:class:`ExampleGato`).
        Returns 0-values when gato is fainted.

        :param team: The team the gato is deployed in. Can be used for team-based buffs.
        :type team: list[:py:class:`ABaseGato`]
        :param seconds: Simulation duration in seconds, defaults to 1.
        :type seconds: int, optional
        :return: The amount of currency and the list of objects gathered by the gato.
        :rtype: tuple[float, list[str]]
        """

        if not self._fainted:
            self._time_deployed += seconds

            self.lose_stats_over_time(seconds)

            currency = self.compute_currency(seconds)

            objects = self.random_object(seconds)

            return currency, objects
        else:
            return 0.0, []


    @require_alive
    def add_health(self, amount: float):
        """Affect a gato's health within its limits.
        Amount can be negative.
        Use this rather than modifying :py:attr:`health` directly.
        Doesn't work when gato is fainted.
        Also sets :py:attr:`_fainted` when :py:attr:`health` is 0.
        *Can be overriden.*

        :param amount: Amount of health to add.
        :type amount: float
        """

        self.health += amount

        if self.health > self.max_health:
            self.health = self.max_health
        elif self.health <= 0.0:
            self.health = 0.0
            self._fainted = True
            self._events.append({"fainted": None})


    @require_alive
    def add_mood(self, amount: float):
        """Affect a gato's mood within its limits.
        Amount can be negative.
        Use this rather than modifying :py:attr:`mood` directly.
        Doesn't work when gato is fainted.
        *Can be overriden.*

        :param amount: Amount of mood to add.
        :type amount: float
        """

        self.mood += amount

        if self.mood > self.max_mood:
            self.mood = self.max_mood
        elif self.mood <= 0.0:
            self.mood = 0.0


    @require_alive
    def add_hunger(self, amount: float):
        """Affect a gato's hunger within its limits.
        Amount can be negative.
        Use this rather than modifying :py:attr:`hunger` directly.
        Doesn't work when gato is fainted.
        *Can be overriden.*

        :param amount: Amount of hunger to add.
        :type amount: float
        """

        self.hunger += amount

        if self.hunger > self.max_hunger:
            self.hunger = self.max_hunger
        elif self.hunger <= 0.0:
            self.hunger = 0.0


    @require_alive
    def add_energy(self, amount: float):
        """Affect a gato's energy within its limits.
        Amount can be negative.
        Use this rather than modifying :py:attr:`energy` directly.
        Doesn't work when gato is fainted.
        *Can be overriden.*

        :param amount: Amount of energy to add.
        :type amount: float
        """

        self.energy += amount

        if self.energy > self.max_energy:
            self.energy = self.max_energy
        elif self.energy <= 0.0:
            self.energy = 0.0
