import asyncio
from UT_dual_port_stack import *

async def my_coro(dut, name):
    for i in range(10):
        print(f"{name}: {i}")
        await dut.astep(1)

async def test_dut(dut):
    asyncio.create_task(my_coro(dut, "coroutine 1"))
    asyncio.create_task(my_coro(dut, "coroutine 2"))
    await asyncio.create_task(dut.runstep(10))

dut = DUTdual_port_stack()
dut.init_clock("clk")
asyncio.run(test_dut(dut))
dut.finalize()
