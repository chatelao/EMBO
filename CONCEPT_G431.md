# Concept: Porting and Rewriting EMBO G431xx Firmware from Nucleo-32 to Nucleo-64

This document presents the high-level conceptual model, business cases, and architecture for porting and rewriting the **EMBO (EMBedded Oscilloscope)** firmware for the **STM32G431xx** family from the ultra-compact **Nucleo-32 (G431KB)** form factor to the full-featured **Nucleo-64 (G431RB)** form factor.

---

## 1. Top Goal
The primary goal is to successfully rewrite, optimize, and expand the **STM32G431xx** firmware to fully leverage the additional pins, interfaces, and user controls of the **Nucleo-64 (G431RB)** hardware platform, while maintaining backward compatibility and preserving high-performance ADC/DMA oscilloscope operations.

---

## 2. Business and Use Cases

### 2.1 Academic & Educational Laboratories
* **Wider Adoption:** The Nucleo-64 is the de facto standard form factor in engineering education due to its Arduino Uno V3 shield compatibility. Porting EMBO to Nucleo-64 enables immediate classroom adoption using existing lab infrastructure.
* **Shield Interoperability:** Students and educators can stack standard displays, sensor shields, or signal conditioners directly on top of the EMBO hardware without wire clutter.

### 2.2 Advanced Prototyping & Headless Diagnostics
* **Physical User Controls:** The addition of a dedicated physical blue User Button (B1) on Nucleo-64 enables headless mode switching, calibration triggers, or starting/stopping acquisition without requiring a PC connection.
* **Dedicated Status Indicators:** Standardizing dedicated, non-overlapping diagnostic LEDs allows for immediate, clear feedback on device states (e.g., trigger armed, sampling active, USB connected, error states).

---

## 3. High-Level Architecture & Functional Components

The system architecture consists of six top-level functional modules communicating over optimized hardware-independent business interfaces:

```
+-----------------------------------------------------------------------------+
|                                  EMBO CLIENT                                |
+-----------------------------------------------------------------------------+
                                       ^
                                       | USB / USART2
                                       v
+-----------------------------------------------------------------------------+
|                            EMBO NUCLEO-64 FIRMWARE                          |
+-----------------------------------------------------------------------------+
|  +--------------------+  +--------------------+  +--------------------+     |
|  |   Communications   |  |   Scope / DAQ      |  |   Logic Analyzer   |     |
|  |   (USB & USART)    |  | (ADC, DMA, Timers) |  |   (GPIO, Timers)   |     |
|  +--------------------+  +--------------------+  +--------------------+     |
|                                                                             |
|  +--------------------+  +--------------------+  +--------------------+     |
|  |  Signal Generator  |  |   PWM Generator    |  |  HMI / User I/O    |     |
|  |     (DAC, DMA)     |  |    (Timers, PWM)   |  |  (LEDs & Buttons)  |     |
|  +--------------------+  +--------------------+  +--------------------+     |
+-----------------------------------------------------------------------------+
```

### 3.1 Functional Component Interfaces
* **Communications Interface:** Handles connection handshakes (`*IDN?`, `SYS:LIM?`, `SYS:INFO?`) and schedules bulk data uploads to the EMBO PC client.
* **DAQ Interface:** Configures sampling rates, registers channels, triggers DMA-based ADC captures, and routes interleaved streams.
* **LA Interface:** Captures multi-channel digital states concurrently via timed GPIO port IDR register direct memory access (DMA).
* **Signal Generator Interface:** Sets wave type, amplitude, and frequency for the DAC outputs.
* **PWM Interface:** Sets duty cycles and frequencies for the square-wave generator.
* **HMI Interface:** Polls button states and controls keepalive/breathing indicator LEDs.

---

## 4. Hardware Mapping Comparison Table

| Feature / Pin | Nucleo-32 (G431KB) Pin | Nucleo-64 (G431RB) Pin | Technical Notes / Constraint Check |
|---|---|---|---|
| **Form Factor** | LQFP32 | LQFP64 | RB has double the pins, allowing isolated peripheral mapping. |
| **DAQ CH1 / LA CH1** | PA0 | PA0 | Kept on GPIOA to preserve single-port parallel IDR DMA capture. |
| **DAQ CH2 / LA CH2** | PA1 | PA1 | Kept on GPIOA to preserve single-port parallel IDR DMA capture. |
| **DAQ CH3 / LA CH3** | PA6 | PA6 | Kept on GPIOA to preserve single-port parallel IDR DMA capture. |
| **DAQ CH4 / LA CH4** | PA7 | PA7 | Kept on GPIOA to preserve single-port parallel IDR DMA capture. |
| **DAC CH1 (SGEN 1)** | PA4 | PA4 | Dedicated high-impedance analog output pin. |
| **DAC CH2 (SGEN 2)** | PA5 | PA5 | **Conflict Pin on Nucleo-64 (shares with onboard LD2).** |
| **User LED (EM_LED)** | PB8 | PB13 (Remapped) | Remapped to avoid conflict with DAC CH2 on PA5. |
| **User Button (B1)** | None | PC13 | Mapped to blue onboard button for interactive triggers. |
| **VCP UART RX / TX** | PA2 / PA3 | PA2 / PA3 | Connected to ST-LINK V3 virtual COM port on both boards. |
| **USB DM / DP** | PA11 / PA12 | PA11 / PA12 | USB Full Speed hardware pins. |

