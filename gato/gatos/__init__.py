import importlib
import os
import sys
DIR = os.path.dirname(__file__)
sys.path.append(DIR)

# Gatos

import ABaseGato
importlib.reload(ABaseGato)

import SwedeGato
import ExampleGato, LNYGato
import SeeleGato
import QingqueGato
import HertaGato
import FuxuanGato
import ClaraGato
import BladeGato
import GuinaifenGato
import KafkaGato
import HimekoGato
import ArgentiGato
import NormalGato

importlib.reload(SwedeGato)
importlib.reload(LNYGato)
importlib.reload(ExampleGato)
importlib.reload(SeeleGato)
importlib.reload(QingqueGato)
importlib.reload(HertaGato)
importlib.reload(FuxuanGato)
importlib.reload(ClaraGato)
importlib.reload(BladeGato)
importlib.reload(GuinaifenGato)
importlib.reload(KafkaGato)
importlib.reload(HimekoGato)
importlib.reload(ArgentiGato)
importlib.reload(NormalGato)

Gato = ABaseGato.ABaseGato
SwedeGato = SwedeGato.SwedeGato
LNYGato = LNYGato.LNYGato
ExampleGato = ExampleGato.ExampleGato
SeeleGato = SeeleGato.SeeleGato
QingqueGato = QingqueGato.QingqueGato
HertaGato = HertaGato.HertaGato
FuxuanGato = FuxuanGato.FuxuanGato
ClaraGato = ClaraGato.ClaraGato
BladeGato = BladeGato.BladeGato
GuinaifenGato = GuinaifenGato.GuinaifenGato
KafkaGato = KafkaGato.KafkaGato
HimekoGato = HimekoGato.HimekoGato
ArgentiGato = ArgentiGato.ArgentiGato
NormalGato = NormalGato.NormalGato

GATOS = [
    SwedeGato,
    LNYGato,
    SeeleGato,
    QingqueGato,
    HertaGato,
    FuxuanGato,
    ClaraGato,
    BladeGato,
    GuinaifenGato,
    KafkaGato,
    HimekoGato,
    ArgentiGato,
    NormalGato
]

## Items

import ABaseItem
importlib.reload(ABaseItem)
Item = ABaseItem.ABaseItem

# Consumables

import AConsumable
importlib.reload(AConsumable)

import RedPacketConsumable, TrashConsumable, MedkitConsumable, \
    AvocadoToastConsumable, CatTreatsConsumable, SwedishFishConsumable, \
    DefibrilatorConsumable, FeatherTeaserConsumable, SalmonConsumable

importlib.reload(RedPacketConsumable)
importlib.reload(TrashConsumable)
importlib.reload(MedkitConsumable)
importlib.reload(AvocadoToastConsumable)
importlib.reload(CatTreatsConsumable)
importlib.reload(SwedishFishConsumable)
importlib.reload(DefibrilatorConsumable)
importlib.reload(FeatherTeaserConsumable)
importlib.reload(SalmonConsumable)

Consumable = AConsumable.AConsumable
RedPacketConsumable = RedPacketConsumable.RedPacketConsumable
TrashConsumable = TrashConsumable.TrashConsumable
MedkitConsumable = MedkitConsumable.MedkitConsumable
AvocadoToastConsumable = AvocadoToastConsumable.AvocadoToastConsumable
CatTreatsConsumable = CatTreatsConsumable.CatTreatsConsumable
SwedishFishConsumable = SwedishFishConsumable.SwedishFishConsumable
DefibrilatorConsumable = DefibrilatorConsumable.DefibrilatorConsumable
FeatherTeaserConsumable = FeatherTeaserConsumable.FeatherTeaserConsumable
SalmonConsumable = SalmonConsumable.SalmonConsumable

CONSUMABLES = [
    RedPacketConsumable,
    TrashConsumable,
    MedkitConsumable,
    AvocadoToastConsumable,
    CatTreatsConsumable,
    SwedishFishConsumable,
    DefibrilatorConsumable,
    FeatherTeaserConsumable,
    SalmonConsumable
]

# Equipments

import AEquipment
importlib.reload(AEquipment)

import EfficiencyFoodEq, FakeMouseEq

importlib.reload(EfficiencyFoodEq)
importlib.reload(FakeMouseEq)

EfficiencyFoodEq = EfficiencyFoodEq.EfficiencyFoodEq
FakeMouseEq = FakeMouseEq.FakeMouseEq

EQUIPMENTS = [FakeMouseEq]

# Team equipments

import MedicalInsuranceTEq

importlib.reload(MedicalInsuranceTEq)

MedicalInsuranceTEq = MedicalInsuranceTEq.MedicalInsuranceTEq

TEAM_EQUIPMENTS = [MedicalInsuranceTEq]
