# Analysis and Compilation Guide: STM32F446RE and STM32G431

This document provides the gap analysis and compilation instructions for bringing up and configuring the **STM32F446RE** and **STM32G431** microcontrollers under the EMBO (EMBedded Oscilloscope) project firmware.

---

# Part 1: Gap Analysis & Integration Guide for STM32F446RE (Nucleo-64)

## 1. Hardware & Core Overview
* **MCU:** STM32F446RET6 (ARM Cortex-M4 with FPU, up to 180 MHz core clock)
* **Flash Memory:** 512 KB
* **SRAM:** 128 KB (112 KB system SRAM + 16 KB auxiliary SRAM)
* **Target Board:** Nucleo-F446RE (Nucleo-64 format with onboard ST-LINK/V2-1)

---

## 2. Identified Gaps

### Gap 2.1: Missing Board Project
Currently, there is no project directory for STM32F446RE under `src/firmware/board/`.
* **Resolution:** Create `src/firmware/board/STM32F446RE/` directory, patterned after the `STM32F401CC` structure.
* **Requirements:**
  * `.project` and `.cproject` files configured for STM32F446RETx.
  * STM32CubeMX project file `EMBO_F446RE.ioc` for configuration.
  * Linker script `STM32F446RETX_FLASH.ld` and startup file `startup_stm32f446xx.s`.

### Gap 2.2: Missing Configuration Header `cfg_f446re.h`
Each supported board requires a specific configuration header inside `src/firmware/src/cfg/` to define pins, timers, DMAs, and capability limits.
* **Resolution:** Create `src/firmware/src/cfg/cfg_f446re.h`.
* **Requirements:** Add preprocessor checks in `src/firmware/src/cfg/cfg.h` to include it when `STM32F446xx` or `EM_F446RE` is defined.

### Gap 2.3: Timer Mapping & Missing TIM15 Timer
Standard EMBO boards use **TIM15** as `EM_TIM_DAQ` to trigger regular ADC acquisitions for the Oscilloscope. **The STM32F446xx does not possess a TIM15 peripheral.**
* **Resolution:**
  * Re-map the `EM_TIM_DAQ` to an alternate 16-bit timer available on the STM32F446.
  * **Option A:** `TIM9` (2 channels, 16-bit, APB2 180MHz max frequency).
  * **Option B:** `TIM12` (2 channels, 16-bit, APB1 90MHz max frequency).
  * TIM9 is the optimal choice since it runs on the faster APB2 clock domain, enabling higher-resolution trigger intervals.

### Gap 2.4: USB and Virtual COM Port Configuration
The STM32F446 uses the USB OTG FS (On-The-Go Full Speed) peripheral for emulated Virtual COM Port (CDC class) communication.
* **Resolution:** Include the `STM32_USB_Device_Library` middleware into the board project and configure `USB_DEVICE/` setup files mapping to the USB OTG FS pins (PA11 for DM, PA12 for DP).

---

## 3. Configuration File Blueprint (`cfg_f446re.h`)

Below is the required configuration for `src/firmware/src/cfg/cfg_f446re.h`:

