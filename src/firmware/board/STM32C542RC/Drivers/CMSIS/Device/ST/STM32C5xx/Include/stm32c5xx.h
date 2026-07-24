/**
  ******************************************************************************
  * @file    stm32c5xx.h
  * @author  MCD Application Team
  * @brief   CMSIS STM32C5xx Device Peripheral Access Layer Header File.
  *
  *          The file is the unique include file that the application programmer
  *          is using in the C source code, usually in main.c. This file contains:
  *           - Configuration section that allows to select:
  *              - The STM32C5xx device used in the target application
  *              - To use or not the peripherals drivers in application code(i.e.
  *                code will be based on direct access to peripherals registers
  *                rather than drivers API), this option is controlled by
  *                "#define USE_HAL_DRIVER"
  *
  ******************************************************************************
  * @attention
  *
  * <h2><center>&copy; Copyright (c) 2019 STMicroelectronics.
  * All rights reserved.</center></h2>
  *
  * This software component is licensed by ST under BSD 3-Clause license,
  * the "License"; You may not use this file except in compliance with the
  * License. You may obtain a copy of the License at:
  *                        opensource.org/licenses/BSD-3-Clause
  *
  ******************************************************************************
  */

/** @addtogroup CMSIS
  * @{
  */

/** @addtogroup stm32c5xx
  * @{
  */

#ifndef __STM32C5xx_H
#define __STM32C5xx_H

#ifdef __cplusplus
 extern "C" {
#endif /* __cplusplus */

/** @addtogroup Library_configuration_section
  * @{
  */

/**
  * @brief STM32 Family
  */
#if !defined (STM32C5)
#define STM32C5
#endif /* STM32C5 */

/* Uncomment the line below according to the target STM32C5 device used in your
   application
  */

#if !defined (STM32C542xx) && !defined (STM32C541xx) && !defined (STM32C571xx) && \
    !defined (STM32C573xx) && !defined (STM32C574xx) && !defined (STM32C584xx) && \
    !defined (STM32GBK1CB) && !defined (STM32C591xx) && !defined (STM32C5A1xx)
  /* #define STM32C542xx */   /*!< STM32C542xx Devices */
  /* #define STM32C541xx */   /*!< STM32C541xx Devices */
  /* #define STM32C571xx */   /*!< STM32C571xx Devices */
  /* #define STM32C573xx */   /*!< STM32C573xx Devices */
  /* #define STM32C583xx */   /*!< STM32C583xx Devices */
  /* #define STM32C574xx */   /*!< STM32C574xx Devices */
  /* #define STM32C584xx */   /*!< STM32C584xx Devices */
  /* #define STM32C591xx */   /*!< STM32C591xx Devices */
  /* #define STM32C5A1xx */   /*!< STM32C5A1xx Devices */
  /* #define STM32GBK1CB */   /*!< STM32GBK1CB Devices */
#endif

/*  Tip: To avoid modifying this file each time you need to switch between these
        devices, you can define the device in your toolchain compiler preprocessor.
  */
#if !defined  (USE_HAL_DRIVER)
/**
 * @brief Comment the line below if you will not use the peripherals drivers.
   In this case, these drivers will not be included and the application code will
   be based on direct access to peripherals registers
   */
  /*#define USE_HAL_DRIVER */
#endif /* USE_HAL_DRIVER */

/**
  * @brief CMSIS Device version number V1.2.0
  */
#define __STM32C5_CMSIS_VERSION_MAIN   (0x01U) /*!< [31:24] main version */
#define __STM32C5_CMSIS_VERSION_SUB1   (0x02U) /*!< [23:16] sub1 version */
#define __STM32C5_CMSIS_VERSION_SUB2   (0x00U) /*!< [15:8]  sub2 version */
#define __STM32C5_CMSIS_VERSION_RC     (0x00U) /*!< [7:0]  release candidate */
#define __STM32C5_CMSIS_VERSION        ((__STM32C5_CMSIS_VERSION_MAIN << 24)\
                                       |(__STM32C5_CMSIS_VERSION_SUB1 << 16)\
                                       |(__STM32C5_CMSIS_VERSION_SUB2 << 8 )\
                                       |(__STM32C5_CMSIS_VERSION_RC))

/**
  * @}
  */

/** @addtogroup Device_Included
  * @{
  */

#if defined(STM32C542xx)
  #include "stm32c542xx.h"
#elif defined(STM32C541xx)
  #include "stm32c541xx.h"
#elif defined(STM32C571xx)
  #include "stm32c571xx.h"
#elif defined(STM32C573xx)
  #include "stm32c573xx.h"
#elif defined(STM32C583xx)
  #include "stm32c583xx.h"
#elif defined(STM32C574xx)
  #include "stm32c574xx.h"
#elif defined(STM32C584xx)
  #include "stm32c584xx.h"
#elif defined(STM32C591xx)
  #include "stm32c591xx.h"
#elif defined(STM32C5A1xx)
  #include "stm32c5a1xx.h"
#elif defined(STM32GBK1CB)
  #include "stm32gbk1cb.h"
#else
  #error "Please select first the target STM32C5xx device used in your application (in stm32c5xx.h file)"
#endif

/**
  * @}
  */

/** @addtogroup Exported_types
  * @{
  */
typedef enum
{
  RESET = 0,
  SET = !RESET
} FlagStatus, ITStatus;

typedef enum
{
  DISABLE = 0,
  ENABLE = !DISABLE
} FunctionalState;
#define IS_FUNCTIONAL_STATE(STATE) (((STATE) == DISABLE) || ((STATE) == ENABLE))

typedef enum
{
  SUCCESS = 0,
  ERROR = !SUCCESS
} ErrorStatus;

/**
  * @}
  */


/** @addtogroup Exported_macros
  * @{
  */
#define SET_BIT(REG, BIT)     ((REG) |= (BIT))

#define CLEAR_BIT(REG, BIT)   ((REG) &= ~(BIT))

#define READ_BIT(REG, BIT)    ((REG) & (BIT))

#define CLEAR_REG(REG)        ((REG) = (0x0))

#define WRITE_REG(REG, VAL)   ((REG) = (VAL))

#define READ_REG(REG)         ((REG))

#define MODIFY_REG(REG, CLEARMASK, SETMASK)  WRITE_REG((REG), (((READ_REG(REG)) & (~(CLEARMASK))) | (SETMASK)))

#define POSITION_VAL(VAL)     (__CLZ(__RBIT(VAL)))


/**
  * @}
  */

#if defined (USE_HAL_DRIVER)
 #include "stm32c5xx_hal.h"
#endif /* USE_HAL_DRIVER */

#ifdef __cplusplus
}
#endif /* __cplusplus */

#endif /* __STM32C5xx_H */
/**
  * @}
  */

/**
  * @}
  */




/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
