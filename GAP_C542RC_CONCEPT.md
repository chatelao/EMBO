# Gap Analysis: Compiling EMBO for STM32C542RC (Nucleo-C542RC)

This document provides a detailed Gap Analysis, integration blueprint, and hardware concept for supporting a hypothetical/conceptual **STM32C542RC** microcontroller (Nucleo-C542RC board) in the EMBO (EMBedded Oscilloscope) project.

---

## 1. Hardware & Core Overview
* **MCU Concept:** STM32C542RCT6 (ARM Cortex-M33 with FPU, TrustZone, up to 100+ MHz core clock)
* **Flash Memory:** 256 KB
* **SRAM:** 64 KB
* **Target Board:** Nucleo-C542RC (Nucleo-64 format with onboard ST-LINK/V3)
* **Peripheral Architecture:**
  * **Core Clock (HCLK):** 100 MHz (PLL driven)
  * **ADC Clock (ADCCLK):** 50 MHz (asynchronous PLL clock divided by 2 or direct APB2 clock)
  * **APB1 Clock (PCLK1):** 100 MHz
  * **APB2 Clock (PCLK2):** 100 MHz
  * **DMAMUX:** Present for peripheral request routing to DMA channels

---

## 2. Identified Gaps

### Gap 2.1: Missing Board Project & Core LL Drivers
Currently, there is no board/project directory for the STM32C5 series under `src/firmware/board/`.
* **Resolution:** Create the `src/firmware/board/STM32C542RC/` directory structure.
* **Requirements:**
  * `.project` and `.cproject` files configured for STM32C542RCTx target and ARM GCC.
  * Linker script `STM32C542RCTX_FLASH.ld` and startup file `startup_stm32c542xx.s`.
  * ST STM32CubeC5 LL source and header files imported under `Drivers/STM32C5xx_HAL_Driver/`.

### Gap 2.2: Missing Configuration Header `cfg_c542rc.h`
Each supported board requires a dedicated board configuration header inside `src/firmware/src/cfg/` to define pins, timers, DMAs, and capability limits.
* **Resolution:** Create `src/firmware/src/cfg/cfg_c542rc.h`.
* **Requirements:** Add preprocessor checks in `src/firmware/src/cfg/cfg.h` to include it when `STM32C542xx` or `EM_C542RC` is defined.

### Gap 2.3: Timer Mapping & Missing TIM15 Timer
Standard EMBO boards use **TIM15** as `EM_TIM_DAQ` to trigger regular ADC acquisitions for the Oscilloscope. The STM32C5 series does not possess a TIM15 peripheral.
* **Resolution:** Re-map `EM_TIM_DAQ` to a timer physically capable of triggering regular ADC conversions on the STM32C542RC.
  * **Option A (Optimal):** `TIM1` (runs on APB2 up to 100MHz, triggering ADC via `TIM1_TRGO` / EXTSEL multiplexer).
  * **Option B (Alternative):** `TIM3` (runs on APB1 up to 100MHz, triggering ADC via `TIM3_TRGO`).
  * TIM1 is configured as the optimal, high-frequency trigger choice.

### Gap 2.4: Pin Overlaps and Conflicts
To avoid conflicts between Oscilloscope (DAQ), Logic Analyzer (LA), Signal Generator (DAC), and the on-board user LED:
* **Resolution:** Map DAQ and LA pins to a single parallel GPIO port (GPIOA) to enable parallel DMA IDR register reads in a single transfer. Place the DAC and LED on non-conflicting pins.
  * **Conflict-Free Pin Layout:**
    * `DAQ / LA CH1` ........... `PA0` (ADC1_IN0)  - Arduino A0
    * `DAQ / LA CH2` ........... `PA1` (ADC1_IN1)  - Arduino A1
    * `DAQ / LA CH3` ........... `PA6` (ADC1_IN6)  - Arduino D12
    * `DAQ / LA CH4` ........... `PA7` (ADC1_IN7)  - Arduino D11
    * `DAC CH1` ................ `PA4` (DAC1_OUT1) - Arduino A2
    * `DAC CH2` ................ `PA5` (DAC1_OUT2) - Arduino A3
    * `EM_LED` ................. `PB13` (Green User LED on Nucleo-C542RC)
  This layout avoids pin conflicts and uses standard Arduino-compatible headers.

