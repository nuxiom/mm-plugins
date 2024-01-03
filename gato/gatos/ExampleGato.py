from ABaseGato import ABaseGato

class ExampleGato(ABaseGato):
    """
        > A gato with 10% more base efficiency.
        > Gets a +20% (+{eidolon} × 2% from Eidolon) efficiency boost for 20 minutes every hour.
    """

    base_efficiency: float = 1.1     # Override initial values for stats
