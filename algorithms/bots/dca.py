from base import BotBase, BotEvaluationResult


class SimpleBot(BotBase):
    def __init__(self):
        super().__init__()

    def start(self) -> None:
        super().start()

    def stop(self) -> None:
        super().stop()

    def step(self) -> BotEvaluationResult:
        return super().step()


s = SimpleBot()
print(s.status)