### Gap 2.5: DMAMUX & Request Mapping
Like other modern STM32 series, the STM32C5 features a DMA Request Multiplexer (DMAMUX).
* **Resolution:** Map the EMBO peripheral DMA channels cleanly through DMAMUX to avoid request overlapping:
  1. `EM_DMA_CH_ADC1`  -> `DMA1 Channel 1` (via `LL_DMAMUX_REQ_ADC1`)
  2. `EM_DMA_CH_LA`    -> `DMA1 Channel 2` (via `LL_DMAMUX_REQ_TIM1_UP` or EXTI trigger)
  3. `EM_DMA_CH_SGEN`  -> `DMA1 Channel 3` (via `LL_DMAMUX_REQ_DAC1_CH1`)
  4. `EM_DMA_CH_SGEN2` -> `DMA1 Channel 4` (via `LL_DMAMUX_REQ_DAC1_CH2`)
  5. `EM_DMA_CH_CNTR`  -> `DMA1 Channel 5` (via `LL_DMAMUX_REQ_TIM8_UP` or input capture)

---

## 3. Configuration File Blueprint (`cfg_c542rc.h`)

Below is the conceptual configuration header file to be placed in `src/firmware/src/cfg/cfg_c542rc.h`:

```c
/*
 * CTU/EMBO - EMBedded Oscilloscope <github.com/parezj/EMBO>
 * Author: Jakub Parez <parez.jakub@gmail.com>
 */

#ifndef INC_CFG_CFG_C542RC_H_
#define INC_CFG_CFG_C542RC_H_

#if defined(EM_C542RC)

#include "stm32c5xx.h"

/*
 * =========layout=========
 *  DAQ CH1 ........... PA0 (ADC1_IN0)  - both ADC + LA
 *  DAQ CH2 ........... PA1 (ADC1_IN1)  - both ADC + LA
 *  DAQ CH3 ........... PA6 (ADC1_IN6)  - both ADC + LA
 *  DAQ CH4 ........... PA7 (ADC1_IN7)  - both ADC + LA
 *  PWM CH1 ........... PB10 (TIM2_CH3)
 *  PWM CH2 ........... PB8  (TIM4_CH3)
 *  CNTR .............. PC9  (TIM8_CH4)
 *  DAC CH1 ........... PA4  (DAC1_OUT1)
 *  DAC CH2 ........... PA5  (DAC1_OUT2)
 *  UART RX ........... PA3  (USART2_RX)
 *  UART TX ........... PA2  (USART2_TX)
 *  USB D- ............ PA11 (USB_OTG_FS_DM)
 *  USB D+ ............ PA12 (USB_OTG_FS_DP)
 *  =======================
 */

// device -----------------------------------------------------------
#define EM_DEV_NAME            "EMBO-STM32C542RC-Nucleo64"
#define EM_DEV_COMM            "USB + USART2 (115200 bps)"
#define EM_LL_VER              "1.0.0"

// pins ------------------------------------------------------------
#define EM_PINS_SCOPE_VM       "PA0-PA1-PA6-PA7"
#define EM_PINS_LA             "PA0-PA1-PA6-PA7"
#define EM_PINS_CNTR           "PC9"
#define EM_PINS_PWM            "PB8-PB10"
#define EM_PINS_SGEN           "PA4-PA5"

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
#define EM_FREQ_HCLK           100000000 // HCLK clock - Core (100 MHz)
#define EM_FREQ_ADCCLK         50000000  // ADC clock (HCLK/2 = 50MHz)
#define EM_FREQ_PCLK1          100000000 // APB1 Clock (100 MHz)
#define EM_FREQ_PCLK2          100000000 // APB2 Clock (100 MHz)
#define EM_SYSTICK_FREQ        1000      // Systick clock

// UART -------------------------------------------------------------
#define EM_UART                USART2
#define EM_UART_RX_IRQHandler  USART2_IRQHandler
#define EM_UART_CLEAR_FLAG(x)  LL_USART_ClearFlag_RXNE(x);
#define EM_USB                 // USB Virtual COM port enabled
#define EM_UART_POLLINIT       // Poll for initialization

// LED -------------------------------------------------------------
#define EM_LED
#define EM_LED_PORT            GPIOB
#define EM_LED_PIN             13        // Green LED on Nucleo board PB13
#define EM_LED_INVERTED

// DAC (Signal Generator) -------------------------------------------
#define EM_DAC                 DAC1
#define EM_DAC_CH              LL_DAC_CHANNEL_1
#define EM_DAC_SRC             LL_DAC_TRIG_EXT_TIM6_TRGO
#define EM_DAC2                DAC1
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
#define EM_ADC_MODE_ADC1
#define EM_ADC_BIT12
#define EM_ADC_BIT8

#define EM_VREF                3300
#define EM_ADC_VREF_CAL        *((uint16_t*)0x1FFF7500) // Concept address for Vrefint Calibration
#define EM_ADC_VREF_CALVAL     3.3
#define EM_ADC_SMPLT_MAX       LL_ADC_SAMPLINGTIME_2CYCLES_5
#define EM_ADC_SMPLT_MAX_N     2.5
#define EM_ADC_TCONV8          8.5
#define EM_ADC_TCONV12         12.5
#define EM_ADC_C_F             0.000000000005 // ~5pF
#define EM_ADC_R_OHM           1000.0
#define EM_ADC_SMPLT_CNT       8

// Timers ----------------------------------------------------------
#define EM_TIM_DAQ             TIM1  // TIM1 runs on fast APB2
#define EM_TIM_DAQ_MAX         65535
#define EM_TIM_DAQ_FREQ        EM_FREQ_PCLK2
#define EM_TIM_DAQ_CC(a)       a##CC1

#define EM_TIM_PWM1            TIM2
#define EM_TIM_PWM1_MAX        65535
#define EM_TIM_PWM1_FREQ       EM_FREQ_PCLK1
#define EM_TIM_PWM1_CH         LL_TIM_CHANNEL_CH3
#define EM_TIM_PWM1_CHN(a)     a##CH3

#define EM_TIM_PWM2            TIM4
#define EM_TIM_PWM2_MAX        65535
#define EM_TIM_PWM2_FREQ       EM_FREQ_PCLK1
#define EM_TIM_PWM2_CH         LL_TIM_CHANNEL_CH3
#define EM_TIM_PWM2_CHN(a)     a##CH3

#define EM_TIM_CNTR            TIM8
#define EM_TIM_CNTR_FREQ       EM_FREQ_PCLK2
#define EM_TIM_CNTR_UP_IRQh    TIM8_UP_IRQHandler
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
#define EM_TIM_SGEN_FREQ       EM_FREQ_PCLK1
#define EM_TIM_SGEN_MAX        65535
#define EM_TIM_SGEN2           TIM7
#define EM_TIM_SGEN2_FREQ      EM_FREQ_PCLK1
#define EM_TIM_SGEN2_MAX       65535

// Memory Depth Allocation -----------------------------------------
#define EM_DAQ_MAX_MEM         32000  // 32KB acquisition buffer max
#define EM_LA_MAX_FS           10000000
#define EM_DAQ_MAX_B12_FS      5000000
#define EM_DAQ_MAX_B8_FS       5000000
#define EM_PWM_MAX_F           25000000
#define EM_SGEN_MAX_F          EM_DAC_TIM_MAX_F
#define EM_CNTR_MAX_F          50000000
#define EM_MEM_RESERVE         10

// ADC & DMA Mapping -----------------------------------------------
#define EM_ADC1                ADC1

#define EM_ADC1_USED

#define EM_ADC1_IRQh           ADC1_IRQHandler

#define EM_DMA_ADC1            DMA1
#define EM_DMA_LA              DMA1
#define EM_DMA_CNTR            DMA1
#define EM_DMA_CNTR2           DMA1
#define EM_DMA_SGEN            DMA1
#define EM_DMA_SGEN2           DMA1

#define EM_DMA_CH_ADC1         LL_DMA_CHANNEL_1
#define EM_DMA_CH_LA           LL_DMA_CHANNEL_2
#define EM_DMA_CH_CNTR         LL_DMA_CHANNEL_5
#define EM_DMA_CH_CNTR2        LL_DMA_CHANNEL_5
#define EM_DMA_CH_SGEN         LL_DMA_CHANNEL_3
#define EM_DMA_CH_SGEN2        LL_DMA_CHANNEL_4

#define EM_IRQN_ADC1           ADC1_IRQn
#define EM_IRQN_UART           USART2_IRQn
#define EM_LA_IRQ_EXTI1        EXTI0_IRQn
#define EM_LA_IRQ_EXTI2        EXTI1_IRQn
#define EM_LA_IRQ_EXTI3        EXTI9_5_IRQn
#define EM_LA_IRQ_EXTI4        EXTI9_5_IRQn
#define EM_CNTR_IRQ            TIM8_UP_IRQn

#define EM_IRQ_ADC1            EM_IRQN_ADC1

// Logic Analyzer pins & EXTI ---------------------------------------
#define EM_LA_EXTI_PORT        LL_SYSCFG_EXTI_PORTA
#define EM_LA_EXTI1            LL_EXTI_LINE_0   // PA0
#define EM_LA_EXTI2            LL_EXTI_LINE_1   // PA1
#define EM_LA_EXTI3            LL_EXTI_LINE_6   // PA6
#define EM_LA_EXTI4            LL_EXTI_LINE_7   // PA7
#define EM_LA_EXTI_UNUSED      LL_EXTI_LINE_2
#define EM_LA_EXTILINE1        LL_SYSCFG_EXTI_LINE0
#define EM_LA_EXTILINE2        LL_SYSCFG_EXTI_LINE1
#define EM_LA_EXTILINE3        LL_SYSCFG_EXTI_LINE6
#define EM_LA_EXTILINE4        LL_SYSCFG_EXTI_LINE7

#define EM_LA_CH1_IRQh         EXTI0_IRQHandler
#define EM_LA_CH2_IRQh         EXTI1_IRQHandler
#define EM_LA_CH3_IRQh         EXTI9_5_IRQHandler
#define EM_LA_UNUSED_IRQh      EXTI2_IRQHandler

#define EM_LA_IRQ1_CH1         la_irq_ch1
#define EM_LA_IRQ2_CH2         la_irq_ch2
#define EM_LA_IRQ3_CH3         la_irq_ch3
#define EM_LA_IRQ3_CH4         la_irq_ch4   // Shared IRQ3 handler

#define EM_ADC_AWD1            LL_ADC_AWD_CHANNEL_0_REG
#define EM_ADC_AWD2            LL_ADC_AWD_CHANNEL_1_REG
#define EM_ADC_AWD3            LL_ADC_AWD_CHANNEL_6_REG
#define EM_ADC_AWD4            LL_ADC_AWD_CHANNEL_7_REG
#define EM_ADC_CH1             LL_ADC_CHANNEL_0
#define EM_ADC_CH2             LL_ADC_CHANNEL_1
#define EM_ADC_CH3             LL_ADC_CHANNEL_6
#define EM_ADC_CH4             LL_ADC_CHANNEL_7

#define EM_GPIO_ADC_PORT1      GPIOA
#define EM_GPIO_ADC_PORT2      GPIOA
#define EM_GPIO_ADC_PORT3      GPIOA
#define EM_GPIO_ADC_PORT4      GPIOA
#define EM_GPIO_ADC_CH1        LL_GPIO_PIN_0
#define EM_GPIO_ADC_CH2        LL_GPIO_PIN_1
#define EM_GPIO_ADC_CH3        LL_GPIO_PIN_6
#define EM_GPIO_ADC_CH4        LL_GPIO_PIN_7

#define EM_GPIO_LA_PORT        GPIOA
#define EM_GPIO_LA_OFFSET      0
#define EM_GPIO_LA_CH1         LL_GPIO_PIN_0
#define EM_GPIO_LA_CH2         LL_GPIO_PIN_1
#define EM_GPIO_LA_CH3         LL_GPIO_PIN_6
#define EM_GPIO_LA_CH4         LL_GPIO_PIN_7

#define EM_GPIO_LA_CH1_NUM     0
#define EM_GPIO_LA_CH2_NUM     1
#define EM_GPIO_LA_CH3_NUM     6
#define EM_GPIO_LA_CH4_NUM     7

#endif
#endif /* INC_CFG_CFG_C542RC_H_ */
```

