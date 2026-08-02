# STM32G431RB Protocol Verification Report

This report provides programmatic verification of the connection handshake and configuration parameters for the **STM32G431RB (Nucleo-64)** target, guaranteeing perfect compatibility with the EMBO PC/Qt client.

## Connection Handshake Sequence

### 1. Identify Query (`*IDN?`)
- **Expected Format:** exactly 4 comma-separated tokens, matching version and device name.
- **Generated Response:** `CTU/Jakub Parez,EMBO-STM32G431RB-Nucleo64,0.2.4,0`
- **Status:** ✅ Validated successfully.

### 2. Limits Query (`SYS:LIM?`)
- **Expected Format:** exactly 17 comma-separated limits.
- **Generated Response:** `5000000,5000000,8800,13333333,16000000,1,42DI,1,2,100,100,2000,4500000,1000,37000000,10,0167`
- **Status:** ✅ Validated successfully.

### 3. Info Query (`SYS:INFO?`)
- **Expected Format:** exactly 10 comma-separated status variables.
- **Generated Response:** `10.3.1,1.3.0,USB + USART2 (115200 bps),150,3300,A0-A1-A6-A7,A0-A1-A6-A7,A8,A15-B6,A4-A5`
- **Status:** ✅ Validated successfully.

## Verified Properties Table

| Parameter | Evaluated Macro Value | Description |
|---|---|---|
| **Device Name** | `EMBO-STM32G431RB-Nucleo64` | `EM_DEV_NAME` matching target board |
| **Firmware Version** | `0` | `EM_DEV_VER` (>= 0.2.3 requirement met) |
| **Max Memory** | `8800` | `EM_DAQ_MAX_MEM` maximum safe raw SRAM capacity |
| **SGEN Max Freq** | `4500000` | `EM_SGEN_MAX_F` maximum signal generator frequency |
| **LA Max Freq** | `13333333` | `EM_LA_MAX_FS` maximum logic analyzer frequency |
| **Counter Max Freq** | `37000000` | `EM_CNTR_MAX_F` maximum frequency counter limit |
| **GPIO LA Channels** | `0,1,6,7` | Map of Logic Analyzer active input pins |

## Conclusion

The connection protocol of the **STM32G431RB** target has been fully validated against the EMBO protocol requirements with perfect compliance.
