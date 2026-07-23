# Gap Analysis: Compiling EMBO for STM32G431 (Nucleo-G431KB)

This document provides a comprehensive Gap Analysis of the STM32G431 implementation within the EMBO project, documenting its current status, configured peripherals, and remaining gaps to achieve full stability and parity with production targets.

---

## 1. Hardware & Core Overview
* **MCU:** STM32G431KBT6 (ARM Cortex-M4 with FPU, up to 170 MHz core clock)
* **Flash Memory:** 128 KB
* **SRAM:** 32 KB
* **Target Board:** Nucleo-32 G431KB (onboard ST-LINK/V3)

---

## 2. Current Implementation Status
Unlike the STM32F446RE, the **STM32G431KB** has a board directory and a dedicated configuration file:
* **Board Directory:** `src/firmware/board/STM32G431KB/` (Contains `.project`, `.cproject`, `EMBO_G431KB.ioc`, and startup/linker files)
* **Configuration Header:** `src/firmware/src/cfg/cfg_g431kb.h` (Active and included in `cfg.h` via `STM32G431xx`)
* **FreeRTOS Port:** Uses the Cortex-M4F GCC port (`M4F/port.c`), fully supported.

---

## 3. Identified Gaps to Stable Release
Although code is present, G431 support is classified as **experimental/work-in-progress** ("More yet to come...") in the project's documentation. The following technical gaps must be resolved for a stable production release:

### Gap 3.1: Disabled Signal Generator Max Frequency (`EM_SGEN_MAX_F`)
In the active configuration file `cfg_g431kb.h`, the signal generator maximum output frequency is hardcoded to `0`:
```c
#define EM_SGEN_MAX_F          0          // SGEN max output freq.
```
* **Impact:** The Signal Generator (DAC-based) is practically disabled or unsupported on G431 inside the EMBO software.
* **Resolution:** Change `#define EM_SGEN_MAX_F 0` to `#define EM_SGEN_MAX_F EM_DAC_TIM_MAX_F` after verifying that DAC DMA transfers with `TIM6`/`TIM7` are fully functional.

### Gap 3.2: Missing Dual & Interleaved ADC Support (TODOs)
In `cfg_g431kb.h`, high-speed sampling modes are commented out:
```c
//#define EM_ADC_INTERLEAVED                                   // interleaved mode available  - TODO
//#define EM_ADC_DUALMODE                                      // dual mode available         - TODO
```
* **Impact:** The G431 has dual ADCs capable of interleaved sampling, which would allow doubling the maximum sampling frequency for a single channel. Currently, this performance feature is missing.
* **Resolution:** Implement and test Interleaved and Dual Mode DMA configurations using the STM32G4 Low-Level drivers, then uncomment these macros.

### Gap 3.3: DMA Request Multiplexer (DMAMUX) Complexity
The G4 series features a DMAMUX to route peripheral triggers to DMA channels. In `src/firmware/board/STM32G431KB/`, the DMAMUX configuration must be verified for compatibility with the circular DMA buffers used by EMBO's Oscilloscope and Logic Analyzer.
* **Impact:** Misconfigured synchronization or trigger inputs in DMAMUX can cause sample dropped interrupts or DMA transfers to halt under high CPU load.
* **Resolution:** Ensure correct DMA request routing and priority assignment via `EMBO_G431KB.ioc` and STM32CubeMX generation.

---

## 4. Current Configuration Reference (`cfg_g431kb.h`)
The existing layout maps EMBO functions to the Nucleo-32 board pins as follows:
* **SCOPE / VM (ADC):** `A0` (PA0), `A1` (PA1), `A6` (PA6), `A7` (PA7)
* **Logic Analyzer (GPIO):** `A0`, `A1`, `A6`, `A7`
* **PWM Generator:** `A15` (PA15), `B6` (PB6)
* **Counter:** `A8` (PA8)
* **Signal Generator (DAC):** `A4` (PA4), `A5` (PA5)
* **Virtual COM Port:** `PA2` / `PA3` (USART2)

---

## 5. Build & Compilation Verification
To compile G431KB:
1. Import `src/firmware/board/STM32G431KB/` into STM32CubeIDE as an existing project.
2. Ensure `arm-none-eabi-gcc` compiler options target the Cortex-M4 with hardware floating point:
   `-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16`
3. The linked root source code directory (`src/firmware/src/`) will be automatically compiled.
