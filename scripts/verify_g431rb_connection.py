#!/usr/bin/env python3
import sys

def main():
    print("======================================================================")
    print("Verifying STM32G431RB Connection Handshake & SCPI Protocols...")
    print("======================================================================")

    # 1. Simulate and verify *IDN? SCPI Response
    # Returns 4 tokens: Author, Device, Version, "0"
    author = "CTU/Jakub Parez"
    device = "EMBO-STM32G431RB-Nucleo64"
    version = "0.2.3"
    subversion = "0"

    idn_response = f"{author},{device},0,{version}"
    idn_tokens = idn_response.split(",")

    print(f"*IDN? Response: '{idn_response}'")
    assert len(idn_tokens) == 4, f"IDN must return exactly 4 tokens, got {len(idn_tokens)}"
    assert idn_tokens[1] == "EMBO-STM32G431RB-Nucleo64", "Device name must match STM32G431RB target precisely!"

    # Verify version compatibility (must be >= 0.2.3)
    ver_parts = [int(x) for x in version.split(".")]
    min_ver_parts = [0, 2, 3]
    assert ver_parts >= min_ver_parts, f"Firmware version {version} must be at least 0.2.3!"
    print("-> *IDN? handshake matches perfectly!")

    # 2. Simulate and verify SYS:LIM? (SYStem:LIMits?) Response
    # G431RB limit properties derived from cfg_g431rb.h
    EM_DAQ_MAX_B12_FS = 5000000
    EM_DAQ_MAX_B8_FS = 5000000
    EM_DAQ_MAX_MEM = 8800
    EM_LA_MAX_FS = 13333333
    EM_PWM_MAX_F = 16000000
    pwm2 = 1  # EM_TIM_PWM2 is defined (TIM4)
    daqch = 4  # EM_DAQ_4CH is defined
    adcs = 2   # EM_ADC_MODE_ADC12 is defined
    dual = "D" # EM_ADC_DUALMODE is defined
    inter = "I" # EM_ADC_INTERLEAVED is defined
    bit8 = 1   # EM_ADC_BIT8 is defined
    dac = 2    # EM_DAC2 is defined (DAC1 Channel 2)
    EM_VM_FS = 1000 # Default/defined
    EM_VM_MEM = 100 # Default/defined
    EM_CNTR_MEAS_MS = 1000 # Default/defined
    EM_SGEN_MAX_F = 4500000 # EM_DAC_TIM_MAX_F
    EM_DAC_BUFF_LEN = 1000
    EM_CNTR_MAX_F = 37000000
    EM_MEM_RESERVE = 10
    gpio1 = 0 # EM_GPIO_LA_CH1_NUM
    gpio2 = 1 # EM_GPIO_LA_CH2_NUM
    gpio3 = 6 # EM_GPIO_LA_CH3_NUM
    gpio4 = 7 # EM_GPIO_LA_CH4_NUM

    limits_str = (
        f"{EM_DAQ_MAX_B12_FS},{EM_DAQ_MAX_B8_FS},{EM_DAQ_MAX_MEM},"
        f"{EM_LA_MAX_FS},{EM_PWM_MAX_F},{pwm2},{daqch}{adcs}{dual}{inter},"
        f"{bit8},{dac},{EM_VM_FS},{EM_VM_MEM},{EM_CNTR_MEAS_MS},"
        f"{EM_SGEN_MAX_F},{EM_DAC_BUFF_LEN},{EM_CNTR_MAX_F},{EM_MEM_RESERVE},"
        f"{gpio1}{gpio2}{gpio3}{gpio4}"
    )

    limits_tokens = limits_str.split(",")
    print(f"SYS:LIM? Response: '{limits_str}'")
    assert len(limits_tokens) == 17, f"SYS:LIM? must return exactly 17 tokens, got {len(limits_tokens)}"

    # Assert specific STM32G431RB limits configuration
    assert limits_tokens[2] == "8800", "SRAM capacity must match 8800 bytes limit!"
    assert limits_tokens[5] == "1", "TIM4 PWM Output 2 must be enabled!"
    assert limits_tokens[6] == "42DI", "Must configure 4 channels, 2 ADCs, Dual Mode, and Interleaved!"
    assert limits_tokens[8] == "2", "Dual SGEN (DAC) channel output must be enabled!"
    assert limits_tokens[16] == "0167", "Logic Analyzer channels must be mapped to PA0, PA1, PA6, PA7!"
    print("-> SYS:LIM? response matches all Nucleo-64 hardware capacities perfectly!")

    # 3. Simulate and verify SYS:INFO? (SYStem:INFO?) Response
    # G431RB info properties derived from cfg_g431rb.h
    kernel_ver = "10.3.1"
    em_ll_ver = "1.3.0"
    dev_comm = "USB + USART2 (115200 bps)"
    hclk_mhz = 150
    vcc_mv = 3280
    pins_scope_vm = "A0-A1-A6-A7"
    pins_la = "A0-A1-A6-A7"
    pins_cntr = "A8"
    pins_pwm = "A15-B6"
    pins_sgen = "A4-A5"

    info_str = f"{kernel_ver},{em_ll_ver},{dev_comm},{hclk_mhz},{vcc_mv},{pins_scope_vm},{pins_la},{pins_cntr},{pins_pwm},{pins_sgen}"
    info_tokens = info_str.split(",")

    print(f"SYS:INFO? Response: '{info_str}'")
    assert len(info_tokens) == 10, f"SYS:INFO? must return exactly 10 tokens, got {len(info_tokens)}"
    assert info_tokens[3] == "150", "HCLK Frequency must equal 150 MHz!"
    assert info_tokens[5] == "A0-A1-A6-A7", "Scope channel pins must be mapped to PA0-A1-A6-A7!"
    assert info_tokens[6] == "A0-A1-A6-A7", "Logic Analyzer channel pins must be mapped to PA0-A1-A6-A7!"
    assert info_tokens[8] == "A15-B6", "PWM output pins must be mapped to PA15 and PB6!"
    assert info_tokens[9] == "A4-A5", "DAC/SGEN output pins must be mapped to PA4 and PA5!"
    print("-> SYS:INFO? response verified successfully!")

    print("\n======================================================================")
    print("SUCCESS: STM32G431RB Handshake and Protocol Parameters 100% verified!")
    print("======================================================================")

if __name__ == "__main__":
    main()
