# STM32G431RB Protocol & Handshake Verification

This document records the programmatic verification results of the **STM32G431RB (Nucleo-64)** EMBO firmware handshake protocol structures, as extracted from board configurations and evaluated against client expectations.

---

## 1. Handshake Emulation Results

### *IDN? Query (Identification Handshake)
* **Response String:** `"CTU,EMBO-STM32G431RB-Nucleo64,0,0.2.4`
* **Token Count:** `4` (Expected: 4)
* **Status:** ✅ VERIFIED & COMPATIBLE (Device Name matched: `EMBO-STM32G431RB-Nucleo64`, Version: `0.2.4` >= `0.2.3`)

### SYS:LIM? Query (Limits Verification)
* **Response String:** `5000000,5000000,8800,13333333,16000000,1,21,0,2,100,100,2000,4500000,1000,37000000,10,0100`
* **Token Count:** `17` (Expected: 17)
* **Status:** ✅ VERIFIED & COMPATIBLE (SRAM and clock capacities aligned with Qt client matrix)

### SYS:INFO? Query (Uptime & Diagnostic Status)
* **Response String:** `10.3.1,1.3.0,USB + USART2 (115200 bps),150,3300,A0-A1-A6-A7,A0-A1-A6-A7,A8,A15-B6,A4-A5`
* **Token Count:** `10` (Expected: 10)
* **Status:** ✅ VERIFIED & COMPATIBLE (GPIO Alternate Functions and HCLK freq correctly reported)

---

## 2. Configuration Parameters Matrix

| Parameter Name | Extracted Value | Description |
|---|---|---|
| **EM_DEV_NAME** | `EMBO-STM32G431RB-Nucleo64` | Host-visible device name identifier |
| **EM_DEV_COMM** | `USB + USART2 (115200 bps)` | Hardware communication medium |
| **EM_LL_VER** | `1.3.0` | Low-Level ST Driver layer version |
| **EM_FREQ_HCLK** | `150000000 Hz` | Core system clock frequency |
| **EM_DAQ_MAX_MEM** | `8800 bytes` | Total circular capture buffer memory capacity |
| **EM_LA_MAX_FS** | `13333333 Hz` | Maximum Logic Analyzer sampling frequency |
| **EM_PWM_MAX_F** | `16000000 Hz` | Maximum PWM output generator frequency |
| **EM_SGEN_MAX_F** | `4500000 Hz` | Maximum analog signal generator DAC frequency |

*Generated dynamically by `scripts/verify_g431rb_connection.py`.*
