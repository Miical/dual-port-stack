import mlvp
import random
from UT_dual_port_stack import *
from mlvp import Bundle, Driver, Monitor, Component, Port
from enum import Enum

class BusCMD(Enum):
    PUSH = 0
    POP = 1
    PUSH_OKAY = 2
    POP_OKAY = 3

class BusBundle(Bundle):
    signals = ['valid', 'ready', 'data', 'cmd']

rm_stack = []

class MasterEnv(Component):
    def __init__(self, bundle: BusBundle):
        super().__init__()

        async def driver_method(bundle: BusBundle, item):
            cmd, data = item
            if cmd == "push":
                bundle.valid.value = True
                bundle.data.value = data
                bundle.cmd.value = BusCMD.PUSH.value
            else:
                bundle.valid.value = True
                bundle.cmd.value = BusCMD.POP.value
            await bundle.step()
            await mlvp.AllValid(bundle.valid, bundle.ready)
            bundle.valid.value = False

            if cmd == "push":
                rm_stack.append(data)

        self.driver = Driver(bundle, driver_method=driver_method)
        self.bundle = bundle

    async def main(self):
        while True:
            await self.driver.port.put(("push", random.randint(0, 127)))
            await self.bundle.step(random.randint(1, 10))
            await self.driver.port.put(("pop", None))

class SlaveEnv(Component):
    def __init__(self, bundle: BusBundle):
        super().__init__()

        async def driver_method(bundle, item):
            bundle.ready.value = True
            await bundle.step()
            await mlvp.AllValid(bundle.valid, bundle.ready)

        self.driver = Driver(bundle, driver_method)

        async def monitor_method(bundle):
            dict = bundle.as_dict()
            if dict['cmd'] == BusCMD.POP_OKAY.value:
                rm_data = rm_stack.pop()
                # print("actual:", dict['data'], "std:", rm_data)
                # print(dict)
                assert dict['data'] == rm_data
                print(f"Pass: {rm_data} == {dict['data']}")
            await bundle.step()
            return dict

        self.monitor = Monitor(bundle, lambda bundle: bundle.valid.value and bundle.ready.value, monitor_method)
        self.bundle = bundle

    async def main(self):
        while True:
            await self.driver.port.put(None)
            ret = await self.monitor.port.get()
            assert ret['cmd'] == BusCMD.PUSH_OKAY.value or ret['cmd'] == BusCMD.POP_OKAY.value
            await self.bundle.step(random.randint(1, 10))


async def test_stack(dut):
    mlvp.create_task(mlvp.start_clock(dut))
    port0_req = BusBundle.from_prefix("in0_").bind(dut)
    port0_resp = BusBundle.from_prefix("out0_").bind(dut)
    port1_req = BusBundle.from_prefix("in1_").bind(dut)
    port1_resp = BusBundle.from_prefix("out1_").bind(dut)

    port0_master_env = MasterEnv(port0_req)
    port0_slave_env = SlaveEnv(port0_resp)
    port1_master_env = MasterEnv(port1_req)
    port1_slave_env = SlaveEnv(port1_resp)

    await mlvp.ClockCycles(dut, 1000)


# mlvp.setup_logging(log_level=mlvp.logger.INFO)
dut = DUTdual_port_stack()
dut.init_clock("clk")
mlvp.run(test_stack(dut))
dut.finalize()

