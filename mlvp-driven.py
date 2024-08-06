import mlvp
import random
from mlvp import *
from enum import Enum
from UT_dual_port_stack import *

class StackPortBundle(Bundle):
    signals = ["in_valid", "in_ready", "in_cmd", "in_data", "out_valid", "out_ready", "out_cmd", "out_data"]

class BusCMD(Enum):
    PUSH = 0
    POP = 1
    PUSH_OKAY = 2
    POP_OKAY = 3

class StackAgent(Agent):
    def __init__(self, port):
        super().__init__(monitor_step=port.step)
        self.port = port

    @driver_method(match_func=True, need_compare=True, sche_order="dut_first")
    async def opt(self, is_push, data=0):
        await ClockCycles(self.port, random.randint(0, 5))
        self.port.in_valid.value = 1
        self.port.in_cmd.value = BusCMD.PUSH.value if is_push else BusCMD.POP.value
        self.port.in_data.value = data

        await Value(self.port.in_ready, 1)
        self.port.in_valid.value = 0

        self.port.out_ready.value = 1
        await Value(self.port.out_valid, 1)
        self.port.out_ready.value = 0

        return self.port.out_data.value if not is_push else 0

class StackModel(Model):
    def __init__(self):
        super().__init__()
        self.stack = []

    def opt(self, is_push, data):
        if is_push:
            self.stack.append(data)
        return 0 if is_push else self.stack.pop()

async def test_stack(dut):
    mlvp.start_clock(dut)
    port0 = StackPortBundle.from_regex("(.*)0(.*)").bind(dut)
    port1 = StackPortBundle.from_regex("(.*)1(.*)").bind(dut)

    model = StackModel()
    agent1 = StackAgent(port0).attach(model)
    agent2 = StackAgent(port1).attach(model)

    async with Executor() as exec:
        for is_push in [True, False]:
            for _ in range(50):
                exec(agent1.opt(is_push, random.randint(0, 2**8-1)))
                exec(agent2.opt(is_push, random.randint(0, 2**8-1)))

if __name__ == '__main__':
    dut = DUTdual_port_stack()
    dut.InitClock("clk")
    # mlvp.setup_logging(mlvp.logger.INFO)
    mlvp.run(test_stack(dut))
    dut.Finish()