---

## 4. Required LL Driver Files
The following Low-Level (LL) drivers must be copied/imported into the board project's `Drivers/STM32C5xx_HAL_Driver/` to satisfy EMBO compilation:
* **Headers (`Inc/`):**
  * `stm32c5xx_ll_adc.h`
  * `stm32c5xx_ll_bus.h`
  * `stm32c5xx_ll_cortex.h`
  * `stm32c5xx_ll_dac.h`
  * `stm32c5xx_ll_dma.h`
  * `stm32c5xx_ll_exti.h`
  * `stm32c5xx_ll_gpio.h`
  * `stm32c5xx_ll_pwr.h`
  * `stm32c5xx_ll_rcc.h`
  * `stm32c5xx_ll_system.h`
  * `stm32c5xx_ll_tim.h`
  * `stm32c5xx_ll_usart.h`
  * `stm32c5xx_ll_utils.h`
* **Sources (`Src/`):**
  * `stm32c5xx_ll_adc.c`
  * `stm32c5xx_ll_dac.c`
  * `stm32c5xx_ll_dma.c`
  * `stm32c5xx_ll_exti.c`
  * `stm32c5xx_ll_gpio.c`
  * `stm32c5xx_ll_rcc.c`
  * `stm32c5xx_ll_tim.c`
  * `stm32c5xx_ll_usart.c`
  * `stm32c5xx_ll_utils.c`

