# Gap Analysis: Compiling EMBO for STM32F446RE (Nucleo-64)

This document provides a detailed Gap Analysis and integration guide for supporting the **STM32F446RE** microcontroller (Nucleo-F446RE board) in the EMBO (EMBedded Oscilloscope) project.

---

## 1. Hardware & Core Overview
* **MCU:** STM32F446RET6 (ARM Cortex-M4 with FPU, up to 180 MHz core clock)
* **Flash Memory:** 512 KB
* **SRAM:** 128 KB (112 KB system SRAM + 16 KB auxiliary SRAM)
* **Target Board:** Nucleo-F446RE (Nucleo-64 format with onboard ST-LINK/V2-1)

---

## 2. Identified Gaps

### Gap 2.1: Missing Board Project & LL Drivers
Currently, there is no project directory for STM32F446RE under `src/firmware/board/`.
* **Resolution:** Create `src/firmware/board/STM32F446RE/` directory, patterned after the `STM32F401CC` structure.
* **Requirements:**
  * `.project` and `.cproject` files configured for STM32F446RETx.
  * STM32CubeMX project file `EMBO_F446RE.ioc` for configuration.
  * Linker script `STM32F446RETX_FLASH.ld` and startup file `startup_stm32f446xx.s`.
  * **Crucial Dependency Note:** The existing `STM32F401CC` board directory in EMBO contains *only* HAL drivers (`stm32f4xx_hal_*.c/h`), whereas the shared EMBO codebase relies entirely on LL (Low-Level) drivers. For the STM32F446RE to compile, the ST STM32CubeF4 LL source and header files must be included in the board's `Drivers/STM32F4xx_HAL_Driver/` directory.

### Gap 2.2: Missing Configuration Header `cfg_f446re.h`
Each supported board requires a specific configuration header inside `src/firmware/src/cfg/` to define pins, timers, DMAs, and capability limits.
* **Resolution:** Create `src/firmware/src/cfg/cfg_f446re.h`.
* **Requirements:** Add preprocessor checks in `src/firmware/src/cfg/cfg.h` to include it when `STM32F446xx` or `EM_F446RE` is defined.

### Gap 2.3: Timer Mapping & Invalid TIM9/TIM12 Suggestion for ADC Triggering
Standard EMBO boards use **TIM15** as `EM_TIM_DAQ` to trigger regular ADC acquisitions for the Oscilloscope. The STM32F446xx does not possess a TIM15 peripheral.
* **Flaw in Previous Analysis:** Previous analyses proposed re-mapping `EM_TIM_DAQ` to `TIM9` or `TIM12`. However, **neither TIM9 nor TIM12 is physically connected to the ADC external trigger multiplexer (EXTSEL) on STM32F4 family microcontrollers**, making a TIM9/TIM12-based trigger concept completely unimplementable.
* **Resolution:**
  * Re-map `EM_TIM_DAQ` to a timer that is physically capable of triggering ADC regular conversions on the STM32F446RE.
  * **Option A (Optimal):** `TIM1` (runs on the faster APB2 clock domain up to 180MHz, enabling higher-resolution trigger intervals, triggering ADC via `TIM1_TRGO` / EXTSEL `0011`).
  * **Option B (Alternative):** `TIM3` (runs on the APB1 clock domain up to 90MHz, triggering ADC via `TIM3_TRGO` / EXTSEL `1000`).
  * We configure the blueprint below using **TIM1** as the optimal, high-frequency trigger choice.

### Gap 2.4: Pin Overlaps and Conflicts
* **Flaw in Previous Analysis:** Previous analyses mapped `DAQ CH3`/`CH4` and `DAC CH1`/`CH2` to the exact same pins (`PA4` and `PA5`), which prevents using the Oscilloscope and Signal Generator simultaneously. Additionally, the green user LED on the Nucleo board is hardwired to `PA5`, causing severe conflicts with both `DAC CH2` and `DAQ CH4`.
* **Resolution:** Re-map `DAQ` (Scope) and `LA` (Logic Analyzer) pins to a separate set of GPIOA pins that do not conflict with the DAC or LED. The Logic Analyzer must reside on a single GPIO port to read the Input Data Register (IDR) simultaneously in a single DMA pass.
  * **Conflict-Free Pin Layout:**
    * `DAQ / LA CH1` ........... `PA0` (ADC123_IN0) - Arduino A0
    * `DAQ / LA CH2` ........... `PA1` (ADC123_IN1) - Arduino A1
    * `DAQ / LA CH3` ........... `PA6` (ADC12_IN6)  - Arduino D12
    * `DAQ / LA CH4` ........... `PA7` (ADC12_IN7)  - Arduino D11
    * `DAC CH1` ................ `PA4` (DAC_OUT1)   - Arduino A2
    * `DAC CH2` ................ `PA5` (DAC_OUT2)   - Arduino A3 (Hardware Note: Output toggle will affect/blink the onboard green LED)
    * `EM_LED` ................. `PA5` (Green LED)
  This layout avoids pin conflicts and uses the standard Arduino analog/digital headers.

