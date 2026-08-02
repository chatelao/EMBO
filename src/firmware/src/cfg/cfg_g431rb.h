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

// GPIO EXTI mappings ----------------------------------------------------------
#define EM_GPIO_EXTI_SRC       LL_SYSCFG_SetEXTISource      // GPIO EXTI source
#define EM_GPIO_EXTI_ACTIVE_R  LL_EXTI_IsActiveFlag_0_31    // GPIO EXTI is active rising?
#define EM_GPIO_EXTI_ACTIVE_F  LL_EXTI_IsActiveFlag_0_31    // GPIO EXTI is active falling?
#define EM_GPIO_EXTI_CLEAR_R   LL_EXTI_ClearFlag_0_31       // GPIO EXTI clear rising flag
#define EM_GPIO_EXTI_CLEAR_F   LL_EXTI_ClearFlag_0_31       // GPIO EXTI clear rising flag

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
