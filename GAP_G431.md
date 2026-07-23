# Gap Analysis: Compiling EMBO for STM32G431 (Nucleo-G431KB)

This document provides a comprehensive, production-ready Gap Analysis and integration blueprint for achieving a stable release of the EMBO (EMBedded Oscilloscope) firmware on the **STM32G431KBT6** microcontroller (Nucleo-32 G431KB board).

---

## 1. Hardware & Core Overview
* **MCU:** STM32G431KBT6 (ARM Cortex-M4 with FPU, up to 170 MHz core clock)
* **Flash Memory:** 128 KB
* **SRAM:** 32 KB
* **Target Board:** Nucleo-32 G431KB (onboard ST-LINK/V3)
* **Internal Clocks Configuration:**
  * **Core Clock (HCLK):** 150 MHz
  * **ADC Clock (ADCCLK):** 60 MHz (derived asynchronously from PLL)
  * **APB1 Clock (PCLK1):** 150 MHz
  * **APB2 Clock (PCLK2):** 150 MHz

---

## 2. Identified Gaps & Technical Resolutions

To transition G431 support from experimental to a stable release, the following technical gaps must be resolved with the concrete, non-open designs outlined below:

### Gap 2.1: Disabled Signal Generator Max Frequency (`EM_SGEN_MAX_F`)
* **Problem:** In `cfg_g431kb.h`, `EM_SGEN_MAX_F` is hardcoded to `0`, practically disabling the DAC-based Signal Generator.
* **Resolution:** Set `EM_SGEN_MAX_F` to `EM_DAC_TIM_MAX_F` (`4500000` / 4.5 MHz). Since the APB1 clock is configured to 150 MHz, TIM6/TIM7 can easily trigger the DAC DMA transfers up to this frequency safely.

### Gap 2.2: Missing Dual & Interleaved ADC Support (Undeclared `chans` Compiler Error)
* **Problem:** If `#define EM_ADC_INTERLEAVED` and `#define EM_ADC_DUALMODE` are uncommented in `cfg_g431kb.h`, compilation fails in `daq.c`. Specifically, inside `daq_mem_set()`, the variable `chans` is used under preprocessor blocks but is never defined or declared in that scope.
* **Resolution:** Define `int chans = self->set.ch1_en + self->set.ch2_en + self->set.ch3_en + self->set.ch4_en;` at the beginning of `daq_mem_set()` to resolve the compiler error and allow correct memory allocation.

### Gap 2.3: Multimode ADC DMA Register Mapping
* **Problem:** In regular single-ADC mode, DMA transfers read from the individual ADC Data Register (`DR`). In dual/interleaved multimode, however, both master and slave conversion results are packed into a single 32-bit register on the master ADC called the **Common Regular Data Register (CDR)**. Reading a 32-bit word from `&ADC1->DR` is hardware-invalid or yields incomplete/corrupted results.
* **Resolution:** Redefine the `EM_ADC_ADDR(x)` macro to conditionally fetch the Common Regular Data Register (using `LL_ADC_DMA_REG_REGULAR_DATA_MULTI`) when dual/interleaved modes are active on the master ADC.

### Gap 2.4: DMA Request Multiplexer (DMAMUX) & Channel Routing Cleanliness
* **Problem:** Misconfigured DMA requests or overlapping channels can cause collisions or sample drops.
* **Resolution:** Verify and commit to a conflict-free, non-overlapping DMA channel allocation across DMA1 and DMA2. All G431 peripheral DMA requests must be routed via DMAMUX without any channel overlap:
  1. `EM_DMA_CH_ADC1`  -> `DMA1 Channel 1` (Triggered by `LL_DMAMUX_REQ_ADC1`)
  2. `EM_DMA_CH_LA`    -> `DMA1 Channel 2` (Triggered by `LL_DMAMUX_REQ_TIM15_CH1` for GPIO capture)
  3. `EM_DMA_CH_ADC2`  -> `DMA1 Channel 3` (Triggered by `LL_DMAMUX_REQ_ADC2`)
  4. `EM_DMA_CH_SGEN`  -> `DMA1 Channel 4` (Triggered by `LL_DMAMUX_REQ_DAC1_CH1` for DAC1 Ch1)
  5. `EM_DMA_CH_SGEN2` -> `DMA1 Channel 5` (Triggered by `LL_DMAMUX_REQ_DAC1_CH2` for DAC1 Ch2)
  6. `EM_DMA_CH_CNTR`  -> `DMA1 Channel 6` (Triggered by `LL_DMAMUX_REQ_TIM1_CH1` for Counter direct capture)
  7. `EM_DMA_CH_CNTR2` -> `DMA2 Channel 1` (Triggered by `LL_DMAMUX_REQ_TIM1_CH2` for Counter indirect capture)

