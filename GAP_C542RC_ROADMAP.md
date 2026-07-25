# Roadmap: Compiling EMBO for STM32C542RC (Nucleo-C542RC)

This document outlines the phased roadmap to implement full support for the conceptual **STM32C542RC** microcontroller on the Nucleo-C542RC board under the EMBO (EMBedded Oscilloscope) project, following the specifications derived in `GAP_C542RC_DESIGN.md`.

---

## Progress Overview

| Phase | Description | Status |
| :--- | :--- | :---: |
| Phase 1 | Project Environment & LL Drivers Import | ✅ |
| Phase 2 | Board-Specific Configuration Header Integration | ✅ |
| Phase 3 | Shared Code & System Integration | ✅ |
| Phase 4 | Verification & Continuous Integration Updates | ✅ |

---

## Goals
* ✅ Core support for STM32C542RC microcontroller under EMBO.
* ✅ Conflict-free pin mapping for Oscilloscope (DAQ), Logic Analyzer (LA), Signal Generator (DAC), and on-board User LED.
* ✅ Setup of DMAMUX routes for clean request-to-channel mappings on DMA1.
* ✅ Successful firmware compilation using `arm-none-eabi-gcc` targeting ARM Cortex-M33 architecture.

---

## Phases

### Phase 1: Project Environment & LL Drivers Import
This phase focuses on creating the target board directory structure and importing required LL (Low-Level) driver files.

- [x] **Task 1.1: Create Board Directory Structure**
  - [x] Subtask 1.1.1: Create directory `src/firmware/board/STM32C542RC/` patterned after existing STM32 board directories (e.g., `STM32G431KB`).
  - [x] Subtask 1.1.2: Add `.project` and `.cproject` files configured for STM32C542RCTx and ARM GCC.
  - [x] Subtask 1.1.3: Include target linker script `STM32C542RCTX_FLASH.ld` and startup file `startup_stm32c542xx.s`.
- [x] **Task 1.2: Import Low-Level (LL) Drivers**
  - [x] Subtask 1.2.1: Copy STM32CubeC5 LL driver headers to `src/firmware/board/STM32C542RC/Drivers/STM32C5xx_HAL_Driver/Inc/`.
  - [x] Subtask 1.2.2: Copy STM32CubeC5 LL driver source files to `src/firmware/board/STM32C542RC/Drivers/STM32C5xx_HAL_Driver/Src/`.

### Phase 2: Board-Specific Configuration Header Integration
This phase defines the conflict-free pinout mapping, timers, DMAs, and stack size allocations.

- [x] **Task 2.1: Create Dedicated Configuration Header**
  - [x] Subtask 2.1.1: Create file `src/firmware/src/cfg/cfg_c542rc.h` with the exact configurations detailed in `GAP_C542RC_DESIGN.md` Section 5.1.
  - [x] Subtask 2.1.2: Map `EM_TIM_DAQ` to `TIM1` to ensure high-performance triggering via `TIM1_TRGO` on the fast 100 MHz APB2 clock domain.
  - [x] Subtask 2.1.3: Establish the conflict-free pin layout for DAQ/LA (PA0, PA1, PA6, PA7), DAC (PA4, PA5), and User LED (PB13).
  - [x] Subtask 2.1.4: Map the DMA channels for all active modules on DMA1 utilizing DMAMUX requests.

### Phase 3: Shared Code & System Integration
This phase integrates the board configuration into the shared EMBO firmware base.

- [x] **Task 3.1: Update Configuration Header Dispatcher**
  - [x] Subtask 3.1.1: Modify `src/firmware/src/cfg/cfg.h` to include a preprocessor dispatch block for `STM32C542xx` / `EM_C542RC`.
  - [x] Subtask 3.1.2: Link the new `cfg_c542rc.h` when compiled under the target MCU define.
- [x] **Task 3.2: Map ADC Sampling Constants**
  - [x] Subtask 3.2.1: Update `src/firmware/src/cfg/cfg.c` with the specific ADC sampling time configurations for `STM32C542xx`.

### Phase 4: Verification & Continuous Integration Updates
This final phase verifies compilation success and configures automatic build rules.

- [x] **Task 4.1: Compilation Script Configuration**
  - [x] Subtask 4.1.1: Update `scripts/compile_firmware.py` to recognise and properly compile the `STM32C542RC` target using correct target CPU flags (`-mcpu=cortex-m33 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16`).
- [x] **Task 4.2: CI/CD Pipeline Integration**
  - [x] Subtask 4.2.1: Update `.github/workflows/compile.yml` to automatically compile the new STM32C542RC target firmware during pipeline execution.
