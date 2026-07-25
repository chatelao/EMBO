/*
 * CTU/EMBO - EMBedded Oscilloscope <github.com/parezj/EMBO>
 * Author: Jakub Parez <parez.jakub@gmail.com>
 */
 
#include "cfg.h"

#ifdef EM_LED

#include "led.h"
#include "main.h"

#ifndef EMBO
    #define EM_LED_PORT            GPIOB    // main LED port
    #define EM_LED_PIN             3        // main LED pin
    #define EM_LED_INVERTED                 // inverted behavior
#endif

void led_init(led_data_t* self)
{
    self->ms = 0;
    self->num = 0;
    self->enabled = EM_FALSE;
    self->uwtick_first = 0;
    self->pwm_cnt = 0;
    self->duty = 0;
    self->breath_cnt = 0;
    self->breath_dir = 1;
}

void led_set(led_data_t* self, uint8_t enable)
{
    self->enabled = enable;

    #ifdef EM_LED_INVERTED
        if (self->enabled == EM_FALSE)
            #if defined(STM32F446xx)
                EM_LED_PORT->BSRR |= (1 << (EM_LED_PIN + 16));  // 1
            #else
                EM_LED_PORT->BRR |= (1 << EM_LED_PIN);  // 1
            #endif
        else
            EM_LED_PORT->BSRR |= (1 << EM_LED_PIN);   // 0
    #else
        if (self->enabled == EM_FALSE)
            EM_LED_PORT->BSRR |= (1 << EM_LED_PIN);  // 1
        else
            #if defined(STM32F446xx)
                EM_LED_PORT->BSRR |= (1 << (EM_LED_PIN + 16));   // 0
            #else
                EM_LED_PORT->BRR |= (1 << EM_LED_PIN);   // 0
            #endif
    #endif
}

void led_toggle(led_data_t* self)
{
    if (self->enabled == EM_TRUE)
        EM_LED_PORT->BSRR |= (1 << EM_LED_PIN);  // 1
    else
        #if defined(STM32F446xx)
            EM_LED_PORT->BSRR |= (1 << (EM_LED_PIN + 16));   // 0
        #else
            EM_LED_PORT->BRR |= (1 << EM_LED_PIN);   // 0
        #endif
    self->enabled = !self->enabled;
}

void led_blink_set(led_data_t* self, int num, int ms, uint32_t _uwTick)
{
    self->num = (num * 2) - 1;
    #ifdef EM_LED_INVERTED
        self->num++;
    #endif
    self->ms = ms;
    self->uwtick_first = _uwTick;
    led_set(self, 1);
}

void led_blink_do(led_data_t* self, uint32_t _uwTick)
{
    if (self->num > 0)
    {
        int diff;
        if (_uwTick >= self->uwtick_first)
            diff = _uwTick - self->uwtick_first;
        else
            diff = (_uwTick - self->uwtick_first) + 4294967295;

        if (diff >= self->ms)
        {
            self->uwtick_first = _uwTick;
            self->num--;
            led_toggle(self);
        }
    }
    else
    {
        // Keepalive breathing effect using software PWM, gated by 1ms tick updates
        if (_uwTick != self->uwtick_first)
        {
            self->uwtick_first = _uwTick;

            self->pwm_cnt++;
            if (self->pwm_cnt >= 10)
            {
                self->pwm_cnt = 0;
            }

            self->breath_cnt++;
            if (self->breath_cnt >= 150) // 150 ticks * 1ms = 150ms per duty level
            {
                self->breath_cnt = 0;
                if (self->breath_dir)
                {
                    self->duty++;
                    if (self->duty >= 9)
                    {
                        self->duty = 9;
                        self->breath_dir = 0;
                    }
                }
                else
                {
                    self->duty--;
                    if (self->duty <= 0)
                    {
                        self->duty = 0;
                        self->breath_dir = 1;
                    }
                }
            }

            if (self->pwm_cnt < self->duty)
            {
                led_set(self, 1);
            }
            else
            {
                led_set(self, 0);
            }
        }
    }
}
#endif
