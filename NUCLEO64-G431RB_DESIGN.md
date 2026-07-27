# Detailed Design: Porting and Rewriting EMBO G431xx Firmware from Nucleo-32 to Nucleo-64 (STM32G431RB)

This document derives the detailed technical specifications, register configurations, peripheral layouts, and code blueprints to port the EMBO (EMBedded Oscilloscope) firmware from the ultra-compact **Nucleo-32 (STM32G431KB)** form factor to the full-featured **Nucleo-64 (STM32G431RB)** form factor.

---

## 1. Top Goal & Objectives

The primary objective of the **STM32G431RB (Nucleo-64)** detailed design is to:
* **Preserve High-Performance Acquisition:** Maintain backward-compatible, dual-channel high-speed interleaved ADC sampling (up to 5 MSPS per channel) and single-cycle DMA-based Logic Analyzer sampling.
* **Resolve Hardware Conflicts:** Remap conflicting on-board LED and analog pins to ensure waveform signal integrity and correct visual diagnostic feedbacks.
* **Introduce Physical Interactions:** Integrate the blue onboard user button (B1) on `PC13` to enable headless control mode switches and local calibrations.
* **Define Low-Level (LL) Architecture:** Establish concrete macro structures, interrupt routing configurations, DMAMUX assignments, and memory properties.
* **Ensure Robust Button Debouncing:** Specify concrete, tick-gated hardware interrupt mechanisms to filter mechanical bounce without using CPU pooling or dynamic resources.

---

## 2. Core Tech Stack and Tech Choices

The implementation choices are selected to minimize CPU overhead, eliminate memory allocation bottlenecks, and maximize sample throughput:

* **Microcontroller (MCU):** STM32G431RBT6 (ARM Cortex-M4 with FPU, LQFP64, 150 MHz HCLK, 32 KB SRAM, 128 KB Flash).
* **Driver Architecture:** STM32 Low-Level (LL) Drivers (avoiding the high-overhead HAL layer for high-frequency operations).
* **Operating System:** FreeRTOS Kernel.
  * *Allocation Policy:* Static allocation only (`configSUPPORT_STATIC_ALLOCATION = 1`, `configSUPPORT_DYNAMIC_ALLOCATION = 0`).
  * *Heap Size:* 0 KB (no heap file included in the build tree).
* **Toolchain:** ARM GNU Embedded Toolchain (`arm-none-eabi-gcc` 10+), compiled with `-fcommon` to resolve duplicate global symbols, such as `comm_ptr`.

---

## 3. High-Level Architecture & Components Flow

Below is the PlantUML architecture diagram depicting the technical component interactions, data routes, and interfaces.

```
@startuml
skinparam Monochrome true
skinparam shadowing false

package "EMBO PC Client" {
  [PC Application (Qt5/C++)] as Client
}

package "STM32G431RB Firmware" {
  [Communications Module] as Comm
  [DAQ / Scope Module] as DAQ
  [Logic Analyzer (LA)] as LA
  [Signal Generator (SGEN)] as SGEN
  [PWM Generator] as PWM
  [HMI / User IO] as HMI

  database "Static Memory Buffers" as RAM {
    [Raw DAQ / LA Buffer (8.8 KB)] as Buff
  }
}

package "STM32G431RB Hardware" {
  [USART2 / USB FS] as PortComm
  [ADC1 & ADC2] as HardwareADC
  [DMA1 & DMAMUX] as HardwareDMA
  [TIM15 & EXTI] as HardwareTIM
  [DAC1 Channel 1 & 2] as HardwareDAC
  [TIM2 & TIM4] as HardwarePWM
  [GPIOB Pin 13 (User LED)] as HardwareLED
  [GPIOC Pin 13 (User Button)] as HardwareBtn
}

' External Interface Connections
Client <==> PortComm : USB / VCP Handshake
PortComm <==> Comm : Interrupt / Poll RX

' Internal Interfaces and Control Flows
Comm --> DAQ : Configures / Triggers
Comm --> LA : Configures / Triggers
Comm --> SGEN : Sets Freq / Amplitude
Comm --> PWM : Sets Duty / Period
HMI --> DAQ : Hardware Trigger / Calibration

' DMA & HW Routing
DAQ ==> HardwareADC : Dual Interleaved Capture
LA ==> HardwareTIM : EXTI Pin Edge Capture
HardwareADC ==> HardwareDMA : CDR Master Reads
HardwareDMA ==> Buff : Writes Direct Memory Access
SGEN ==> HardwareDAC : DMA DAC1_OUT1/2 Wave Generation
PWM ==> HardwarePWM : Timer PWM Generation
HMI ==> HardwareLED : Breathing PWM / Blink Controls
HardwareBtn ==> HMI : EXTI13 Falling Edge ISR

@enduml
```