---

## 3. Conflict-Free Pin Layout Reference
The G431KB configuration maps EMBO functionalities to Nucleo-32 pinouts seamlessly:
* **DAQ (Scope) / LA (Logic Analyzer) Pins:** Shared on `GPIOA` to enable parallel DMA IDR register reads for the Logic Analyzer:
  * `DAQ CH1` / `LA CH1` ........... `PA0` (ADC1_IN1)
  * `DAQ CH2` / `LA CH2` ........... `PA1` (ADC1_IN2)
  * `DAQ CH3` / `LA CH3` ........... `PA6` (ADC2_IN3)
  * `DAQ CH4` / `LA CH4` ........... `PA7` (ADC2_IN4)
* **PWM Generator:**
  * `PWM CH1` ...................... `PA15` (TIM2_CH1)
  * `PWM CH2` ...................... `PB6` (TIM4_CH1)
* **Frequency Counter:**
  * `CNTR` ......................... `PA8` (TIM1_CH1)
* **Signal Generator (DAC):**
  * `DAC CH1` ...................... `PA4` (DAC1_OUT1)
  * `DAC CH2` ...................... `PA5` (DAC1_OUT2)
* **Communications & Debug:**
  * `UART RX` / `TX` ............... `PA2` / `PA3` (USART2 Virtual COM Port)
  * `USB DM` / `DP` ................ `PA11` / `PA12` (USB FS Device)
  * `SWDIO` / `SWDCLK` ............. `PA13` / `PA14` (ST-Link Debug)
  * `User LED` ..................... `PB8` (Active-low onboard green LED)

---

## 4. Required LL Driver Files
Ensure the following ST Low-Level (LL) drivers are imported/referenced inside the board directory `src/firmware/board/STM32G431KB/Drivers/STM32G4xx_HAL_Driver/`:
* **Headers (`Inc/`):**
  * `stm32g4xx_ll_adc.h`, `stm32g4xx_ll_bus.h`, `stm32g4xx_ll_cortex.h`, `stm32g4xx_ll_dac.h`, `stm32g4xx_ll_dma.h`, `stm32g4xx_ll_dmamux.h`, `stm32g4xx_ll_exti.h`, `stm32g4xx_ll_gpio.h`, `stm32g4xx_ll_pwr.h`, `stm32g4xx_ll_rcc.h`, `stm32g4xx_ll_system.h`, `stm32g4xx_ll_tim.h`, `stm32g4xx_ll_usart.h`, `stm32g4xx_ll_utils.h`
* **Sources (`Src/`):**
  * `stm32g4xx_ll_adc.c`, `stm32g4xx_ll_dac.c`, `stm32g4xx_ll_dma.c`, `stm32g4xx_ll_exti.c`, `stm32g4xx_ll_gpio.c`, `stm32g4xx_ll_rcc.c`, `stm32g4xx_ll_tim.c`, `stm32g4xx_ll_usart.c`, `stm32g4xx_ll_utils.c`

---

## 5. Concrete Code Modification Blueprints

### Blueprint 5.1: `src/firmware/src/cfg/cfg_g431kb.h`
Uncomment the multimode high-speed ADC sampling options, and enable the maximum signal generator frequency parameter:

```c
<<<<<<< SEARCH
//#define EM_ADC_INTERLEAVED                                   // interleaved mode available  - TODO
//#define EM_ADC_DUALMODE                                      // dual mode available         - TODO
=======
#define EM_ADC_INTERLEAVED                                   // interleaved mode available
#define EM_ADC_DUALMODE                                      // dual mode available
>>>>>>> REPLACE
```

