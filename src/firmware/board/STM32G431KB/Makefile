TARGET = EMBO_G431KB

DEBUG = 1
OPT = -Os

BUILD_DIR = build

C_SOURCES = \
Core/Src/main.c \
Core/Src/stm32g4xx_it.c \
Core/Src/stm32g4xx_hal_msp.c \
Core/Src/system_stm32g4xx.c \
Core/Src/syscalls.c \
Core/Src/sysmem.c \
USB_Device/App/usb_device.c \
USB_Device/App/usbd_cdc_if.c \
USB_Device/App/usbd_desc.c \
USB_Device/Target/usbd_conf.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_pcd.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_pcd_ex.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_ll_usb.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_rcc.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_rcc_ex.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_flash.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_flash_ex.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_flash_ramfunc.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_gpio.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_exti.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_dma.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_dma_ex.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_pwr.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_pwr_ex.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_cortex.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_tim.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_hal_tim_ex.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_ll_utils.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_ll_exti.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_ll_gpio.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_ll_adc.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_ll_dma.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_ll_rcc.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_ll_tim.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_ll_usart.c \
Drivers/STM32G4xx_HAL_Driver/Src/stm32g4xx_ll_dac.c \
Middlewares/ST/STM32_USB_Device_Library/Core/Src/usbd_core.c \
Middlewares/ST/STM32_USB_Device_Library/Core/Src/usbd_ctlreq.c \
Middlewares/ST/STM32_USB_Device_Library/Core/Src/usbd_ioreq.c \
Middlewares/ST/STM32_USB_Device_Library/Class/CDC/Src/usbd_cdc.c \
../../src/os/event_groups.c \
../../src/os/portable/M4F/port.c \
../../src/os/croutine.c \
../../src/os/tasks.c \
../../src/os/queue.c \
../../src/os/stream_buffer.c \
../../src/os/timers.c \
../../src/os/list.c \
../../src/app/app_sync.c \
../../src/app/periph/periph_adc.c \
../../src/app/periph/periph_dma.c \
../../src/app/app.c \
../../src/app/app_data.c \
../../src/app/pwm/pwm.c \
../../src/app/led/led.c \
../../src/app/irq.c \
../../src/app/comm/comm_irq.c \
../../src/app/comm/comm_proto.c \
../../src/app/comm/comm.c \
../../src/app/sgen/sgen.c \
../../src/app/daq/daq_irq.c \
../../src/app/daq/daq.c \
../../src/app/daq/daq_trig.c \
../../src/app/cntr/cntr.c \
../../src/app/cntr/cntr_irq.c \
../../src/cfg/cfg.c \
../../src/cfg/SEGGER_SYSVIEW_Config_FreeRTOS.c \
../../src/util/str.c \
../../src/util/util.c \
../../src/util/circ.c \
../../src/lib/scpi/src/minimal.c \
../../src/lib/scpi/src/lexer.c \
../../src/lib/scpi/src/units.c \
../../src/lib/scpi/src/fifo.c \
../../src/lib/scpi/src/ieee488.c \
../../src/lib/scpi/src/expression.c \
../../src/lib/scpi/src/parser.c \
../../src/lib/scpi/src/error.c \
../../src/lib/scpi/src/utils.c \
../../src/lib/SEGGER.SystemView/SEGGER_SYSVIEW_FreeRTOS.c \
../../src/lib/SEGGER.SystemView/SEGGER_RTT_printf.c \
../../src/lib/SEGGER.SystemView/SEGGER_RTT.c \
../../src/lib/SEGGER.SystemView/SEGGER_SYSVIEW.c \
../../src/lib/SEGGER.SystemView/SEGGER_RTT_Syscalls_GCC.c

ASM_SOURCES = \
Core/Startup/startup_stm32g431kbtx.s

PREFIX = arm-none-eabi-
CC = $(PREFIX)gcc
AS = $(PREFIX)gcc -x assembler-with-cpp
CP = $(PREFIX)objcopy
SZ = $(PREFIX)size
HEX = $(CP) -O ihex
BIN = $(CP) -O binary -S

CPU = -mcpu=cortex-m4
FPU = -mfpu=fpv4-sp-d16
FLOAT-ABI = -mfloat-abi=hard
MCU = $(CPU) -mthumb $(FPU) $(FLOAT-ABI)

C_DEFS = \
-DSTM32G431xx \
-DUSE_HAL_DRIVER \
-DUSE_FULL_LL_DRIVER

C_INCLUDES = \
-I../../src/app \
-I../../src/cfg \
-I../../src/lib \
-I../../src/lib/scpi/inc \
-I../../src/lib/SEGGER.SystemView \
-I../../src/os/include \
-I../../src/os/portable/M4F \
-I../../src/util \
-ICore/Inc \
-IDrivers/STM32G4xx_HAL_Driver/Inc \
-IDrivers/STM32G4xx_HAL_Driver/Inc/Legacy \
-IDrivers/CMSIS/Device/ST/STM32G4xx/Include \
-IDrivers/CMSIS/Include \
-IUSB_Device/App \
-IUSB_Device/Target \
-IMiddlewares/ST/STM32_USB_Device_Library/Core/Inc \
-IMiddlewares/ST/STM32_USB_Device_Library/Class/CDC/Inc

CFLAGS = $(MCU) $(C_DEFS) $(C_INCLUDES) $(OPT) -Wall -fdata-sections -ffunction-sections -fcommon

ifeq ($(DEBUG), 1)
CFLAGS += -g -gdwarf-2 -DDEBUG
endif

ASFLAGS = $(MCU) $(AS_DEFS) $(AS_INCLUDES) $(OPT) -Wall -fdata-sections -ffunction-sections

LDSCRIPT = STM32G431KBTX_FLASH.ld

LIBS = -lc -lm -lnosys
LIBDIR =
LDFLAGS = $(MCU) -specs=nano.specs -T$(LDSCRIPT) $(LIBDIR) $(LIBS) -Wl,-Map=$(BUILD_DIR)/$(TARGET).map,--gc-sections

all: $(BUILD_DIR)/$(TARGET).elf $(BUILD_DIR)/$(TARGET).hex $(BUILD_DIR)/$(TARGET).bin

OBJECTS = $(addprefix $(BUILD_DIR)/,$(notdir $(C_SOURCES:.c=.o)))
vpath %.c $(sort $(dir $(C_SOURCES)))

OBJECTS += $(addprefix $(BUILD_DIR)/,$(notdir $(ASM_SOURCES:.s=.o)))
vpath %.s $(sort $(dir $(ASM_SOURCES)))

$(BUILD_DIR)/%.o: %.c Makefile | $(BUILD_DIR)
	$(CC) -c $(CFLAGS) -Wa,-a,-ad,-al=$(@:.o=.lst) $< -o $@

$(BUILD_DIR)/%.o: %.s Makefile | $(BUILD_DIR)
	$(AS) -c $(ASFLAGS) $< -o $@

$(BUILD_DIR)/$(TARGET).elf: $(OBJECTS) Makefile
	$(CC) $(OBJECTS) $(LDFLAGS) -o $@
	$(SZ) $@

$(BUILD_DIR)/%.hex: $(BUILD_DIR)/%.elf | $(BUILD_DIR)
	$(HEX) $< $@

$(BUILD_DIR)/%.bin: $(BUILD_DIR)/%.elf | $(BUILD_DIR)
	$(BIN) $< $@

$(BUILD_DIR):
	mkdir $@

clean:
	rm -fR $(BUILD_DIR)