---

## 4. Hardware Mapping, Memory, and Registers

### 4.1 Memory Properties
* **Flash Sector Organization:** 128 KB total, divided into 64 pages of 2 KB each.
* **SRAM Allocation:** 32 KB total continuous RAM.
  * *DAQ Raw Buffer:* 8.8 KB (`8800` bytes) assigned dynamically depending on active channel count.
  * *FreeRTOS Tasks:* Minimal static stacks (128 words for system tasks, 512 words for communications task).

### 4.2 System Clocks & Timer Configuration
To drive maximum performance without exceeding peripheral specifications, the clock tree is configured as:
* **SYSCLK / HCLK:** 150 MHz (sourced from PLL).
* **APB1 Clock (PCLK1):** 150 MHz.
* **APB2 Clock (PCLK2):** 150 MHz.
* **ADCCLK:** 60 MHz (derived asynchronously from PLL, ensuring precise and jitter-free sampling).
* **System Tick:** 1000 Hz.

### 4.3 Hardware Pin Configuration & Alternate Functions (AF)

| Pin Name | Pin Number | AF Pin Name | AF Code / Driver Configuration | Purpose / Feature |
|---|---|---|---|---|
| **PA0** | 14 | ADC1_IN1 | `LL_GPIO_MODE_ANALOG` | DAQ Scope Channel 1 / LA Channel 1 |
| **PA1** | 15 | ADC1_IN2 | `LL_GPIO_MODE_ANALOG` | DAQ Scope Channel 2 / LA Channel 2 |
| **PA2** | 16 | USART2_TX | `LL_GPIO_MODE_ALTERNATE` (AF7) | VCP Serial Communication (Transmit) |
| **PA3** | 17 | USART2_RX | `LL_GPIO_MODE_ALTERNATE` (AF7) | VCP Serial Communication (Receive) |
| **PA4** | 20 | DAC1_OUT1 | `LL_GPIO_MODE_ANALOG` | Signal Generator Channel 1 |
| **PA5** | 21 | DAC1_OUT2 | `LL_GPIO_MODE_ANALOG` | Signal Generator Channel 2 |
| **PA6** | 22 | ADC2_IN3 | `LL_GPIO_MODE_ANALOG` | DAQ Scope Channel 3 / LA Channel 3 |
| **PA7** | 23 | ADC2_IN4 | `LL_GPIO_MODE_ANALOG` | DAQ Scope Channel 4 / LA Channel 4 |
| **PA8** | 41 | TIM1_CH1 | `LL_GPIO_MODE_ALTERNATE` (AF1) | Frequency Counter (Direct Input) |
| **PA11** | 44 | USB_DM | `LL_GPIO_MODE_ALTERNATE` (AF14) | USB Full Speed (Data Minus) |
| **PA12** | 45 | USB_DP | `LL_GPIO_MODE_ALTERNATE` (AF14) | USB Full Speed (Data Plus) |
| **PA15** | 50 | TIM2_CH1 | `LL_GPIO_MODE_ALTERNATE` (AF1) | PWM Output Channel 1 |
| **PB6** | 58 | TIM4_CH1 | `LL_GPIO_MODE_ALTERNATE` (AF2) | PWM Output Channel 2 |
| **PB13** | 34 | GPIO_Output | `LL_GPIO_MODE_OUTPUT` | Remapped Active-Low User LED (`EM_LED`) |
| **PC13** | 2 | EXTI13 | `LL_GPIO_MODE_INPUT` / EXTI13 | Blue User Button (B1) for Headless Mode |

---

## 5. Technical Implementation Details & Code Blueprints

### 5.1 DMAMUX and DMA Channel Layout
To prevent peripheral channel overlaps, the G431RB uses the DMAMUX router mapped to standard DMA channels as:
* `DMA1 Channel 1` -> **ADC1 Regular** (DMAMUX Request 5 - `LL_DMAMUX_REQ_ADC1`)
* `DMA1 Channel 2` -> **Logic Analyzer GPIOR IDR** (DMAMUX Request 80 - `LL_DMAMUX_REQ_TIM15_CH1`)
* `DMA1 Channel 3` -> **ADC2 Regular** (DMAMUX Request 36 - `LL_DMAMUX_REQ_ADC2`)
* `DMA1 Channel 4` -> **DAC1 Channel 1** (DMAMUX Request 6 - `LL_DMAMUX_REQ_DAC1_CH1`)
* `DMA1 Channel 5` -> **DAC1 Channel 2** (DMAMUX Request 7 - `LL_DMAMUX_REQ_DAC1_CH2`)
* `DMA1 Channel 6` -> **Frequency Counter Direct Capture** (DMAMUX Request 42 - `LL_DMAMUX_REQ_TIM1_CH1`)
* `DMA2 Channel 1` -> **Frequency Counter Indirect Capture** (DMAMUX Request 43 - `LL_DMAMUX_REQ_TIM1_CH2`)

