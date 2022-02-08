#!/usr/bin/env python3

import argparse
from panda import Panda
from panda.python.uds import UdsClient, MessageTimeoutError, NegativeResponseError, SESSION_TYPE, DATA_IDENTIFIER_TYPE

class EPS_CONTROLLER:
  tx_addr = 0x712
  rx_addr = 0x77c
  config_access = 28183
  dataset = {
    "EV_SteerAssisMQB": {"byte": 0, "bit": 4},  # Coding data lengths differ 1 to 4 bytes, but HCA is in same place
  }

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--debug", action="store_true", help="enable ISO-TP/UDS stack debugging output")
  parser.add_argument("--show", action="store_true", help="show current EPS configuration")
  args = parser.parse_args()

  panda = Panda()
  panda.set_safety_mode(Panda.SAFETY_ELM327)
  bus = 1 if panda.has_obd else 0
  uds_client = UdsClient(panda, 0x712, 0x77c, bus, timeout=0.2, debug=args.debug)
  try:
    uds_client.diagnostic_session_control(SESSION_TYPE.DEFAULT)
  except MessageTimeoutError:
    print("Timeout opening session with EPS")
    quit()

  try:
    hw_pn = uds_client.read_data_by_identifier(DATA_IDENTIFIER_TYPE.VEHICLE_MANUFACTURER_ECU_HARDWARE_NUMBER).decode("utf-8")
    sw_pn = uds_client.read_data_by_identifier(DATA_IDENTIFIER_TYPE.VEHICLE_MANUFACTURER_SPARE_PART_NUMBER).decode("utf-8")
    sw_ver = uds_client.read_data_by_identifier(DATA_IDENTIFIER_TYPE.VEHICLE_MANUFACTURER_ECU_SOFTWARE_VERSION_NUMBER).decode("utf-8")
    component = uds_client.read_data_by_identifier(DATA_IDENTIFIER_TYPE.SYSTEM_NAME_OR_ENGINE_TYPE).decode("utf-8")
    odx_file = uds_client.read_data_by_identifier(DATA_IDENTIFIER_TYPE.ODX_FILE).decode("utf-8")
    odx_ver = uds_client.read_data_by_identifier(0xF1A2).decode("utf-8")
    coding = uds_client.read_data_by_identifier(0x0600).hex()

    print("\nDiagnostic data from EPS controller\n")
    print(f"   Part No HW:   {hw_pn}")
    print(f"   Part No SW:   {sw_pn}")
    print(f"   SW version:   {sw_ver}")
    print(f"   Component:    {component}")
    print(f"   Coding:       {coding}")
    print(f"   ASAM Dataset: {odx_file} version {odx_ver}")
  except NegativeResponseError:
    print("Error fetching data from EPS")
    quit()
  except MessageTimeoutError:
    print("Timeout fetching data from EPS")
    quit()

