from algorithms.bots.base import BotBase, BotEvaluationResult


class GridBot(BotBase):
    def __init__(self):
        super().__init__()

    def start(self) -> None:
        super().start()

    def stop(self) -> None:
        super().stop()

    def step(self, new_price) -> BotEvaluationResult:
        return super().step(new_price)