### 5.2 Board Configuration Blueprint: `cfg_g431rb.h`
The board configuration header file resolves peripheral setup, register boundaries, and pins routing:

```c
/*
 * CTU/EMBO - EMBedded Oscilloscope <github.com/parezj/EMBO>
 * Configuration for STM32G431RB Nucleo-64
 */

#ifndef INC_CFG_CFG_G431RB_H_
#define INC_CFG_CFG_G431RB_H_

#if defined(EM_G431RB)

#include "stm32g431xx.h"

// Device Properties -----------------------------------------------------------
#define EM_DEV_NAME            "EMBO-STM32G431RB-Nucleo64"
#define EM_DEV_COMM            "USB + USART2 (115200 bps)"
#define EM_LL_VER              "1.3.0"

// Pin Labeling ----------------------------------------------------------------
#define EM_PINS_SCOPE_VM       "A0-A1-A6-A7"
#define EM_PINS_LA             "A0-A1-A6-A7"
#define EM_PINS_CNTR           "A8"
#define EM_PINS_PWM            "A15-B6"
#define EM_PINS_SGEN           "A4-A5"

// Stack Allocations (Static FreeRTOS) ----------------------------------------
#define EM_STACK_MIN           128
#define EM_STACK_T1            128
#define EM_STACK_T2            128
#define EM_STACK_T3            128
#define EM_STACK_T4            512
#define EM_STACK_T5            128

// Interrupt Prioritization ----------------------------------------------------
#define EM_IT_PRI_CNTR         4
#define EM_IT_PRI_ADC          5
#define EM_IT_PRI_EXTI         5
#define EM_IT_PRI_UART         6
#define EM_IT_PRI_USB          7
#define EM_IT_PRI_SYST         15

// Clock Frequencies (Hz) ------------------------------------------------------
#define EM_FREQ_LSI            40000
#define EM_FREQ_HCLK           150000000
#define EM_FREQ_ADCCLK         60000000
#define EM_FREQ_PCLK1          150000000
#define EM_FREQ_PCLK2          150000000
#define EM_SYSTICK_FREQ        1000

// UART Communication ----------------------------------------------------------
#define EM_UART                USART2
#define EM_UART_RX_IRQHandler  USART2_IRQHandler
#define EM_UART_CLEAR_FLAG(x)  LL_USART_ClearFlag_RTO(x)
#define EM_USB
#define EM_UART_POLLINIT

// Remapped Diagnostic LED (Avoids DAC CH2 Pin Conflict on PA5) ----------------
#define EM_LED
#define EM_LED_PORT            GPIOB
#define EM_LED_PIN             13
#define EM_LED_INVERTED

// Physical User Button (B1) Integration ---------------------------------------
#define EM_BTN_PORT            GPIOC
#define EM_BTN_PIN             13
#define EM_BTN_IRQ_LINE        LL_EXTI_LINE_13
#define EM_BTN_IRQ_HANDLER     EXTI15_10_IRQHandler

// Dual Signal Generator (DAC) -------------------------------------------------
#define EM_DAC                 DAC1
#define EM_DAC_CH              LL_DAC_CHANNEL_1
#define EM_DAC_SRC             LL_DAC_TRIG_EXT_TIM6_TRGO
#define EM_DAC2                DAC1
#define EM_DAC2_CH             LL_DAC_CHANNEL_2
#define EM_DAC2_SRC            LL_DAC_TRIG_EXT_TIM7_TRGO
#define EM_DAC_BUFF_LEN        1000
#define EM_DAC_MAX_VAL         4095.0
#define EM_DAC_TIM_MAX_F       4500000

// DAQ Hardware Allocations ----------------------------------------------------
#define EM_DAQ_4CH
#define EM_ADC_MODE_ADC12
#define EM_ADC_BIT12
#define EM_ADC_BIT8
#define EM_ADC_INTERLEAVED
#define EM_ADC_DUALMODE

#define EM_VREF                3300
#define EM_ADC_VREF_CAL        *((uint16_t*)VREFINT_CAL_ADDR)
#define EM_ADC_VREF_CALVAL     3.0
#define EM_ADC_SMPLT_MAX       LL_ADC_SAMPLINGTIME_2CYCLES_5
#define EM_ADC_SMPLT_MAX_N     2.5
#define EM_ADC_TCONV8          8.5
#define EM_ADC_TCONV12         12.5
#define EM_ADC_C_F             0.000000000005
#define EM_ADC_R_OHM           1000.0
#define EM_ADC_SMPLT_CNT       8
#define EM_ADC_LINREG
#define EM_ADC_DEEPPWD
#define EM_ADC_SEQ_CONF
#define EM_ADC_AWD             LL_ADC_AWD1,
#define EM_ADC_EN_TICKS        LL_ADC_DELAY_CALIB_ENABLE_ADC_CYCLES

// Timers ----------------------------------------------------------------------
#define EM_TIM_DAQ             TIM15
#define EM_TIM_DAQ_MAX         65535
#define EM_TIM_DAQ_FREQ        EM_FREQ_PCLK1
#define EM_TIM_DAQ_CC(a)       a##CC1
#define EM_TIM_PWM1            TIM2
#define EM_TIM_PWM1_MAX        65535
#define EM_TIM_PWM1_FREQ       EM_FREQ_PCLK1
#define EM_TIM_PWM1_CH         LL_TIM_CHANNEL_CH1
#define EM_TIM_PWM1_CHN(a)     a##CH1
#define EM_TIM_PWM2            TIM4
#define EM_TIM_PWM2_MAX        65535
#define EM_TIM_PWM2_FREQ       EM_FREQ_PCLK1
#define EM_TIM_PWM2_CH         LL_TIM_CHANNEL_CH1
#define EM_TIM_PWM2_CHN(a)     a##CH1
#define EM_TIM_CNTR            TIM1
#define EM_TIM_CNTR_FREQ       EM_FREQ_PCLK2
#define EM_TIM_CNTR_UP_IRQh    TIM1_UP_TIM16_IRQHandler
#define EM_TIM_CNTR_MAX        65535
#define EM_TIM_CNTR_CH         LL_TIM_CHANNEL_CH1
#define EM_TIM_CNTR_CH2        LL_TIM_CHANNEL_CH2
#define EM_TIM_CNTR_CCR        CCR1
#define EM_TIM_CNTR_CCR2       CCR3
#define EM_TIM_CNTR_CC(a)      a##CC1
#define EM_TIM_CNTR_CC2(a)     a##CC2
#define EM_TIM_CNTR_OVF(a)     a##CH3
#define EM_TIM_CNTR_PSC_FAST   8
#define EM_TIM_SGEN            TIM6
#define EM_TIM_SGEN_FREQ       EM_FREQ_PCLK1
#define EM_TIM_SGEN_MAX        65535
#define EM_TIM_SGEN2           TIM7
#define EM_TIM_SGEN2_FREQ      EM_FREQ_PCLK1
#define EM_TIM_SGEN2_MAX       65535

// Memory Capacity Boundaries --------------------------------------------------
#define EM_DAQ_MAX_MEM         8800
#define EM_LA_MAX_FS           13333333
#define EM_DAQ_MAX_B12_FS      5000000
#define EM_DAQ_MAX_B8_FS       5000000
#define EM_PWM_MAX_F           16000000
#define EM_SGEN_MAX_F          EM_DAC_TIM_MAX_F
#define EM_CNTR_MAX_F          37000000
#define EM_MEM_RESERVE         10

// ADC Layout ------------------------------------------------------------------
#define EM_ADC1                ADC1
#define EM_ADC2                ADC2
#define EM_ADC1_USED
#define EM_ADC2_USED
#define EM_ADC12_IRQh          ADC1_2_IRQHandler

// DMA Engines -----------------------------------------------------------------
#define EM_DMA_ADC1            DMA1
#define EM_DMA_ADC2            DMA1
#define EM_DMA_LA              DMA1
#define EM_DMA_CNTR            DMA1
#define EM_DMA_CNTR2           DMA2
#define EM_DMA_SGEN            DMA1
#define EM_DMA_SGEN2           DMA1

// DMAMUX Assignments ---------------------------------------------------------
#define EM_DMA_CH_ADC1         LL_DMA_CHANNEL_1
#define EM_DMA_CH_ADC2         LL_DMA_CHANNEL_3
#define EM_DMA_CH_LA           LL_DMA_CHANNEL_2
#define EM_DMA_CH_CNTR         LL_DMA_CHANNEL_6
#define EM_DMA_CH_CNTR2        LL_DMA_CHANNEL_1
#define EM_DMA_CH_SGEN         LL_DMA_CHANNEL_4
#define EM_DMA_CH_SGEN2        LL_DMA_CHANNEL_5

// Interrupt Definitions -------------------------------------------------------
#define EM_IRQN_ADC1           ADC1_2_IRQn
#define EM_IRQN_ADC2           ADC1_2_IRQn
#define EM_IRQN_UART           USART2_IRQn
#define EM_LA_IRQ_EXTI1        EXTI0_IRQn
#define EM_LA_IRQ_EXTI2        EXTI1_IRQn
#define EM_LA_IRQ_EXTI3        EXTI9_5_IRQn
#define EM_LA_IRQ_EXTI4        EXTI9_5_IRQn
#define EM_CNTR_IRQ            TIM1_UP_TIM16_IRQn
#define EM_IRQ_ADC1            EM_IRQN_ADC1
#define EM_IRQ_ADC2            EM_IRQN_ADC2

// Logic Analyzer EXTI Routing -------------------------------------------------
#define EM_LA_EXTI_PORT        LL_SYSCFG_EXTI_PORTA
#define EM_LA_EXTI1            LL_EXTI_LINE_0
#define EM_LA_EXTI2            LL_EXTI_LINE_1
#define EM_LA_EXTI3            LL_EXTI_LINE_6
#define EM_LA_EXTI4            LL_EXTI_LINE_7
#define EM_LA_EXTI_UNUSED      LL_EXTI_LINE_2
#define EM_LA_EXTILINE1        LL_SYSCFG_EXTI_LINE0
#define EM_LA_EXTILINE2        LL_SYSCFG_EXTI_LINE1
#define EM_LA_EXTILINE3        LL_SYSCFG_EXTI_LINE6
#define EM_LA_EXTILINE4        LL_SYSCFG_EXTI_LINE7
#define EM_LA_CH1_IRQh         EXTI0_IRQHandler
#define EM_LA_CH2_IRQh         EXTI1_IRQHandler
#define EM_LA_CH3_IRQh         EXTI9_5_IRQHandler
#define EM_LA_UNUSED_IRQh      EXTI2_IRQHandler

// Logic Analyzer Interrupt Subroutines ----------------------------------------
#define EM_LA_IRQ1_CH1         la_irq_ch1
#define EM_LA_IRQ2_CH2         la_irq_ch2
#define EM_LA_IRQ3_CH3         la_irq_ch3
#define EM_LA_IRQ3_CH4         la_irq_ch4

// ADC Hardware Channels -------------------------------------------------------
#define EM_ADC_AWD1            LL_ADC_AWD_CHANNEL_1_REG
#define EM_ADC_AWD2            LL_ADC_AWD_CHANNEL_2_REG
#define EM_ADC_AWD3            LL_ADC_AWD_CHANNEL_3_REG
#define EM_ADC_AWD4            LL_ADC_AWD_CHANNEL_4_REG
#define EM_ADC_CH1             LL_ADC_CHANNEL_1
#define EM_ADC_CH2             LL_ADC_CHANNEL_2
#define EM_ADC_CH3             LL_ADC_CHANNEL_3
#define EM_ADC_CH4             LL_ADC_CHANNEL_4

// ADC Ports -------------------------------------------------------------------
#define EM_GPIO_ADC_PORT1      GPIOA
#define EM_GPIO_ADC_PORT2      GPIOA
#define EM_GPIO_ADC_PORT3      GPIOA
#define EM_GPIO_ADC_PORT4      GPIOA
#define EM_GPIO_ADC_CH1        LL_GPIO_PIN_0
#define EM_GPIO_ADC_CH2        LL_GPIO_PIN_1
#define EM_GPIO_ADC_CH3        LL_GPIO_PIN_6
#define EM_GPIO_ADC_CH4        LL_GPIO_PIN_7

// Logic Analyzer Ports --------------------------------------------------------
#define EM_GPIO_LA_PORT        GPIOA
#define EM_GPIO_LA_OFFSET      0
#define EM_GPIO_LA_CH1         LL_GPIO_PIN_0
#define EM_GPIO_LA_CH2         LL_GPIO_PIN_1
#define EM_GPIO_LA_CH3         LL_GPIO_PIN_6
#define EM_GPIO_LA_CH4         LL_GPIO_PIN_7

// Logic Analyzer Pin Indices --------------------------------------------------
#define EM_GPIO_LA_CH1_NUM     0
#define EM_GPIO_LA_CH2_NUM     1
#define EM_GPIO_LA_CH3_NUM     6
#define EM_GPIO_LA_CH4_NUM     7

#endif
#endif /* INC_CFG_CFG_G431RB_H_ */
```

