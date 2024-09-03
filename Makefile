WORK_DIR = $(shell pwd)/src
PYTHON 	= python3
PICKER 	= picker
NAME	= dual_port_stack 

run:
	pytest --mlvp-report -v .

dut:
	$(PICKER) export --autobuild=true dual_port_stack.v -w dual_port_stack.fst --sname dual_port_stack --tdir picker_out_dual_port_stack --lang python -e -c --sim verilator
	cp -r picker_out_dual_port_stack/UT_dual_port_stack .

clean:
	rm -rf UT_dual_port_stack picker_out_dual_port_stack reports
