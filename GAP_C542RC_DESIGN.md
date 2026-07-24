# Technical Design Document: Compiling EMBO for STM32C542RC (Nucleo-C542RC)

This document derives the detailed technical design, architectural specifications, and implementation blueprints for supporting the conceptual **STM32C542RC** microcontroller on the Nucleo-C542RC board under the EMBO (EMBedded Oscilloscope) project. It is based directly on the architectural requirements outlined in `GAP_C542RC_CONCEPT.md`.

---

## 1. System Architecture & Core Specifications

* **Microcontroller:** STM32C542RCT6 (ARM Cortex-M33 with FPU and TrustZone)
* **Core Frequency (HCLK):** 100 MHz
* **SRAM/Flash Size:** 64 KB SRAM / 256 KB Flash
* **Board Form Factor:** Nucleo-64 (Nucleo-C542RC)
* **On-Board Debugger:** ST-LINK/V3

### 1.1 Technical Interface & Component Interaction
EMBO firmware utilizes Low-Level (LL) drivers to bypass the HAL overhead, allowing high-speed timing and deterministic analog/digital operations.
The system block diagram below maps the interaction of the core components under the STM32C542RC design:

```
+-----------------------------------------------------------------------------------+
|                                EMBO Core Firmware                                 |
|                                                                                   |
|  +--------------------+      +--------------------+      +---------------------+  |
|  |     Oscilloscope   |      |   Logic Analyzer   |      |  Signal Generator   |  |
|  |       (DAQ)        |      |        (LA)        |      |       (SGEN)        |  |
|  +---------+----------+      +---------+----------+      +----------+----------+  |
|            |                           |                            |             |
|            v                           v                            v             |
|  +---------+----------+      +---------+----------+      +----------+----------+  |
|  |     ADC1 (DMA)     |      |    GPIO (DMA)      |      |     DAC1 (DMA)      |  |
|  +---------+----------+      +---------+----------+      +----------+----------+  |
+------------|---------------------------|----------------------------|-------------+
             |                           |                            |
             | DMA Request               | DMA Request                | DMA Request
             v                           v                            v
+-----------------------------------------------------------------------------------+
|                                 DMA & DMAMUX                                      |
|                                                                                   |
|                        +---------------------------+                              |
|                        |      DMAMUX Router        |                              |
|                        +-------------+-------------+                              |
|                                      |                                            |
|                  +-------------------+-------------------+                        |
|                  |                   |                   |                        |
|                  v                   v                   v                        |
|             DMA1 Ch 1           DMA1 Ch 2           DMA1 Ch 3                     |
|            (ADC1 DMAMUX)       (TIM1_UP DMAMUX)    (DAC1_CH1 DMAMUX)              |
+------------------|-------------------|-------------------|------------------------+
                   |                   |                   |
                   v                   v                   v
+-----------------------------------------------------------------------------------+
|                                Hardware Peripherals                               |
|                                                                                   |
|  +--------------------+      +--------------------+      +---------------------+  |
|  |    ADC1_IN0/1/6/7  |      |   GPIOA Pin IDR    |      |    DAC1_OUT1/2      |  |
|  |    (PA0,1,6,7)     |      |    (PA0,1,6,7)     |      |     (PA4, PA5)      |  |
|  +--------------------+      +--------------------+      +---------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Major Technical Decision Alternatives

To ensure high reliability, optimal resource usage, and a modular architecture, several critical hardware and software decisions were evaluated across three alternatives.

### 2.1 Timer Selection for Regular ADC Triggering (`EM_TIM_DAQ`)
* **Alternative A (Optimal - Selected):** Use **TIM1** (Advanced-Control Timer running on the fast APB2 clock domain up to 100 MHz) triggering the ADC via `TIM1_TRGO`.
  * *Why:* Provides maximum timing resolution (10 ns clock ticks), avoids conflicts with APB1 timers, and does not overlap with pins allocated to PWM or Counter peripherals.
* **Alternative B (Discarded):** Use **TIM3** (General-Purpose Timer on APB1 up to 100 MHz).
  * *Why Discarded:* While capable, TIM3 has fewer advanced triggering features than TIM1. Reserving TIM3 leaves general-purpose timer channels available for future expansions.
* **Alternative C (Discarded):** Use **TIM2** (32-bit General-Purpose Timer).
  * *Why Discarded:* TIM2 is actively mapped to the PWM CH1 (`PB10`) function. Re-using TIM2 for DAQ triggers would introduce severe functional conflicts, disabling the PWM Generator.

### 2.2 Pin Allocation & GPIO Port Mapping for DAQ/LA
* **Alternative A (Optimal - Selected):** Map both DAQ and LA to PA0, PA1, PA6, PA7 (GPIOA).
  * *Why:* Logic Analyzer captures demand all target pins to reside on a *single parallel GPIO port*. This allows a single DMA read of the GPIO Input Data Register (IDR), ensuring perfectly synchronized, simultaneous pin sampling. Placing them on GPIOA also conforms to standard Arduino Uno analog/digital header layout.
* **Alternative B (Discarded):** Map to a mixed configuration (e.g., PA0, PA1, PB0, PB1).
  * *Why Discarded:* Violates EMBO's hardware requirements. Multiple GPIO ports cannot be read simultaneously via a single DMA pass, causing channel misalignment (skew) and doubling the DMA bandwidth overhead.
* **Alternative C (Discarded):** Map to dedicated GPIOB pins (e.g., PB0, PB1, PB4, PB5).
  * *Why Discarded:* Restricts compatible pins on Nucleo-64. Most high-performance ADC channels map naturally to GPIOA, and GPIOB pins are heavily used for on-board functions like the User LED (`PB13`) and UART communications.

### 2.3 DMA Channel Routing & DMAMUX Allocation
* **Alternative A (Optimal - Selected):** Use Single DMA Controller (DMA1) with clean DMAMUX Routing (Channels 1 to 5).
  * *Why:* The DMAMUX can freely route any peripheral trigger to any DMA channel. Consolidating all EMBO functions to DMA1 channels 1-5 simplifies the interrupt framework and provides optimal performance without utilizing the auxiliary DMA2 controller, saving silicon power.
* **Alternative B (Discarded):** Use Distributed Dual Controller Mapping (DMA1 + DMA2).
  * *Why Discarded:* Spreading 5 channels across DMA1 and DMA2 unnecessarily complicates clock gating, initialization code, and interrupt service routines, without providing any practical performance benefit for the Cortex-M33 core clock speeds.
* **Alternative C (Discarded):** Rely on Legacy Direct Channel DMA mapping (bypassing DMAMUX).
  * *Why Discarded:* The STM32C5 series physically routes all DMA requests through the DMAMUX block. Bypassing it is not supported in the hardware architecture, making this option completely non-functional.

### 2.4 Clock Tree & System Frequency Configuration
* **Alternative A (Optimal - Selected):** Run HCLK/Core at 100 MHz and APB1/APB2 at 100 MHz (PLL driven), with ADCCLK running asynchronously at 50 MHz (HCLK/2).
  * *Why:* Maximizes the performance of the Cortex-M33 core, allowing faster GUI/OS processing, and enables the highest regular ADC conversion speed.
* **Alternative B (Discarded):** Run ADCCLK synchronously with APB2 (e.g., APB2 divided by 2 or 4).
  * *Why Discarded:* Limits ADC flexibility. Asynchronous clocking decouples the ADC speed from APB frequency changes, keeping regular oscilloscope sample rates constant.
* **Alternative C (Discarded):** Run a power-saving profile at HCLK = 80 MHz, ADCCLK = 40 MHz.
  * *Why Discarded:* Reduces maximum oscilloscope and logic analyzer sampling capabilities by 20%, which compromises performance on high-frequency signals.

---

## 3. Conflict-Free Pin Layout & Hardware Reference

To avoid hardware resource conflicts on the Nucleo-C542RC board:

| Function | Pin | Hardware Peripheral | DMA Controller / DMAMUX Request | Arduino Connector |
| :--- | :--- | :--- | :--- | :--- |
| **DAQ / LA CH1** | PA0 | ADC1_IN0 / GPIOA | DMA1 Channel 1 / `LL_DMAMUX_REQ_ADC1` | A0 |
| **DAQ / LA CH2** | PA1 | ADC1_IN1 / GPIOA | DMA1 Channel 1 / `LL_DMAMUX_REQ_ADC1` | A1 |
| **DAQ / LA CH3** | PA6 | ADC1_IN6 / GPIOA | DMA1 Channel 1 / `LL_DMAMUX_REQ_ADC1` | D12 |
| **DAQ / LA CH4** | PA7 | ADC1_IN7 / GPIOA | DMA1 Channel 1 / `LL_DMAMUX_REQ_ADC1` | D11 |
| **DAC CH1** | PA4 | DAC1_OUT1 | DMA1 Channel 3 / `LL_DMAMUX_REQ_DAC1_CH1` | A2 |
| **DAC CH2** | PA5 | DAC1_OUT2 | DMA1 Channel 4 / `LL_DMAMUX_REQ_DAC1_CH2` | A3 |
| **PWM CH1** | PB10 | TIM2_CH3 | None (Timer Output) | D6 |
| **PWM CH2** | PB8 | TIM4_CH3 | None (Timer Output) | D15 |
| **CNTR** | PC9 | TIM8_CH4 | DMA1 Channel 5 / `LL_DMAMUX_REQ_TIM8_UP` | D2 |
| **USART TX** | PA2 | USART2_TX | None | D1 |
| **USART RX** | PA3 | USART2_RX | None | D0 |
| **User LED** | PB13 | GPIOB Pin 13 | None | Green LED |

---

## 4. Technical Resolution of Gaps

### DMAMUX Configurations
To route peripheral signals correctly, the DMAMUX must be explicitly configured prior to enabling any DMA channels:
```c
LL_DMA_SetPeriphRequest(DMA1, LL_DMA_CHANNEL_1, LL_DMAMUX_REQ_ADC1);
LL_DMA_SetPeriphRequest(DMA1, LL_DMA_CHANNEL_2, LL_DMAMUX_REQ_TIM1_UP);
LL_DMA_SetPeriphRequest(DMA1, LL_DMA_CHANNEL_3, LL_DMAMUX_REQ_DAC1_CH1);
LL_DMA_SetPeriphRequest(DMA1, LL_DMA_CHANNEL_4, LL_DMAMUX_REQ_DAC1_CH2);
LL_DMA_SetPeriphRequest(DMA1, LL_DMA_CHANNEL_5, LL_DMAMUX_REQ_TIM8_UP);
```

### Low-Level Driver Dependencies
The following STM32CubeC5 LL driver modules must be imported into the board directory:
* **Headers (`Drivers/STM32C5xx_HAL_Driver/Inc/`):**
  - `stm32c5xx_ll_adc.h`, `stm32c5xx_ll_dac.h`, `stm32c5xx_ll_dma.h`, `stm32c5xx_ll_gpio.h`, `stm32c5xx_ll_tim.h`, etc.
* **Sources (`Drivers/STM32C5xx_HAL_Driver/Src/`):**
  - `stm32c5xx_ll_adc.c`, `stm32c5xx_ll_dac.c`, `stm32c5xx_ll_dma.c`, `stm32c5xx_ll_gpio.c`, `stm32c5xx_ll_tim.c`, etc.

---

## 5. Precise Implementation Blueprints

### 5.1 New Header File: `src/firmware/src/cfg/cfg_c542rc.h`

Create a clean, dedicated header configuration for STM32C542RC:

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

### 5.2 Shared Code Modification: `src/firmware/src/cfg/cfg.h`

To integrate the new configuration when `STM32C542xx` or `EM_C542RC` is defined, add the following block inside `src/firmware/src/cfg/cfg.h`:

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

### 5.3 Shared Code Modification: `src/firmware/src/cfg/cfg.c`

To map the ADC sampling times, add the following block inside `src/firmware/src/cfg/cfg.c`:

```c
#elif defined (STM32C542xx)

    #include "stm32c5xx_ll_adc.h"

    const uint32_t EM_ADC_SMPLT[EM_ADC_SMPLT_CNT] = { LL_ADC_SAMPLINGTIME_1CYCLE_5, LL_ADC_SAMPLINGTIME_2CYCLES_5, LL_ADC_SAMPLINGTIME_8CYCLES_5,
                                                      LL_ADC_SAMPLINGTIME_16CYCLES_5, LL_ADC_SAMPLINGTIME_32CYCLES_5, LL_ADC_SAMPLINGTIME_64CYCLES_5,
                                                      LL_ADC_SAMPLINGTIME_128CYCLES_5, LL_ADC_SAMPLINGTIME_640CYCLES_5};
    const float EM_ADC_SMPLT_N[EM_ADC_SMPLT_CNT]  = { 1.5, 2.5, 8.5, 16.5, 32.5, 64.5, 128.5, 640.5};
```

---

## 6. Build and Verification Instructions

1. **Toolchain Requirement:** Run using GCC Arm Embedded Toolchain (`arm-none-eabi-gcc`).
2. **Architecture Target Compiler Flags:**
   ```bash
   -mcpu=cortex-m33 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16
   ```
3. **Trigger Compilation Process:** Ensure that executing the central compilation python script `scripts/compile_firmware.py` works properly and does not trigger any syntax or configuration regression within other existing board builds.
