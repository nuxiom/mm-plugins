import importlib
import os
import sys
DIR = os.path.dirname(__file__)
sys.path.append(DIR)

import ABaseGato
importlib.reload(ABaseGato)

import ExampleGato, StrongGato

importlib.reload(ExampleGato)
importlib.reload(StrongGato)

Gato = ABaseGato.ABaseGato
ExampleGato = ExampleGato.ExampleGato
StrongGato = StrongGato.NormalGato