---

## 5. Required Shared Code Modifications

To complete the support inside the shared EMBO sources, two files must be updated:

### 5.1 Updates to `src/firmware/src/cfg/cfg.h`
Add a preprocessor check block for `STM32C542xx`:

```c
#elif defined(STM32C542xx)
/*.................................................. C542RC .................................................*/

    #define EM_C542RC
    #define EM_CORTEX_M33

    /*
     * =========layout=========
     *  DAQ CH1 ........... PA0 (ADC1_IN0)  - both ADC + LA
     *  DAQ CH2 ........... PA1 (ADC1_IN1)  - both ADC + LA
     *  DAQ CH3 ........... PA6 (ADC1_IN6)  - both ADC + LA
     *  DAQ CH4 ........... PA7 (ADC1_IN7)  - both ADC + LA
     *  PWM CH1 ........... PB10 (TIM2_CH3)
     *  PWM CH2 ........... PB8  (TIM4_CH3)
     *  CNTR .............. PC9  (TIM8_CH4)
     *  DAC CH1 ........... PA4  (DAC1_OUT1)
     *  DAC CH2 ........... PA5  (DAC1_OUT2)
     *  UART RX ........... PA3  (USART2_RX)
     *  UART TX ........... PA2  (USART2_TX)
     *  USB D- ............ PA11 (USB_OTG_FS_DM)
     *  USB D+ ............ PA12 (USB_OTG_FS_DP)
     *  =======================
     */

    #include "cfg_c542rc.h"
```

