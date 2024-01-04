import importlib
import os
import sys
DIR = os.path.dirname(__file__)
sys.path.append(DIR)

import ABaseGato
importlib.reload(ABaseGato)

import ExampleGato, NormalGato

importlib.reload(ExampleGato)
importlib.reload(NormalGato)

Gato = ABaseGato.ABaseGato
ExampleGato = ExampleGato.ExampleGato
NormalGato = NormalGato.NormalGato