---

## 5. Major Choices & Alternatives

### 5.1 Major Choice 1: User LED & DAC1_OUT2 Conflict on PA5
On the Nucleo-64 G431RB, the onboard User LED (LD2) is hardwired to `PA5`. However, EMBO utilizes `PA5` as **DAC1_OUT2 (Signal Generator Channel 2)**. Statically mapping both to the same pin introduces visual noise (LED flashing rapidly during signal generation) and adds an unwanted capacitive load to the analog signal.

* **Alternative A (Selected): Remap EMBO Indicator LED to an unused pin (e.g., PB13).**
  * *Description:* Disable the onboard LD2 (PA5) from EMBO's firmware LED driver and remap the software logical LED (`EM_LED`) to a different, conflict-free physical pin such as `PB13`.
  * *Reasoning:* This maintains absolute signal integrity for the analog generator (DAC CH2) while keeping full indicator LED features intact (using an external LED on PB13 or another pin).
* **Alternative B: Shared Co-existence on PA5.**
  * *Description:* Leave PA5 configured for both the LED and DAC1_OUT2.
  * *Reasoning:* While easy, this induces heavy signal distortion on DAC Channel 2 due to the LED's pull-down resistor and diode capacitance, degrading SGEN performance.
* **Alternative C: Disable Signal Generator Channel 2.**
  * *Description:* Completely disable DAC Channel 2 to free up PA5 for the onboard LD2.
  * *Reasoning:* This unnecessarily reduces EMBO's functional capabilities (reducing it to a single-channel signal generator).

---

### 5.2 Major Choice 2: Virtual COM Port (VCP) UART configuration
The PC client relies on a reliable serial connection for control signals. We must choose the optimal hardware UART routing on the Nucleo-64.

* **Alternative A (Selected): Maintain USART2 on PA2/PA3.**
  * *Description:* Continue using `USART2` mapped to `PA2`/`PA3`, which is directly routed through the ST-LINK debugger's VCP on the Nucleo-64 board.
  * *Reasoning:* Provides the simplest, out-of-the-box user experience without requiring custom jumper wires on the board.
* **Alternative B: Move to LPUART1 on PC4/PC5.**
  * *Description:* Remap communication to the Low Power UART (LPUART1) using PC4/PC5.
  * *Reasoning:* Frees up PA2/PA3 for general GPIO/analog use but requires custom hardware modifications on the Nucleo SB (Solder Bridge) resistors to route to the VCP.
* **Alternative C: Pure USB-only Connection (Disable UART entirely).**
  * *Description:* Rely exclusively on the onboard STM32 USB FS peripheral.
  * *Reasoning:* Saves pins but removes USART fallback capabilities, which is critical for systems with complex USB topologies or environments where USB stack debugging is active.

---

### 5.3 Major Choice 3: DAQ / LA Pin Mapping for High-Speed DMA Reads
The Logic Analyzer (LA) requires concurrent, single-cycle sampling of digital states across multiple pins.

* **Alternative A (Selected): Keep All 4 Channels on GPIOA (PA0, PA1, PA6, PA7).**
  * *Description:* Maintain the original GPIO port alignment where all four input channels reside on the same GPIO port (`GPIOA`).
  * *Reasoning:* This allows the DMA engine to capture the state of all 4 pins simultaneously using a single DMA transaction reading the `GPIOA->IDR` register, eliminating synchronization skew.
* **Alternative B: Scatter Channels across Ports (GPIOA/GPIOB/GPIOC).**
  * *Description:* Re-route channels to different ports based on the physical pin order of the Arduino connectors.
  * *Reasoning:* While visually cleaner on physical boards, this requires multiple DMA streams or software polling, introducing significant timing skew and reducing the maximum sampling rate of the Logic Analyzer by several orders of magnitude.
* **Alternative C: Expand to a Dedicated 8-channel Single-port Layout (PC0-PC7).**
  * *Description:* Expand the LA to 8 channels by dedicating an entire contiguous byte of `GPIOC` (PC0 to PC7) for digital sampling.
  * *Reasoning:* Increases scope of the analyzer but breaks hardware backwards compatibility with the Nucleo-32 G431KB and requires significant modifications to the shared EMBO codebase which expects 4-channel configurations.

---

## 6. Summary of Discarded Alternatives

* **Shared Co-existence on PA5 (5.1-B):** Discarded because analog signal integrity on DAC CH2 is of paramount importance. The capacitive and resistive loading of the LED circuit would distort high-frequency waveforms.
* **Disable Signal Generator Channel 2 (5.1-C):** Discarded as it violates the principle of maximum feature preservation during porting.
* **Move to LPUART1 on PC4/PC5 (5.2-B):** Discarded due to high barrier to entry for end users who would need to solder or configure physical jumpers on their Nucleo boards.
* **Pure USB-only Connection (5.2-C):** Discarded because USART2 provides a robust, fail-safe communication interface that is invaluable for early-stage boot diagnostics.
* **Scatter Channels across Ports (5.3-B):** Discarded because it breaks the fundamental timing synchronization of the Logic Analyzer DMA engine.
* **Expand to a Dedicated 8-channel Single-port Layout (5.3-C):** Discarded because it requires extensive, non-standard updates to the EMBO desktop application and shared core firmware, increasing technical debt.