### 5.2 Updates to `src/firmware/src/cfg/cfg.c`
Add the sampling time configuration array inside `src/firmware/src/cfg/cfg.c`:

```c
#elif defined (STM32C542xx)

    #include "stm32c5xx_ll_adc.h"

    const uint32_t EM_ADC_SMPLT[EM_ADC_SMPLT_CNT] = { LL_ADC_SAMPLINGTIME_1CYCLE_5, LL_ADC_SAMPLINGTIME_2CYCLES_5, LL_ADC_SAMPLINGTIME_8CYCLES_5,
                                                      LL_ADC_SAMPLINGTIME_16CYCLES_5, LL_ADC_SAMPLINGTIME_32CYCLES_5, LL_ADC_SAMPLINGTIME_64CYCLES_5,
                                                      LL_ADC_SAMPLINGTIME_128CYCLES_5, LL_ADC_SAMPLINGTIME_640CYCLES_5};
    const float EM_ADC_SMPLT_N[EM_ADC_SMPLT_CNT]  = { 1.5, 2.5, 8.5, 16.5, 32.5, 64.5, 128.5, 640.5};
```

---

## 6. Project Integration Steps
1. Create `src/firmware/board/STM32C542RC/` as a clone of `STM32F446RE` or `STM32G431KB`.
2. Configure `.project`, `.cproject`, and `.ioc` for the STM32C542RCTx MCU.
3. Import the required LL Driver files as outlined in Section 4.
4. Modify `cfg.h` and `cfg.c` with the code blocks in Section 5.
5. Compile using `scripts/compile_firmware.py` or directly with GCC compiler flags targeting the ARM Cortex-M33 architecture:
   `-mcpu=cortex-m33 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16`.