```c
/*
 * CTU/EMBO - EMBedded Oscilloscope <github.com/parezj/EMBO>
 * Author: Jakub Parez <parez.jakub@gmail.com>
 */

#ifndef INC_CFG_CFG_F446RE_H_
#define INC_CFG_CFG_F446RE_H_

#if defined(EM_F446RE)

#include "stm32f4xx.h"

/*
 * =========layout=========
 *  DAQ CH1 ........... PA0 (ADC123_IN0)
 *  DAQ CH2 ........... PA1 (ADC123_IN1)
 *  DAQ CH3 ........... PA4 (ADC12_IN4)
 *  DAQ CH4 ........... PA5 (ADC12_IN5)
 *  PWM CH1 ........... PB10 (TIM2_CH3)
 *  PWM CH2 ........... PB8  (TIM4_CH3)
 *  CNTR .............. PC9  (TIM8_CH4)
 *  DAC CH1 ........... PA4  (DAC_OUT1)
 *  DAC CH2 ........... PA5  (DAC_OUT2)
 *  UART RX ........... PA3  (USART2_RX)
 *  UART TX ........... PA2  (USART2_TX)
 *  USB D- ............ PA11 (USB_OTG_FS_DM)
 *  USB D+ ............ PA12 (USB_OTG_FS_DP)
 *  =======================
 */

// device -----------------------------------------------------------
#define EM_DEV_NAME            "EMBO-STM32F446RE-Nucleo64"
#define EM_DEV_COMM            "USB + USART2 (115200 bps)"
#define EM_LL_VER              "1.26.2"

// pins ------------------------------------------------------------
#define EM_PINS_SCOPE_VM       "A0-A1-A4-A5"
#define EM_PINS_LA             "A0-A1-A4-A5"
#define EM_PINS_CNTR           "C9"
#define EM_PINS_PWM            "B8-B10"
#define EM_PINS_SGEN           "A4-A5"

// stack size ------------------------------------------------------
#define EM_STACK_MIN           128
#define EM_STACK_T1            128
#define EM_STACK_T2            128
#define EM_STACK_T3            128
#define EM_STACK_T4            512
#define EM_STACK_T5            128

// IRQ priorities --------------------------------------------------
#define EM_IT_PRI_CNTR         4   // Counter - overflow bit
#define EM_IT_PRI_ADC          5   // Analog Watchdog ADC
#define EM_IT_PRI_EXTI         5   // Logic Analyzer GPIO
#define EM_IT_PRI_UART         6   // UART RX
#define EM_IT_PRI_USB          7   // USB RX
#define EM_IT_PRI_SYST         15  // Systick

// clock frequencies -----------------------------------------------
#define EM_FREQ_LSI            32000     // LSI clock - watchdog
#define EM_FREQ_HCLK           180000000 // HCLK clock - Core (180 MHz)
#define EM_FREQ_ADCCLK         22500000  // ADC clock (APB2/8 = 180MHz/8 = 22.5MHz)
#define EM_FREQ_PCLK1          45000000  // APB1 Clock (45 MHz)
#define EM_FREQ_PCLK2          90000000  // APB2 Clock (90 MHz)
#define EM_SYSTICK_FREQ        1000      // Systick clock

// UART -------------------------------------------------------------
#define EM_UART                USART2
#define EM_UART_RX_IRQHandler  USART2_IRQHandler
#define EM_UART_CLEAR_FLAG(x)  LL_USART_ClearFlag_RXNE(x);
#define EM_USB                 // USB Virtual COM port enabled
#define EM_UART_POLLINIT       // Poll for initialization

// LED -------------------------------------------------------------
#define EM_LED
#define EM_LED_PORT            GPIOA
#define EM_LED_PIN             5         // Green LED on Nucleo board PA5
#define EM_LED_INVERTED

// DAC (Signal Generator) -------------------------------------------
#define EM_DAC                 DAC
#define EM_DAC_CH              LL_DAC_CHANNEL_1
#define EM_DAC_SRC             LL_DAC_TRIG_EXT_TIM6_TRGO
#define EM_DAC2                DAC
#define EM_DAC2_CH             LL_DAC_CHANNEL_2
#define EM_DAC2_SRC            LL_DAC_TRIG_EXT_TIM7_TRGO
#define EM_DAC_BUFF_LEN        1000
#define EM_DAC_MAX_VAL         4095.0
#define EM_DAC_TIM_MAX_F       5000000

// GPIO ------------------------------------------------------------
#define EM_GPIO_EXTI_SRC       LL_SYSCFG_SetEXTISource
#define EM_GPIO_EXTI_ACTIVE_R  LL_EXTI_IsActiveFlag_0_31
#define EM_GPIO_EXTI_ACTIVE_F  LL_EXTI_IsActiveFlag_0_31
#define EM_GPIO_EXTI_CLEAR_R   LL_EXTI_ClearFlag_0_31
#define EM_GPIO_EXTI_CLEAR_F   LL_EXTI_ClearFlag_0_31

// DAQ -------------------------------------------------------------
#define EM_DAQ_4CH

// ADC -------------------------------------------------------------
#define EM_ADC_MODE_ADC12
#define EM_ADC_BIT12
#define EM_ADC_BIT8

#define EM_VREF                3300
#define EM_ADC_VREF_CAL        *((uint16_t*)0x1FFF7A2A) // STM32F446 Vrefint Calibration address
#define EM_ADC_VREF_CALVAL     3.3
#define EM_ADC_SMPLT_MAX       LL_ADC_SAMPLINGTIME_3CYCLES
#define EM_ADC_SMPLT_MAX_N     3.0
#define EM_ADC_TCONV8          8.5
#define EM_ADC_TCONV12         12.5
#define EM_ADC_C_F             0.000000000006 // ~6pF
#define EM_ADC_R_OHM           1500.0
#define EM_ADC_SMPLT_CNT       8

// Timers ----------------------------------------------------------
#define EM_TIM_DAQ             TIM9  // Replaced TIM15 with TIM9
#define EM_TIM_DAQ_MAX         65535
#define EM_TIM_DAQ_FREQ        EM_FREQ_PCLK2
#define EM_TIM_DAQ_CC(a)       a##CC1

#define EM_TIM_PWM1            TIM2
#define EM_TIM_PWM1_MAX        65535
#define EM_TIM_PWM1_FREQ       EM_FREQ_PCLK1 * 2 // TIM2 input frequency is 90MHz
#define EM_TIM_PWM1_CH         LL_TIM_CHANNEL_CH3
#define EM_TIM_PWM1_CHN(a)     a##CH3

#define EM_TIM_PWM2            TIM4
#define EM_TIM_PWM2_MAX        65535
#define EM_TIM_PWM2_FREQ       EM_FREQ_PCLK1 * 2 // TIM4 input frequency is 90MHz
#define EM_TIM_PWM2_CH         LL_TIM_CHANNEL_CH3
#define EM_TIM_PWM2_CHN(a)     a##CH3

#define EM_TIM_CNTR            TIM8
#define EM_TIM_CNTR_FREQ       EM_FREQ_PCLK2 * 2 // TIM8 input frequency is 180MHz
#define EM_TIM_CNTR_UP_IRQh    TIM8_UP_TIM13_IRQHandler
#define EM_TIM_CNTR_MAX        65535
#define EM_TIM_CNTR_CH         LL_TIM_CHANNEL_CH4
#define EM_TIM_CNTR_CH2        LL_TIM_CHANNEL_CH3
#define EM_TIM_CNTR_CCR        CCR4
#define EM_TIM_CNTR_CCR2       CCR2
#define EM_TIM_CNTR_CC(a)      a##CC4
#define EM_TIM_CNTR_CC2(a)     a##CC3
#define EM_TIM_CNTR_OVF(a)     a##CH2
#define EM_TIM_CNTR_PSC_FAST   8

#define EM_TIM_SGEN            TIM6
#define EM_TIM_SGEN_FREQ       EM_FREQ_PCLK1 * 2
#define EM_TIM_SGEN_MAX        65535
#define EM_TIM_SGEN2           TIM7
#define EM_TIM_SGEN2_FREQ      EM_FREQ_PCLK1 * 2
#define EM_TIM_SGEN2_MAX       65535

// Memory Depth Allocation -----------------------------------------
#define EM_DAQ_MAX_MEM         64000  // F446RE has large SRAM (128KB), allowing up to 64KB acquisition buffer
#define EM_LA_MAX_FS           15000000
#define EM_DAQ_MAX_B12_FS      6000000
#define EM_DAQ_MAX_B8_FS       6000000
#define EM_PWM_MAX_F           45000000
#define EM_SGEN_MAX_F          EM_DAC_TIM_MAX_F
#define EM_CNTR_MAX_F          90000000
#define EM_MEM_RESERVE         10

// ADC & DMA Mapping -----------------------------------------------
#define EM_ADC1                ADC1
#define EM_ADC2                ADC2

#define EM_ADC1_USED
#define EM_ADC2_USED

#define EM_ADC12_IRQh          ADC_IRQHandler

#define EM_DMA_ADC1            DMA2
#define EM_DMA_ADC2            DMA2
#define EM_DMA_LA              DMA2
#define EM_DMA_CNTR            DMA2
#define EM_DMA_CNTR2           DMA2
#define EM_DMA_SGEN            DMA1
#define EM_DMA_SGEN2           DMA1

#define EM_DMA_CH_ADC1         LL_DMA_STREAM_0
#define EM_DMA_CH_ADC2         LL_DMA_STREAM_2
#define EM_DMA_CH_LA           LL_DMA_STREAM_1
#define EM_DMA_CH_CNTR         LL_DMA_STREAM_3
#define EM_DMA_CH_CNTR2        LL_DMA_STREAM_4
#define EM_DMA_CH_SGEN         LL_DMA_STREAM_5
#define EM_DMA_CH_SGEN2        LL_DMA_STREAM_6

#define EM_IRQN_ADC1           ADC_IRQn
#define EM_IRQN_ADC2           ADC_IRQn
#define EM_IRQN_UART           USART2_IRQn
#define EM_LA_IRQ_EXTI1        EXTI0_IRQn
#define EM_LA_IRQ_EXTI2        EXTI1_IRQn
#define EM_LA_IRQ_EXTI3        EXTI4_IRQn
#define EM_LA_IRQ_EXTI4        EXTI9_5_IRQn
#define EM_CNTR_IRQ            TIM8_UP_TIM13_IRQn

#define EM_IRQ_ADC1            EM_IRQN_ADC1
#define EM_IRQ_ADC2            EM_IRQN_ADC2

// Logic Analyzer pins & EXTI ---------------------------------------
#define EM_LA_EXTI_PORT        LL_SYSCFG_EXTI_PORTA
#define EM_LA_EXTI1            LL_EXTI_LINE_0
#define EM_LA_EXTI2            LL_EXTI_LINE_1
#define EM_LA_EXTI3            LL_EXTI_LINE_4
#define EM_LA_EXTI4            LL_EXTI_LINE_5
#define EM_LA_EXTI_UNUSED      LL_EXTI_LINE_2
#define EM_LA_EXTILINE1        LL_SYSCFG_EXTI_LINE0
#define EM_LA_EXTILINE2        LL_SYSCFG_EXTI_LINE1
#define EM_LA_EXTILINE3        LL_SYSCFG_EXTI_LINE4
#define EM_LA_EXTILINE4        LL_SYSCFG_EXTI_LINE5

#define EM_LA_CH1_IRQh         EXTI0_IRQHandler
#define EM_LA_CH2_IRQh         EXTI1_IRQHandler
#define EM_LA_CH3_IRQh         EXTI4_IRQHandler
#define EM_LA_CH4_IRQh         EXTI9_5_IRQHandler
#define EM_LA_UNUSED_IRQh      EXTI2_IRQHandler

#define EM_LA_IRQ1_CH1         la_irq_ch1
#define EM_LA_IRQ2_CH2         la_irq_ch2
#define EM_LA_IRQ3_CH3         la_irq_ch3
#define EM_LA_IRQ4_CH4         la_irq_ch4

#define EM_ADC_AWD1            LL_ADC_AWD_CHANNEL_0_REG
#define EM_ADC_AWD2            LL_ADC_AWD_CHANNEL_1_REG
#define EM_ADC_AWD3            LL_ADC_AWD_CHANNEL_4_REG
#define EM_ADC_AWD4            LL_ADC_AWD_CHANNEL_5_REG
#define EM_ADC_CH1             LL_ADC_CHANNEL_0
#define EM_ADC_CH2             LL_ADC_CHANNEL_1
#define EM_ADC_CH3             LL_ADC_CHANNEL_4
#define EM_ADC_CH4             LL_ADC_CHANNEL_5

#define EM_GPIO_ADC_PORT1      GPIOA
#define EM_GPIO_ADC_PORT2      GPIOA
#define EM_GPIO_ADC_PORT3      GPIOA
#define EM_GPIO_ADC_PORT4      GPIOA
#define EM_GPIO_ADC_CH1        LL_GPIO_PIN_0
#define EM_GPIO_ADC_CH2        LL_GPIO_PIN_1
#define EM_GPIO_ADC_CH3        LL_GPIO_PIN_4
#define EM_GPIO_ADC_CH4        LL_GPIO_PIN_5

#define EM_GPIO_LA_PORT        GPIOA
#define EM_GPIO_LA_OFFSET      0
#define EM_GPIO_LA_CH1         LL_GPIO_PIN_0
#define EM_GPIO_LA_CH2         LL_GPIO_PIN_1
#define EM_GPIO_LA_CH3         LL_GPIO_PIN_4
#define EM_GPIO_LA_CH4         LL_GPIO_PIN_5

#define EM_GPIO_LA_CH1_NUM     0
#define EM_GPIO_LA_CH2_NUM     1
#define EM_GPIO_LA_CH3_NUM     4
#define EM_GPIO_LA_CH4_NUM     5

#endif
#endif /* INC_CFG_CFG_F446RE_H_ */
```

---

# Part 2: Gap Analysis & Integration Guide for STM32G431 (Nucleo-32)

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

# Part 3: Build & Compilation Verification
To compile either target within STM32CubeIDE:
1. Import target folder (`src/firmware/board/STM32F446RE/` or `src/firmware/board/STM32G431KB/`) into STM32CubeIDE as an existing project.
2. Ensure compiler options target the Cortex-M4 with hardware floating point:
   `-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16`
3. The linked root source code directory (`src/firmware/src/`) will be automatically compiled.
