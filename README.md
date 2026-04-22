# Transient-load-test

# 1. Initialization of Equipments
  Keithley 2230 - GPIB TO USB
  Keithley 2380 - GPIB TO USB
  Keysight DSOX6004A - USB
  Keithley DMM6500 - USB

  To find exact address using rm.list_resources()
	After getting address replace in place of ‘USB0::0x….::0x....::.....' respectively.
	idn = inst.query('*IDN?')     # Identification
	inst.write('*RST')             # Reset to defaults
	inst.write('*CLS')             # Clear status registers
	inst.query('*OPC?')            # Wait for operation complete
	errors = inst.query('SYST:ERR?')  # Check error queue

# 3. Configure Programmable DC Power Supply (Keithley 2230-30-1)
	Turn on remote mode (so that SCPI commands work)
	vm.write('SYST:REM')
	vm.write('APPL CH1, 12V, 3A’) #change as per requirement
	vm.write('OUTP ON')
	print('Power on... waiting for settling')
	# need a little delay right here
	time.sleep(3)
		
	print('Taking measurements')
	voltCH1 = float(vm.query('MEAS:VOLT? CH1'))
	currentCH1 = float(vm.query('MEAS:CURR? CH1'))
	powerCH1 = voltCH1 * currentCH1
	print(f'V={voltCH1:.1f}V I={currentCH1:.2f}A P={powerCH1:.2f}W')

  //command for turn off 'OUTP OFF' or 'OUTP 0'
	vm.write('OUTP OFF')
	print('Turned off power’)

4. Configure Electronic Load (Keithley 2380)
	# Turn on remote mode
	load.write(‘SYST:REM’)
	# Turn on current mode
  load.write("FUNC:MODE CURR") 
	# Turn on Transient mode
	load.write("CURRent:TRANsient:MODE CONTinuous”)
	# Steady state current
	load.write("CURR:TRAN:ALEV 5.0”)
	# Transient peak current
  load.write("CURR:TRAN:BLEV 1.0")
  
5. Configure Oscilloscope
	scope.write(":AUToscale")
  time.sleep(2)
  scope.write(":TRIGger:MODE EDGE")
  scope.write(":TRIGger:EDGE:SOURce CHAN1")
	# Trigger slightly below nominal voltage 	
	scope.write(f":TRIGger:EDGE:LEVel {nominal_volt - (nominal_volt * 0.05)}")
	# Trigger on voltage drop
	scope.write(":TRIGger:EDGE:SLOPe NEGative")

6. Capture Digital Multimeter reading voltage
	dmm.query("MEAS:VOLT:DC?")

7. Acquiring wave form Oscilloscope
	data = scope.query_binary_values(':DISPlay:DATA? PNG,SCReen,1,NORMal’, 				datatype='B', header_fmt='ieee', container=bytes)

  file_id = open(“rail 3.6.png”, 'wb')
  file_id.write(data)
  file_id.close()


Reference:
https://www.pyvisa.com/docs/scpi-commands-python
https://iotexpert.com/pyvisa-first-use/
https://download.tek.com/manual/2230G-900-01A_Jun_2018_User.pdf
https://download.tek.com/manual/2380-120-60-900-01_A_Nov_2015.pdf
https://yout.be/TLUTCDbt52I?si=2d2F0aNQ9KqSg2R0
https://assets.testequity.com/te1/Documents/pdf/keithley/2220-2230-ds.pdf
https://www.keysight.com/us/en/assets/9018-07124/programming-guides/9018-07124.pdf?success=true
https://keyoscacquire.readthedocs.io/en/v3.0.2/
https://download.tek.com/manual/DMM6500-901-01_A_April_2018_Ref_DMM6500-901-01A.pdf
https://www.mouser.com/datasheet/3/720/1/2380_DataSheet.pdf?srsltid=AfmBOoolBcKqD-GtJFpYjMJG9WK9UBBXrrjSmH2b_a2lgYeDdFnnjnbU
