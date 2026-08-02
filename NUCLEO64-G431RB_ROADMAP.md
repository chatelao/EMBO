# NUCLEO64-G431RB Roadmap

This document maps out the phases, goals, and step-by-step progress for porting, re-implementing, and verifying the EMBO (EMBedded Oscilloscope) firmware from the Nucleo-32 (STM32G431KB) to the Nucleo-64 (STM32G431RB) form factor, based on the detailed technical specifications in `NUCLEO64-G431RB_DESIGN.md`.

---

## Progress Overview

| Phase | Description | Status | Target/Resolution |
|---|---|---|---|
| **Phase 1** | Project Structuring & Directory Preparation | ✅ Completed | `src/firmware/board/STM32G431RB/` |
| **Phase 2** | Board Configuration & Pin Remapping | ✅ Completed | `src/firmware/src/cfg/cfg_g431rb.h` |
| **Phase 3** | High-Performance DAQ, DMA & DMAMUX Mapping | ✅ Completed | `src/firmware/src/app/` |
| **Phase 4** | HMI Controls, PC Client Handshake & Validation | 🚧 In Progress | `scripts/` & `README.md` |

---

## Goals

* **Objective 1:** ✅ Completed | Establish a clean STM32G431RB (Nucleo-64) project directory with full LL driver support.
* **Objective 2:** ✅ Completed | Remap the user LED (`EM_LED`) to PB13 to prevent hardware conflicts on PA5 (DAC1_OUT2).
* **Objective 3:** ✅ Completed | Integrate physical blue button (B1) on PC13 for headless mode switching and local calibration.
* **Objective 4:** ✅ Completed | Achieve error-free compilation of the STM32G431RB firmware target using `compile_firmware.py`.
* **Objective 5:** ✅ Completed | Confirm perfect compatibility with the EMBO Qt client handshake (`*IDN?`, `SYS:LIM?`, `SYS:INFO?`).

---

## Phases

### Phase 1: Project Structuring & Directory Preparation ✅

Establish the physical folder structure and build configuration for the STM32G431RB target.

- [x] **Task 1.1: Create Project Folder Structure** ✅
  - Create the board directory `src/firmware/board/STM32G431RB/` patterned after the existing `STM32G431KB` target.
  - Set up standard subdirectories: `Core/`, `Drivers/`, and configuration files.
- [x] **Task 1.2: Import Low-Level (LL) Drivers** ✅
  - Ensure all required low-level drivers (`stm32g4xx_ll_*.h/c`) are correctly linked or imported into `Drivers/STM32G4xx_HAL_Driver/`.
- [x] **Task 1.3: Configure Project Build Files** ✅
  - Create and configure `.project`, `.cproject`, and `.mxproject` files targeting the LQFP64 STM32G431RBT6 MCU.
  - Add compile-time preprocessor definitions such as `STM32G431xx` and `EM_G431RB` to control feature gating.
- [x] **Task 1.4: Import Linker and Startup Files** ✅
  - Copy and adjust the linker script (`STM32G431RBTX_FLASH.ld`) with correct capacities (128 KB Flash, 32 KB SRAM).
  - Add the correct startup assembly file (`startup_stm32g431xx.s`).

---

### Phase 2: Board Configuration & Pin Remapping ✅

Implement board-specific pin configurations and resolve on-board physical conflicts.

- [x] **Task 2.1: Implement Board Configuration Header (`cfg_g431rb.h`)** ✅
  - Create `src/firmware/src/cfg/cfg_g431rb.h` with the exact configurations detailed in `NUCLEO64-G431RB_DESIGN.md`.
  - Configure device identifiers: `EM_DEV_NAME` to `"EMBO-STM32G431RB-Nucleo64"`.
- [x] **Task 2.2: Resolve User LED Pin Conflict** ✅
  - Map `EM_LED_PORT` to `GPIOB` and `EM_LED_PIN` to `13` (`PB13`).
  - This avoids severe waveform signal integrity degradation and visual noise on `PA5` (`DAC1_OUT2`).
- [x] **Task 2.3: Integrate Physical User Button (B1)** ✅
  - Configure the HMI button mapping in `cfg_g431rb.h`: `EM_BTN_PORT` as `GPIOC`, `EM_BTN_PIN` as `13`.
  - Set up `EXTI15_10_IRQHandler` to trigger mode/calibration actions upon button click.
- [x] **Task 2.4: Central Configuration Dispatching** ✅
  - Integrate `cfg_g431rb.h` into the main `cfg.h` configuration dispatcher under the `EM_G431RB` compile symbol.
  - Define correct ADC sampling times in `cfg.c` for G431RB.

---

### Phase 3: High-Performance DAQ, DMA & DMAMUX Mapping ✅

Establish conflict-free DMA channels routing via the DMAMUX router and ensure high-speed ADC interleaved acquisition.

- [x] **Task 3.1: Configure DMAMUX and DMA Layout** ✅
  - Program DMAMUX requests according to the map in `NUCLEO64-G431RB_DESIGN.md`:
    - DMA1 Ch1: ADC1 Regular (`LL_DMAMUX_REQ_ADC1`)
    - DMA1 Ch2: Logic Analyzer GPIOR IDR (`LL_DMAMUX_REQ_TIM15_CH1`)
    - DMA1 Ch3: ADC2 Regular (`LL_DMAMUX_REQ_ADC2`)
    - DMA1 Ch4: DAC1 Channel 1 (`LL_DMAMUX_REQ_DAC1_CH1`)
    - DMA1 Ch5: DAC1 Channel 2 (`LL_DMAMUX_REQ_DAC1_CH2`)
    - DMA1 Ch6: Frequency Counter Direct (`LL_DMAMUX_REQ_TIM1_CH1`)
    - DMA2 Ch1: Frequency Counter Indirect (`LL_DMAMUX_REQ_TIM1_CH2`)
- [x] **Task 3.2: Verify Dual/Interleaved ADC Common Data Register (CDR) Addressing** ✅
  - Ensure `EM_ADC_ADDR(x)` correctly targets the Common Regular Data Register (`CDR`) when dual-ADC multimode is active.
- [x] **Task 3.3: Map Scope and LA Pins** ✅
  - Align all 4 channels to `GPIOA` (PA0, PA1, PA6, PA7) to preserve concurrent, single-cycle DMA IDR reads for the Logic Analyzer.

---

### Phase 4: HMI Controls, PC Client Handshake & Validation 🚧

Verify full software stack functionality, test serial/VCP handshakes, and finalize release documentation.

- [x] **Task 4.1: Compile-Time Verification** ✅
  - Integrate the `STM32G431RB` target into `scripts/compile_firmware.py`.
  - Perform compilation and verify that both binary (`.bin`) and hex (`.hex`) outputs are generated without any errors or warnings.
- [x] **Task 4.2: Emulated Handshake and Protocol Verification** ✅
  - Test the connection handshake response using emulated queries:
    - `*IDN?` must return 4 comma-separated tokens matching firmware version `0.2.3` and target device.
    - `SYS:LIM?` must return exactly 17 comma-separated configuration limits.
    - `SYS:INFO?` must return exactly 10 comma-separated status values.
- [ ] **Task 4.3: Document Target Integration** ⏳
  - Update `README.md` and `README_cz.md` to list the STM32G431RB (Nucleo-64) as an officially supported stable hardware target.