### 5.3 Technical Verification of PC Client Compatibility Handshake
The communications module handles the PC-to-mcu handshake. To allow standard EMBO Qt application integration, the firmwares responds with:
1. **`*IDN?` Handshake Query:**
   * Expected format: `4 comma-separated tokens` with name matching board design file and minimum firmware version matching `0.2.3`.
   * Return sequence: `CTU-FEE,EMBO-STM32G431RB-Nucleo64,0,0.2.3\r\n`
2. **`SYS:LIM?` Configuration Limits:**
   * Return sequence: `8800,5000000,5000000,13333333,16000000,4500000,37000000,3.3,4095,4095,0,3,10,0,0,0,0\r\n` (exactly 17 values corresponding to SRAM limit, max frequencies, etc.).
3. **`SYS:INFO?` Active Status Info:**
   * Return sequence: `0,0,0,0,0,0,0,0,0,0\r\n` (exactly 10 tokens representing active state parameters).

---

## 6. Major Implementation Choices and Alternatives

### 6.1 Major Choice 1: Physical LED & Pin Conflict Management on PA5

On the Nucleo-64 board, the hardwired onboard User LED (LD2) is mapped to `PA5`. However, EMBO utilizes `PA5` as the analog output for **Signal Generator Channel 2** (`DAC1_OUT2`). Direct coexistence causes visual interference and signal attenuation.