```c
<<<<<<< SEARCH
#define EM_SGEN_MAX_F          0          // SGEN max output freq.
=======
#define EM_SGEN_MAX_F          EM_DAC_TIM_MAX_F          // SGEN max output freq.
>>>>>>> REPLACE
```

### Blueprint 5.2: `src/firmware/src/cfg/cfg.h`
Modify the `EM_ADC_ADDR(x)` macro definition in the common calc helpers section of `cfg.h` to automatically redirect Master ADC DMA destination address to the Common Regular Data Register (`CDR`) when multimode (dual/interleaved) is active:

```c
<<<<<<< SEARCH
// calc helpers ----------------------------------------------------
#define EM_ADC_ADDR(x)           (uint32_t)LL_ADC_DMA_GetRegAddr(x, LL_ADC_DMA_REG_REGULAR_DATA) // ADC DMA address
=======
// calc helpers ----------------------------------------------------
#if defined(EM_ADC_DUALMODE) || defined(EM_ADC_INTERLEAVED)
  #define EM_ADC_ADDR(x)           ((self->dualmode || self->interleaved) ? (uint32_t)LL_ADC_DMA_GetRegAddr(x, LL_ADC_DMA_REG_REGULAR_DATA_MULTI) : (uint32_t)LL_ADC_DMA_GetRegAddr(x, LL_ADC_DMA_REG_REGULAR_DATA))
#else
  #define EM_ADC_ADDR(x)           (uint32_t)LL_ADC_DMA_GetRegAddr(x, LL_ADC_DMA_REG_REGULAR_DATA) // ADC DMA address
#endif
>>>>>>> REPLACE
```

### Blueprint 5.3: `src/firmware/src/app/daq/daq.c`
Define `chans` inside `daq_mem_set()` to solve the "undeclared chans" compile issue when `EM_ADC_INTERLEAVED` is enabled:

```c
<<<<<<< SEARCH
int daq_mem_set(daq_data_t* self, uint16_t mem_per_ch)
{
    daq_enable(self, EM_FALSE);
    daq_reset(self);

    daq_clear_buff(&self->buff1);
    daq_clear_buff(&self->buff2);
    daq_clear_buff(&self->buff3);
    daq_clear_buff(&self->buff4);
    self->buff_raw_ptr = 0;
    memset(self->buff_raw, 0, EM_DAQ_MAX_MEM * sizeof(uint8_t));

    int max_len = EM_DAQ_MAX_MEM;
    if (self->set.bits == B12)
        max_len /= 2;

    if (self->mode != LA)
=======
int daq_mem_set(daq_data_t* self, uint16_t mem_per_ch)
{
    daq_enable(self, EM_FALSE);
    daq_reset(self);

    daq_clear_buff(&self->buff1);
    daq_clear_buff(&self->buff2);
    daq_clear_buff(&self->buff3);
    daq_clear_buff(&self->buff4);
    self->buff_raw_ptr = 0;
    memset(self->buff_raw, 0, EM_DAQ_MAX_MEM * sizeof(uint8_t));

    int max_len = EM_DAQ_MAX_MEM;
    if (self->set.bits == B12)
        max_len /= 2;

    int chans = self->set.ch1_en + self->set.ch2_en + self->set.ch3_en + self->set.ch4_en; // Fix undeclared chans compile error for multimode

    if (self->mode != LA)
>>>>>>> REPLACE
```

---

## 6. Build & Compilation Verification Instructions
To compile and verify the STM32G431 firmware:
1. Ensure the ARM GCC embedded toolchain is installed (`gcc-arm-none-eabi`, `binutils-arm-none-eabi`, `libnewlib-arm-none-eabi`).
2. Run the custom compilation script from the repository root:
   ```bash
   python3 scripts/compile_firmware.py
   ```
   Or invoke the compiler manually with the G4-specific Cortex-M4 floating-point architecture flags:
   ```bash
   arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -O3 -std=gnu11 ...
   ```
3. Verify that the output binaries (`EMBO_G431KB.bin`, `EMBO_G431KB.hex`, `EMBO_G431KB.elf`) are generated correctly without any linker or compiler warnings.