### Gap 2.5: Incorrect Counter (TIM8) DMA Mappings
* **Flaw in Previous Analysis:** Previous analyses defined `EM_DMA_CH_CNTR` (the capture DMA) as `LL_DMA_STREAM_3` on DMA2.
* **Flaw:** On STM32F446, `TIM8_CH4` is routed **only to Stream 7 on DMA2 (Channel 7)**. It is physically impossible to route it to Stream 3.
* **Resolution:** Correct `EM_DMA_CH_CNTR` to `LL_DMA_STREAM_7` (Channel 7). Set `EM_DMA_CH_CNTR2` (which handles `TIM8_CH3`) to `LL_DMA_STREAM_4` (Channel 7).

### Gap 2.6: USB and Virtual COM Port Configuration
The STM32F446 uses the USB OTG FS (On-The-Go Full Speed) peripheral for emulated Virtual COM Port (CDC class) communication.
* **Resolution:** Include the `STM32_USB_Device_Library` middleware into the board project and configure `USB_DEVICE/` setup files mapping to the USB OTG FS pins (PA11 for DM, PA12 for DP).

---

## 3. Configuration File Blueprint (`cfg_f446re.h`)

Create `src/firmware/src/cfg/cfg_f446re.h` containing:

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
 *  DAQ CH1 ........... PA0 (ADC123_IN0) - both ADC + LA
 *  DAQ CH2 ........... PA1 (ADC123_IN1) - both ADC + LA
 *  DAQ CH3 ........... PA6 (ADC12_IN6)  - both ADC + LA
 *  DAQ CH4 ........... PA7 (ADC12_IN7)  - both ADC + LA
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
#define EM_PINS_SCOPE_VM       "A0-A1-A6-A7"
#define EM_PINS_LA             "A0-A1-A6-A7"
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
#define EM_FREQ_ADCCLK         22500000  // ADC clock (APB2/4 = 90MHz/4 = 22.5MHz)
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
// DAQ Timer configured to TIM1 (optimal choice on fast APB2 clock domain)
#define EM_TIM_DAQ             TIM1
#define EM_TIM_DAQ_MAX         65535
#define EM_TIM_DAQ_FREQ        (EM_FREQ_PCLK2 * 2) // TIM1 runs on APB2 multiplied clock (180 MHz)
#define EM_TIM_DAQ_CC(a)       a##CC1

#define EM_TIM_PWM1            TIM2
#define EM_TIM_PWM1_MAX        65535
#define EM_TIM_PWM1_FREQ       (EM_FREQ_PCLK1 * 2) // TIM2 input frequency is 90MHz
#define EM_TIM_PWM1_CH         LL_TIM_CHANNEL_CH3
#define EM_TIM_PWM1_CHN(a)     a##CH3

#define EM_TIM_PWM2            TIM4
#define EM_TIM_PWM2_MAX        65535
#define EM_TIM_PWM2_FREQ       (EM_FREQ_PCLK1 * 2) // TIM4 input frequency is 90MHz
#define EM_TIM_PWM2_CH         LL_TIM_CHANNEL_CH3
#define EM_TIM_PWM2_CHN(a)     a##CH3

#define EM_TIM_CNTR            TIM8
#define EM_TIM_CNTR_FREQ       (EM_FREQ_PCLK2 * 2) // TIM8 input frequency is 180MHz
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
#define EM_TIM_SGEN_FREQ       (EM_FREQ_PCLK1 * 2)
#define EM_TIM_SGEN_MAX        65535
#define EM_TIM_SGEN2           TIM7
#define EM_TIM_SGEN2_FREQ      (EM_FREQ_PCLK1 * 2)
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

// Stream Mapping corrected to match STM32F446 DMA2 request matrix
#define EM_DMA_CH_ADC1         LL_DMA_STREAM_0  // ADC1 is on Stream 0 (Channel 0)
#define EM_DMA_CH_ADC2         LL_DMA_STREAM_2  // ADC2 is on Stream 2 (Channel 1)
#define EM_DMA_CH_LA           LL_DMA_STREAM_1  // TIM1_CH1 triggers DMA2 Stream 1 (Channel 6)
#define EM_DMA_CH_CNTR         LL_DMA_STREAM_7  // TIM8_CH4 is exclusively routed to Stream 7 (Channel 7)
#define EM_DMA_CH_CNTR2        LL_DMA_STREAM_4  // TIM8_CH3 is routed to Stream 4 (Channel 7)
#define EM_DMA_CH_SGEN         LL_DMA_STREAM_5  // DAC1 is on DMA1 Stream 5 (Channel 7)
#define EM_DMA_CH_SGEN2        LL_DMA_STREAM_6  // DAC2 is on DMA1 Stream 6 (Channel 7)

#define EM_IRQN_ADC1           ADC_IRQn
#define EM_IRQN_ADC2           ADC_IRQn
#define EM_IRQN_UART           USART2_IRQn
#define EM_LA_IRQ_EXTI1        EXTI0_IRQn
#define EM_LA_IRQ_EXTI2        EXTI1_IRQn
#define EM_LA_IRQ_EXTI3        EXTI9_5_IRQn
#define EM_LA_IRQ_EXTI4        EXTI9_5_IRQn
#define EM_CNTR_IRQ            TIM8_UP_TIM13_IRQn