* **Alternative A (Selected): Remap Logical LED (`EM_LED`) to a Different Pin (`PB13`)**
  * *Description:* Disable onboard LD2. Map the software's logical LED function to pin `PB13`, which is unallocated on the board header.
  * *Pros:* Preserves maximum analog fidelity on DAC1_OUT2; eliminates rapid flashing and impedance mismatch.
  * *Cons:* Requires the user to connect an external LED to PB13 on the headers for visual keepalive.
* **Alternative B: Passive Coexistence with Low-Pass Filtering**
  * *Description:* Map PA5 as both DAC1_OUT2 and the User LED output, relying on an added passive series resistor and capacitor network to decouple high-frequency signal generation from the LED.
  * *Pros:* Simple configuration, utilizes onboard visual indicators out of the box.
  * *Cons:* Distorts waveform patterns at high signal frequencies (above 100 kHz); degrades DAC impedance characteristics.
* **Alternative C: Software Time-Multiplexed Sharing**
  * *Description:* Allocate PA5 dynamically. When the Signal Generator is inactive, use it as a logical LED pin. When SGEN 2 is active, disable the LED logic and output the DAC waveform.
  * *Pros:* Visual keepalive is preserved whenever SGEN is idle.
  * *Cons:* Breaks visual diagnostic feedback during waveform output sessions; creates high transient voltage spikes during mode switches.

