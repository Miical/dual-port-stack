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

class StackEnv(Env):
    def __init__(self, port0, port1):
        super().__init__(monitor_step=port0.step)
        self.port0 = port0
        self.port1 = port1

    async def exec_once(self, port, is_push, data=0):
        port.in_valid.value = 1
        port.in_cmd.value = BusCMD.PUSH.value if is_push else BusCMD.POP.value
        port.in_data.value = data

        await port.step()
        await Value(port.in_ready, 1)
        port.in_valid.value = 0

        port.out_ready.value = 1
        await port.step()
        await Value(port.out_valid, 1)
        port.out_ready.value = 0

        return port.out_data.value

    @driver_method(imme_ret=False, match_func=True)
    async def push_port0(self, data):
        await self.exec_once(self.port0, is_push=True, data=data)

    @driver_method(imme_ret=False, match_func=True)
    async def push_port1(self, data):
        await self.exec_once(self.port1, is_push=True, data=data)

    @driver_method(imme_ret=False, match_func=True, result_compare=True)
    async def pop_port0(self):
        return await self.exec_once(self.port0, is_push=False)

    @driver_method(imme_ret=False, match_func=True, result_compare=True)
    async def pop_port1(self):
        return await self.exec_once(self.port1, is_push=False)

class StackModel(Model):
    def __init__(self):
        super().__init__()
        self.stack = []

    def push_port0(self, data):
        self.stack.append(data)

    def push_port1(self, data):
        self.stack.append(data)

    def pop_port0(self):
        return self.stack.pop()

    def pop_port1(self):
        return self.stack.pop()

async def test_stack(dut):
    mlvp.create_task(mlvp.start_clock(dut))

    port0 = StackPortBundle.from_regex("(.*)0(.*)").bind(dut)
    port1 = StackPortBundle.from_regex("(.*)1(.*)").bind(dut)
    env = StackEnv(port0, port1)
    env.attach(StackModel())

    for _ in range(10):
        await env.push_port0(random.randint(0, 2**8-1))
        await env.push_port1(random.randint(0, 2**8-1))

    for _ in range(10):
        await env.pop_port0()
        await env.pop_port1()

if __name__ == '__main__':
    dut = DUTdual_port_stack()
    dut.init_clock("clk")
    mlvp.setup_logging(mlvp.logger.INFO)
    mlvp.run(test_stack(dut))
    dut.finalize()
