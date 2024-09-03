import pytest
from mlvp import *
from mlvp.triggers import *
from mlvp.agent import *
from mlvp.model import *
import random
from enum import Enum
from UT_dual_port_stack import *

class StackPortBundle(Bundle):
	in_cmd, in_data, in_ready, in_valid, out_cmd, out_data, out_ready, out_valid = Signals(8)

class BusCMD(Enum):
    PUSH = 0
    POP = 1
    PUSH_OKAY = 2
    POP_OKAY = 3

class StackAgent(Agent):
    def __init__(self, bundle):
        super().__init__(bundle.step)
        self.bundle = bundle

    async def opt(self, is_push, data=0):
        self.bundle.in_valid.value = 1
        self.bundle.in_cmd.value = BusCMD.PUSH.value if is_push else BusCMD.POP.value
        self.bundle.in_data.value = data
        await Value(self.bundle.in_ready, 1)
        self.bundle.in_valid.value = 0

        self.bundle.out_ready.value = 1
        await Value(self.bundle.out_valid, 1)
        self.bundle.out_ready.value = 0

        return self.bundle.out_data.value

    @driver_method()
    async def push(self, data):
        await self.opt(True, data)

    @driver_method()
    async def pop(self):
        return await self.opt(False)

class DualPortStackEnv(Env):
    def __init__(self, port1, port2):
        super().__init__()

        self.port1_agent = StackAgent(port1)
        self.port2_agent = StackAgent(port2)

class StackModel(Model):
    def __init__(self):
        super().__init__()
        self.stack = []

    async def opt(self, opt_name, args):
        if opt_name == "push":
            self.stack.append(args['data'])
        elif opt_name == "pop":
            return self.stack.pop()

    @agent_hook()
    async def port1_agent(self, opt_name, args):
        return await self.opt(opt_name, args)

    @agent_hook()
    async def port2_agent(self, opt_name, args):
        return await self.opt(opt_name, args)

@pytest.mark.mlvp_async
async def test_stack(dut):
    start_clock(dut)
    port0 = StackPortBundle.from_regex("(.*)0(.*)").bind(dut)
    port1 = StackPortBundle.from_regex("(.*)1(.*)").bind(dut)
    env = DualPortStackEnv(port0, port1).attach(StackModel())

    async with Executor() as exec:
        for _ in range(50):
            exec(env.port1_agent.push(random.randint(0, 2**8-1)), sche_order="dut_first", sche_group="1")
            exec(env.port2_agent.push(random.randint(0, 2**8-1)), sche_order="dut_first", sche_group="2")

        for _ in range(50):
            exec(env.port1_agent.pop(), sche_order="dut_first", sche_group="1")
            exec(env.port2_agent.pop(), sche_order="dut_first", sche_group="2")

@pytest.fixture()
def dut(mlvp_pre_request: PreRequest):
    return mlvp_pre_request.create_dut(DUTdual_port_stack, "clk")