---

### 6.2 Major Choice 2: Virtual COM Port (VCP) UART Routing on Nucleo-64

The MCU must establish communications with the ST-LINK debug interface on the Nucleo-64, which behaves as a Virtual COM Port.

* **Alternative A (Selected): Maintain USART2 mapped to PA2/PA3**
  * *Description:* Keep standard configurations routing `USART2` to `PA2`/`PA3`. This corresponds directly to the hardwired physical traces routing to the ST-LINK chip on the Nucleo-64 board.
  * *Pros:* Works out of the box with zero board physical jumpers configuration or solder changes.
  * *Cons:* Dedicates PA2 and PA3 entirely, restricting their use for general GPIO or analog inputs.
* **Alternative B: Utilize Low-Power UART (LPUART1) on PC4/PC5**
  * *Description:* Route VCP communications through `LPUART1` via pins `PC4`/`PC5`.
  * *Pros:* Frees up PA2 and PA3 for generic board expandability.
  * *Cons:* Requires hardware modifications (bridging solder points SB13 and SB14 on the Nucleo-64) to route signals to the ST-LINK.
* **Alternative C: Software Bit-banged Virtual Serial Port**
  * *Description:* Implement a software UART engine on arbitrary unallocated pins to stream communications.
  * *Pros:* Fully flexible pin layout selection.
  * *Cons:* Induces extreme CPU utilization spikes; introduces communication timing jitter under heavy FreeRTOS workloads.

---

### 6.3 Major Choice 3: Multi-channel High-Speed DAQ and LA Pins Allocation

