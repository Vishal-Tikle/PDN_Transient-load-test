import pyvisa as pv
import time
from datetime import datetime
import csv
import numpy as np
import matplotlib.pyplot as plt

# --- Test Parameters ---
V_IN = 5.0  # Input Voltage
I_IN = 3.0  # Input Current

PASS_THRESHOLD_V = 0.05 # 5% allowable deviation

def test_transient(nominal_volt, maxCurrent):
    rm = pv.ResourceManager()
    
    try:
        # 1. Initialization of Equipments
        # To find exact address using rm.list_resources()
        vm = rm.open_resource('USB0::0x....::0x....::.....')
        load = rm.open_resource('USB0::0x....::0x....::.....')
        scope = rm.open_resource('USB0::0x....::0x....::.....')
        dmm = rm.open_resource('USB0::0x....::0x....::.....') 

        for inst in [vm, load, scope, dmm]:
            inst.write("*RST")
            inst.write('*CLS')
            inst.query('*OPC?')
            print(f"Initialized: {inst.query('*IDN?').strip()}")

        # 2. Configure Programmable DC Power Supply (Keithley 2230-30-1)
        # Turn on remote mode (so that SCPI commands work)
        vm.write('SYST:REM')
        vm.write(f'APPL CH1, {V_IN}, {I_IN}') 

        print('Taking measurements')
        voltIN = float(vm.query('MEASure:VOLTage? CH1'))
        currentIN = float(vm.query('MEASure:CURRent? CH1'))
        powerIN = voltIN * currentIN
        print(f'Vin={voltIN:.2f}V Iin={currentIN:.2f}A Pin={powerIN:.2f}W')

        # 3. Configure Electronic Load (Keithley 2380) - Transient Mode
        load.write("SYST:REM") 
        load.write("FUNC:MODE CURR") 
        load.write("CURRent:TRANsient:MODE CONTinuous")
        load.write(f"CURR:TRAN:ALEV {maxCurrent}")
        load.write("CURR:TRAN:BLEV 0.5")
        load.write("CURR:TRAN:RISE 0.1") 
        load.write("CURR:TRAN:FALL 0.1")

        # 4. Configure Oscilloscope (Keysight DSOX6004A)
        scope.write(":AUToscale")
        time.sleep(2)

        scope.write(":TRIGger:MODE EDGE")
        scope.write(":TRIGger:EDGE:SOURce CHAN1")
        scope.write(f":TRIGger:EDGE:LEVel {nominal_volt - (nominal_volt * 0.05)}")
        scope.write(":TRIGger:EDGE:SLOPe NEGative")

        # 5. Execute Test & Capture
        print("Starting load transient...")
        vm.write('OUTP ON')
        print('Power on... waiting for settling')
        time.sleep(3)

        load.write("OUTP ON")
        load.write("TRAN ON") # Begin transient cycles
        time.sleep(2)

        # Capture DMM Reading
        v_out = float(dmm.query("MEAS:VOLT:DC?"))
        
        # Capture Waveform from Scope
        scope.write(":DIGitize CHANnel1")
        scope.write(':WAVeform:POINts:MODE MAXimum')
        raw_data = scope.query_binary_values(":WAVeform:DATA?", datatype='s')
        
        # 6. Data Processing & Logging
        v_min = np.min(raw_data) # Simplified: would require scaling factors
        v_max = np.max(raw_data)
        pass_status = "PASS" if abs(v_out - nominal_volt) < (nominal_volt * PASS_THRESHOLD_V) else "FAIL"

        # Save to CSV
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        filename = f"transient_report_{nominal_volt}V_{timestamp}.csv"
        
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp","Parameter", "Value", "Status"])
            writer.writerow([timestamp, "Steady State V", v_out, pass_status])
            writer.writerow([timestamp, "Min Transient V", v_min, "N/A"])
            writer.writerow([timestamp, "Max Transient V", v_max, "N/A"])

        # 7. Screenshot Capture
        data = scope.query_binary_values(':DISPlay:DATA? PNG,SCReen,1,NORMal', datatype='B', header_fmt='ieee', container=bytes)
        file_id = open(f"rail{nominal_volt}V.png", 'wb')
        file_id.write(data)
        file_id.close()

        print(f"Test Complete. Report saved to {filename}")

    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        # Safety Shutdown
        print('Turned off power')
        vm.write('OUTP OFF')
        load.write("OUTP OFF")
        rm.close()

if __name__ == "__main__":
    test_transient(3.6, 2.5);
    test_transient(1.8, 3.0);
    test_transient(3.3, 3.0);
    test_transient(2.5, 1.5);