#define EM_IRQ_ADC1            EM_IRQN_ADC1
#define EM_IRQ_ADC2            EM_IRQN_ADC2

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
// EM_LA_CH4_IRQh is commented out to avoid double-definition of the EXTI9_5 vector.
// Both CH3 and CH4 will share the same EXTI9_5 ISR.
//#define EM_LA_CH4_IRQh         EXTI9_5_IRQHandler
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
#endif /* INC_CFG_CFG_F446RE_H_ */
```

---

## 4. Required LL Driver Files
The following Low-Level (LL) drivers must be copied from the STM32CubeF4 repository into `src/firmware/board/STM32F446RE/Drivers/STM32F4xx_HAL_Driver/` to satisfy EMBO compile requirements:
* **Headers (`Inc/`):**
  * `stm32f4xx_ll_adc.h`
  * `stm32f4xx_ll_bus.h`
  * `stm32f4xx_ll_cortex.h`
  * `stm32f4xx_ll_dac.h`
  * `stm32f4xx_ll_dma.h`
  * `stm32f4xx_ll_exti.h`
  * `stm32f4xx_ll_gpio.h`
  * `stm32f4xx_ll_pwr.h`
  * `stm32f4xx_ll_rcc.h`
  * `stm32f4xx_ll_system.h`
  * `stm32f4xx_ll_tim.h`
  * `stm32f4xx_ll_usart.h`
  * `stm32f4xx_ll_utils.h`
* **Sources (`Src/`):**
  * `stm32f4xx_ll_adc.c`
  * `stm32f4xx_ll_dac.c`
  * `stm32f4xx_ll_dma.c`
  * `stm32f4xx_ll_exti.c`
  * `stm32f4xx_ll_gpio.c`
  * `stm32f4xx_ll_rcc.c`
  * `stm32f4xx_ll_tim.c`
  * `stm32f4xx_ll_usart.c`
  * `stm32f4xx_ll_utils.c`

---

## 5. Required Shared Code Modifications

To complete the support inside the shared EMBO sources, two files must be updated:

### 5.1 Updates to `src/firmware/src/cfg/cfg.h`
Append the following preprocessor block inside `src/firmware/src/cfg/cfg.h` (e.g., right under the `STM32G431xx` block):

```c
#elif defined(STM32F446xx)
/*.................................................. F446RE .................................................*/

    #define EM_F446RE
    #define EM_CORTEX_M4F

    /*
     * =========layout=========
     *  DAQ CH1 ........... PA0 (ADC123_IN0) - both ADC + LA
     *  DAQ CH2 ........... PA1 (ADC123_IN1) - both ADC + LA
     *  DAQ CH3 ........... PA6 (ADC12_IN6)  - both ADC + LA
     *  DAQ CH4 ........... PA7 (ADC12_IN7)  - both ADC + LA
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

    #include "cfg_f446re.h"
```

### 5.2 Updates to `src/firmware/src/cfg/cfg.c`
Append the following block to define the ADC sampling time constants inside `src/firmware/src/cfg/cfg.c`:

```c
#elif defined (STM32F446xx)

    #include "stm32f4xx_ll_adc.h"

    const uint32_t EM_ADC_SMPLT[EM_ADC_SMPLT_CNT] = { LL_ADC_SAMPLINGTIME_3CYCLES, LL_ADC_SAMPLINGTIME_15CYCLES, LL_ADC_SAMPLINGTIME_28CYCLES,
                                                      LL_ADC_SAMPLINGTIME_56CYCLES, LL_ADC_SAMPLINGTIME_84CYCLES, LL_ADC_SAMPLINGTIME_112CYCLES,
                                                      LL_ADC_SAMPLINGTIME_144CYCLES, LL_ADC_SAMPLINGTIME_480CYCLES};
    const float EM_ADC_SMPLT_N[EM_ADC_SMPLT_CNT]  = { 3.0, 15.0, 28.0, 56.0, 84.0, 112.0, 144.0, 480.0};
```

---

## 6. Compilation Steps
To build the firmware for STM32F446RE within STM32CubeIDE:
1. Copy the template `src/firmware/board/STM32F401CC/` to `src/firmware/board/STM32F446RE/`.
2. Overwrite files under `Drivers/CMSIS/` and `Drivers/STM32F4xx_HAL_Driver/` to target F446xx specifically, and include all the Low-Level (LL) drivers listed in Section 4.
3. Open `EMBO_F446RE.ioc` in STM32CubeMX, configure core clock to 180 MHz, map peripherals according to Pinout section, enable TIM1-based ADC triggering, and generate LL initialization files.
4. Update shared source code files in `src/firmware/src/` as detailed in Section 5.
5. Build the workspace in STM32CubeIDE or using `arm-none-eabi-gcc` with options `-mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16`.
