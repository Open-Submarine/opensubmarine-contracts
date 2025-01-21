from algopy import UInt64, ARC4Contract

class ReceiverInterface(ARC4Contract):
    """
    Interface for all abimethods of receiver contract.
    """

    def __init__(self) -> None:  # pragma: no cover
        self.messenger_id = UInt64()


class Receiver(ReceiverInterface):
    def __init__(self) -> None:  # pragma: no cover
        super().__init__()