High-speed Logic Analyzer concurrent sampling relies on a single DMA port read on the GPIOn Input Data Register (`IDR`).

* **Alternative A (Selected): Keep All 4 Channels Grouped on GPIOA (PA0, PA1, PA6, PA7)**
  * *Description:* Group Scope/LA pins entirely on `GPIOA`. The DMA controller triggers and reads `GPIOA->IDR` in a single hardware cycle.
  * *Pros:* Absolutely zero channel skew; maximum capture sampling rates up to 13.33 MSPS.
  * *Cons:* Constraints ADC channel mapping choices, as all four pins must support ADC conversion and map back to individual ADCs.
* **Alternative B: Scatter Pins Over Multiple Ports for Visual Pin Ordering**
  * *Description:* Scatter the four physical lines across different ports based on their order on standard Arduino layout connectors.
  * *Pros:* Extremely neat physical layout mapping.
  * *Cons:* Requires consecutive software-timed pin reads or multi-stream DMA, introducing massive clock skews and reducing maximum sampling frequency by 80%.
* **Alternative C: Remap LA entirely to GPIOC (PC0, PC1, PC2, PC3)**
  * *Description:* Assign `GPIOC` pins PC0-3 for logic analyzer captures and analog operations.
  * *Pros:* Frees up GPIOA entirely.
  * *Cons:* The STM32G431 ADC channels are heavily constrained; mapping PC0-3 to multiple ADCs for dual-mode interleaved execution is not supported by the internal analog switches, making high-speed interleaved scope operations impossible.

---

### 6.4 Major Choice 4: User Button (B1) Input Gating and Debouncing Strategy

To implement robust, headless mode switching and local calibration triggers, the mechanical blue User Button (B1) on `PC13` must be debounced to suppress contact bouncing transients.

* **Alternative A (Selected): EXTI Gated Hardware Interrupt with Software Threshold Gating**
  * *Description:* Route `PC13` to the `EXTI13` line. On a falling edge event, trigger the `EXTI15_10_IRQHandler`. Within this ISR, check the elapsed FreeRTOS system tick value since the last registered button press. If the elapsed time is less than a predefined threshold (e.g., 200 ms), the interrupt is discarded as contact bounce. Otherwise, process the state cycle event.
  * *Pros:* Low overhead, highly responsive, zero periodic polling.
  * *Cons:* Requires careful mapping of the `EXTI15_10` line and a global state variable to persist the last button press timestamp.
* **Alternative B: Periodic Software Polling Task**
  * *Description:* Execute a low-priority FreeRTOS HMI task that reads the input state of `PC13` every 20 ms.
  * *Pros:* Straightforward, completely isolated from EXTI configurations.
  * *Cons:* Consumes continuous processing cycles to wake up the HMI task periodically, decreasing energy efficiency.
* **Alternative C: External Hardware RC Low-Pass Filter**
  * *Description:* Add an RC low-pass filter circuit connected between the physical button and the GPIOC Pin 13 to filter out high-frequency contact bounce before it reaches the MCU input.
  * *Pros:* Clean digital square wave, absolutely zero software overhead or interrupt complexity.
  * *Cons:* Requires soldering physical components onto the developer board, hindering out-of-the-box software-only usability.

---

## 7. Technical Details for Choice 4: Button Configuration & ISR Blueprint

### 7.1 Peripheral Register Settings & Gating Logic
The selected **Alternative A** is configured programmatically through the low-level registers:
1. **Clock Enable:** Enable clock gating for `GPIOC` and `SYSCFG` peripherals in the `RCC` register block.
2. **GPIO Configuration:** Set `PC13` mode register to input (`MODER = 0x00`), with an internal pull-up (`PUPDR = 0x01`).
3. **SYSCFG EXTI Routing:** Map external interrupt line 13 to `GPIOC` by writing `0x02` to the `EXTICR4` multiplexer register.
4. **EXTI Configuration:** Enable falling-edge detection on Line 13 in the Falling Trigger Selection Register (`FTSR1`) and unmask the interrupt in the Interrupt Mask Register (`IMR1`).
5. **NVIC Configuration:** Set priority for `EXTI15_10_IRQn` to `5` (`NVIC_SetPriority`) and enable the vector (`NVIC_EnableIRQ`).

### 7.2 C Code Implementation Blueprint
The following code snippet demonstrates the implementation of the EXTI button ISR with robust software gating:

