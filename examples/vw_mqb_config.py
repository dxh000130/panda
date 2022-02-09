#!/usr/bin/env python3

import argparse
import struct
from panda import Panda
from panda.python.uds import UdsClient, MessageTimeoutError, NegativeResponseError, SESSION_TYPE, DATA_IDENTIFIER_TYPE

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--debug", action="store_true", help="enable ISO-TP/UDS stack debugging output")
  parser.add_argument("action", default="show", choices={"show", "enable", "disable"}, help="show or modify current EPS HCA config")
  args = parser.parse_args()

  panda = Panda()
  panda.set_safety_mode(Panda.SAFETY_ELM327)
  bus = 1 if panda.has_obd else 0
  uds_client = UdsClient(panda, 0x712, 0x77c, bus, timeout=0.2, debug=args.debug)

  try:
    uds_client.diagnostic_session_control(SESSION_TYPE.EXTENDED_DIAGNOSTIC)
  except MessageTimeoutError:
    print("Timeout opening session with EPS")
    quit()

  odx_ver = ""
  try:
    hw_pn = uds_client.read_data_by_identifier(DATA_IDENTIFIER_TYPE.VEHICLE_MANUFACTURER_ECU_HARDWARE_NUMBER).decode("utf-8")
    sw_pn = uds_client.read_data_by_identifier(DATA_IDENTIFIER_TYPE.VEHICLE_MANUFACTURER_SPARE_PART_NUMBER).decode("utf-8")
    sw_ver = uds_client.read_data_by_identifier(DATA_IDENTIFIER_TYPE.VEHICLE_MANUFACTURER_ECU_SOFTWARE_VERSION_NUMBER).decode("utf-8")
    component = uds_client.read_data_by_identifier(DATA_IDENTIFIER_TYPE.SYSTEM_NAME_OR_ENGINE_TYPE).decode("utf-8")
    odx_file = uds_client.read_data_by_identifier(DATA_IDENTIFIER_TYPE.ODX_FILE).decode("utf-8")
    odx_ver = uds_client.read_data_by_identifier(0xF1A2).decode("utf-8")
    current_coding = uds_client.read_data_by_identifier(0x0600)
    coding_text = current_coding.hex()

    print("\nDiagnostic data from EPS controller\n")
    print(f"   Part No HW:   {hw_pn}")
    print(f"   Part No SW:   {sw_pn}")
    print(f"   SW version:   {sw_ver}")
    print(f"   Component:    {component}")
    print(f"   Coding:       {coding_text}")
    print(f"   ASAM Dataset: {odx_file} version {odx_ver}")
  except NegativeResponseError:
    print("Error fetching data from EPS")
    quit()
  except MessageTimeoutError:
    print("Timeout fetching data from EPS")
    quit()

  if args.action in ["enable", "disable"]:
    print("")
    if odx_file != "EV_SteerAssisMQB\x00":
      # EV_SteerAssisMQB covers the majority of MQB racks (EPS_MQB_ZFLS)
      # APA racks (MQB_PP_APA) have a different coding layout, which should
      # be easy to support once we identify the specific config bit
      print("Configuration changes not yet supported on this EPS!")
      quit()
    current_coding_array = struct.unpack("!4B", current_coding)
    if(args.action == "enable"):
      new_byte_0 = current_coding_array[0] | 1<<4
    else:
      new_byte_0 = current_coding_array[0] & ~(1<<4)
    new_coding = new_byte_0.to_bytes(1, "little") + current_coding[1:]
    print(f"\n   New coding:   {new_coding}")
    #try:
    seed = uds_client.security_access(0x3)
    key = struct.unpack("!I", seed)[0] + 28183  # yeah, it's like that
    uds_client.security_access(0x4, struct.pack("!I", key))
    uds_client.write_data_by_identifier(0x0600, new_coding)
    print("EPS configuration successfully updated!")
    #except NegativeResponseError:
    #  print("Error changing config")
    #except MessageTimeoutError:
    #  print("Timeout changing config")
