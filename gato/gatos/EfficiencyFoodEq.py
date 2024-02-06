from AEquipment import AEquipment
from ABaseItem import ItemType

class EfficiencyFoodEq(AEquipment):
    """Boosts efficiency by 10% for 1 hour. Automatically equiped on use of an efficiency food Consumable."""

    ITEM_TYPE: ItemType = ItemType.EQUIPMENT
    DISPLAY_NAME = "Effiency Food Buff"

    FOOD_BUFF_KEY = "food_eff_buff"

    buff_duration: int

    def __init__(self):
        super().__init__()
        self.buff_duration = 0

    def simulate(self, gato, seconds: int = 1):
        super().simulate(gato, seconds)

        if self.FOOD_BUFF_KEY not in gato.efficiency_boosts:
            gato.efficiency_boosts[self.FOOD_BUFF_KEY] = 0.1
            self.buff_duration = 3600
        else:
            if self.buff_duration > 0:
                self.buff_duration -= seconds
            else:
                gato.efficiency_boosts.pop(self.FOOD_BUFF_KEY)
                self.used_up = True