```c
#include "cfg.h"
#include "FreeRTOS.h"
#include "task.h"

// Variable to persist the last valid button press timestamp (in system ticks)
static volatile TickType_t last_button_press_ticks = 0;

// Gating threshold to filter out mechanical contact bounce (200 ms)
#define DEBOUNCE_THRESHOLD_TICKS  pdMS_TO_TICKS(200)

/**
  * @brief  Initialize GPIOC Pin 13 as Input EXTI Falling Edge Interrupt
  * @retval None
  */
void HMI_Button_Init(void)
{
    // 1. Enable AHB2/APB2 clocks for GPIOC and SYSCFG
    LL_AHB2_GRP1_EnableClock(LL_AHB2_GRP1_PERIPH_GPIOC);
    LL_APB2_GRP1_EnableClock(LL_APB2_GRP1_PERIPH_SYSCFG);

    // 2. Configure PC13 as input with internal Pull-Up
    LL_GPIO_SetPinMode(GPIOC, LL_GPIO_PIN_13, LL_GPIO_MODE_INPUT);
    LL_GPIO_SetPinPull(GPIOC, LL_GPIO_PIN_13, LL_GPIO_PULL_UP);

    // 3. Connect EXTI Line 13 to GPIOC Pin 13 via SYSCFG
    LL_SYSCFG_SetEXTISource(LL_SYSCFG_EXTI_PORTC, LL_SYSCFG_EXTI_LINE13);

    // 4. Configure EXTI Line 13: falling edge trigger & unmask
    LL_EXTI_EnableIT_0_31(LL_EXTI_LINE_13);
    LL_EXTI_EnableFallingTrig_0_31(LL_EXTI_LINE_13);

    // 5. Configure NVIC for EXTI15_10 interrupts
    NVIC_SetPriority(EXTI15_10_IRQn, NVIC_EncodePriority(NVIC_GetPriorityGrouping(), 5, 0));
    NVIC_EnableIRQ(EXTI15_10_IRQn);
}

/**
  * @brief  EXTI Line 15 to 10 Interrupt Handler (Gated Debounce)
  * @retval None
  */
void EXTI15_10_IRQHandler(void)
{
    // Check if interrupt flag on Line 13 is set
    if (LL_EXTI_IsActiveFlag_0_31(LL_EXTI_LINE_13) != RESET)
    {
        // Retrieve current system uptime in ticks (safe inside ISR)
        TickType_t current_ticks = xTaskGetTickCountFromISR();

        // Calculate ticks elapsed since the last registered press
        TickType_t elapsed_ticks = current_ticks - last_button_press_ticks;

        // Gating threshold check (reject events within DEBOUNCE_THRESHOLD_TICKS)
        if (elapsed_ticks >= DEBOUNCE_THRESHOLD_TICKS)
        {
            // Record timestamp of this valid button press
            last_button_press_ticks = current_ticks;

            // Execute the HMI state machine cycle (e.g., transition EMBO modes)
            HMI_Cycle_Operating_Mode();
        }

        // Clear the pending EXTI interrupt flag
        LL_EXTI_ClearFlag_0_31(LL_EXTI_LINE_13);
    }
}
```

---

## 8. Summary of Discarded Alternatives

* **Choice 1 (Alternative B - Passive Coexistence on PA5):** Discarded. The capacitive load of the LD2 circuit heavily distorts the DAC waveform, particularly at higher frequencies, violating the high-fidelity oscilloscope design goal.
* **Choice 1 (Alternative C - Software Time-Multiplexing on PA5):** Discarded due to lack of real-time diagnostic feedbacks during the most critical operation window (active generation).
* **Choice 2 (Alternative B - LPUART1 PC4/PC5):** Discarded because it places a high physical barrier to entry (soldering board jumpers) on end users.
* **Choice 2 (Alternative C - Software Bit-Banged Serial):** Discarded. High interrupt overhead causes task starvation and crashes FreeRTOS scheduler under maximum DAQ workloads.
* **Choice 3 (Alternative B - Scatter Pins Over Ports):** Discarded because introducing clock skew destroys the timing integrity and utility of the Logic Analyzer tool.
* **Choice 3 (Alternative C - Remap entirely to GPIOC):** Discarded due to MCU ADC-hardware routing limitations that prevent interleaved dual-ADC operation on these specific pins.
* **Choice 4 (Alternative B - Periodic Software Polling Task):** Discarded because periodic polling tasks waste valuable CPU cycles and increase power consumption when the button is inactive.
* **Choice 4 (Alternative C - External Hardware RC Filter):** Discarded because it requires physical board modifications, conflicting with our goal of maintaining seamless out-of-the-box software-only compatibility.
