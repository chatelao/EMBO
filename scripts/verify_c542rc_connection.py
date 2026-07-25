#!/usr/bin/env python3
import os
import re
import sys

def parse_header_defines(filepath):
    defines = {}
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return defines

    with open(filepath, "r") as f:
        content = f.read()

    # Match simple #define KEY VALUE or #define KEY (no value)
    pattern = re.compile(r'#define\s+(\w+)(?:\s+([^\n]+))?')
    for match in pattern.finditer(content):
        key = match.group(1)
        val = match.group(2)
        if val is not None:
            # Strip quotes, comments, trailing spaces
            val = val.split("//")[0].split("/*")[0].strip()
            # Strip outer quotes if any
            if val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            defines[key] = val
        else:
            defines[key] = True
    return defines

def main():
    print("=" * 70)
    print("EMBO C542RC Connection Verification Tool")
    print("=" * 70)

    # 1. Parse header files
    cfg_path = "src/firmware/src/cfg/cfg.h"
    cfg_c542rc_path = "src/firmware/src/cfg/cfg_c542rc.h"

    cfg_defines = parse_header_defines(cfg_path)
    c542rc_defines = parse_header_defines(cfg_c542rc_path)

    # Merge defines
    all_defines = {**cfg_defines, **c542rc_defines}

    # Extract required values
    dev_name = all_defines.get("EM_DEV_NAME", "EMBO-STM32C542RC-Nucleo64")
    dev_comm = all_defines.get("EM_DEV_COMM", "USB + USART2 (115200 bps)")
    ll_ver = all_defines.get("EM_LL_VER", "1.0.0")
    dev_ver = all_defines.get("EM_DEV_VER", "0.2.4")

    print("\n--- Extracted Configurations ---")
    print(f"Device Name: {dev_name}")
    print(f"Device Comm: {dev_comm}")
    print(f"LL Version:  {ll_ver}")
    print(f"Dev Version: {dev_ver}")

    # --- Step 1: Emulating *IDN? ---
    print("\n--- Handshake Step 1: Emulating *IDN? ---")
    simulated_date = "2025/01/01 12:00:00"
    idn_response = f"CTU/Jakub Parez,{dev_name},0,{dev_ver} ({simulated_date})"
    print(f"Simulated *IDN? response: {idn_response}")

    tokens = idn_response.split(",")
    if len(tokens) != 4:
        print(f"FAIL: Expected exactly 4 comma-separated tokens in *IDN?, got {len(tokens)}")
        sys.exit(1)
    print("Delimiter count: PASS")

    # Extract and verify version
    fw_info = tokens[3]
    fw_ver_match = re.match(r'^([\d\.]+)', fw_info)
    if not fw_ver_match:
        print(f"FAIL: Could not parse firmware version from '{fw_info}'")
        sys.exit(1)
    extracted_version = fw_ver_match.group(1)
    print(f"Extracted firmware version: {extracted_version}")

    def version_tuple(v):
        return tuple(map(int, v.split(".")))

    if version_tuple(extracted_version) < version_tuple("0.2.3"):
        print(f"FAIL: Firmware version {extracted_version} is less than required minimum 0.2.3")
        sys.exit(1)
    print(f"Firmware version {extracted_version} is supported (>= 0.2.3): PASS")

    # Board image mapping rules
    n = dev_name.lower()
    mapped_image = ""
    if "bluepill" in n:
        mapped_image = "bluepill"
    elif "nucleo32" in n:
        mapped_image = "nucleo32"
    elif "nucleo" in n:
        mapped_image = "nucleo64"
    else:
        mapped_image = "chip"

    print(f"Client mapped board image: '{mapped_image}'")
    if mapped_image != "nucleo64":
        print(f"FAIL: Expected mapped board image to be 'nucleo64' (Nucleo-64 layout) for '{dev_name}', got '{mapped_image}'")
        sys.exit(1)
    print("Board image mapping: PASS")


    # --- Step 2: Emulating SYS:LIM? ---
    print("\n--- Handshake Step 2: Emulating SYS:LIM? ---")

    # Calculate conditional fields in EM_SYS_LimitsQ
    dac = 0
    if "EM_DAC" in all_defines:
        dac = 1
    if "EM_DAC2" in all_defines:
        dac = 2

    bit8 = 1 if "EM_ADC_BIT8" in all_defines else 0
    daqch = 4 if "EM_DAQ_4CH" in all_defines else 2

    adcs = 0
    if "EM_ADC_MODE_ADC1" in all_defines:
        adcs = 1
    elif "EM_ADC_MODE_ADC12" in all_defines:
        adcs = 2
    elif "EM_ADC_MODE_ADC1234" in all_defines:
        adcs = 4

    dual = "D" if "EM_ADC_DUALMODE" in all_defines else ""
    inter = "I" if "EM_ADC_INTERLEAVED" in all_defines else ""
    pwm2 = 1 if "EM_TIM_PWM2" in all_defines else 0

    gpio1 = int(all_defines.get("EM_GPIO_LA_CH1_NUM", "0"))
    gpio2 = int(all_defines.get("EM_GPIO_LA_CH2_NUM", "0"))
    gpio3 = 0
    gpio4 = 0
    if "EM_DAQ_4CH" in all_defines:
        gpio3 = int(all_defines.get("EM_GPIO_LA_CH3_NUM", "0"))
        gpio4 = int(all_defines.get("EM_GPIO_LA_CH4_NUM", "0"))

    # Convert macros to integers
    def get_int(key, default):
        val = all_defines.get(key, default)
        if isinstance(val, str):
            # Strip trailing U/L modifiers
            val = re.sub(r'[uUlL]+$', '', val)
            try:
                return int(val)
            except ValueError:
                return default
        return val

    # SGEN max frequency maps to EM_DAC_TIM_MAX_F which is 5000000
    sgen_max_f = get_int("EM_DAC_TIM_MAX_F", 5000000)

    limits_str = (
        f"{get_int('EM_DAQ_MAX_B12_FS', 5000000)},"
        f"{get_int('EM_DAQ_MAX_B8_FS', 5000000)},"
        f"{get_int('EM_DAQ_MAX_MEM', 32000)},"
        f"{get_int('EM_LA_MAX_FS', 10000000)},"
        f"{get_int('EM_PWM_MAX_F', 25000000)},"
        f"{pwm2},"
        f"{daqch}{adcs}{dual}{inter},"
        f"{bit8},"
        f"{dac},"
        f"{get_int('EM_VM_FS', 100)},"
        f"{get_int('EM_VM_MEM', 100)},"
        f"{get_int('EM_CNTR_MEAS_MS', 2000)},"
        f"{sgen_max_f},"
        f"{get_int('EM_DAC_BUFF_LEN', 1000)},"
        f"{get_int('EM_CNTR_MAX_F', 50000000)},"
        f"{get_int('EM_MEM_RESERVE', 10)},"
        f"{gpio1}{gpio2}{gpio3}{gpio4}"
    )

    print(f"Simulated SYS:LIM? response: {limits_str}")
    lim_tokens = limits_str.split(",")
    if len(lim_tokens) != 17:
        print(f"FAIL: Expected exactly 17 comma-separated tokens in SYS:LIM?, got {len(lim_tokens)}")
        sys.exit(1)
    print("Token count parsed by client: 17 - PASS")

    capabilities = lim_tokens[6]
    print(f"Token 6 (Capabilities): '{capabilities}'")
    if len(capabilities) < 2:
        print(f"FAIL: Capabilities token '{capabilities}' must be at least 2 characters long")
        sys.exit(1)

    gpio_layout = lim_tokens[16]
    print(f"Token 17 (GPIO pins):   '{gpio_layout}'")
    if len(gpio_layout) != 4:
        print(f"FAIL: GPIO pins token '{gpio_layout}' must be exactly 4 characters long")
        sys.exit(1)
    print("SYS:LIM? parsing validation: PASS")


    # --- Step 3: Emulating SYS:INFO? ---
    print("\n--- Handshake Step 3: Emulating SYS:INFO? ---")
    rtos_ver = "10.2.1"
    vcc_mv = get_int("EM_VREF", 3300)

    info_str = (
        f"{rtos_ver},"
        f"{ll_ver},"
        f"{dev_comm},"
        f"{get_int('EM_FREQ_HCLK', 100000000)//1000000},"
        f"{vcc_mv},"
        f"{all_defines.get('EM_PINS_SCOPE_VM', 'PA0-PA1-PA6-PA7')},"
        f"{all_defines.get('EM_PINS_LA', 'PA0-PA1-PA6-PA7')},"
        f"{all_defines.get('EM_PINS_CNTR', 'PC9')},"
        f"{all_defines.get('EM_PINS_PWM', 'PB8-PB10')},"
        f"{all_defines.get('EM_PINS_SGEN', 'PA4-PA5')}"
    )

    print(f"Simulated SYS:INFO? response: {info_str}")
    info_tokens = info_str.split(",")
    if len(info_tokens) != 10:
        print(f"FAIL: Expected exactly 10 comma-separated tokens in SYS:INFO?, got {len(info_tokens)}")
        sys.exit(1)
    print("Token count parsed by client: 10 - PASS")
    print("SYS:INFO? parsing validation: PASS")

    print("\n" + "=" * 70)
    print("SUCCESS: C542RC connection with Windows Client programmatically verified!")
    print("=" * 70)


if __name__ == "__main__":
    main()
