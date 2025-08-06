/*
 * ODStepper - Open-Drain Stepper Motor Library
 * Copyright (c) 2024 Rose&Swan
 * 
 * This work is licensed under the Creative Commons Attribution-NonCommercial 4.0 
 * International License. You may use, share, and adapt this work for 
 * non-commercial purposes only, provided you give appropriate credit.
 * 
 * For commercial use, please contact: tim@rosener.com
 * 
 * Full license: https://creativecommons.org/licenses/by-nc/4.0/
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.
 */

#ifndef ODSTEPPER_H
#define ODSTEPPER_H

// Override PIN_OUTPUT macro BEFORE including FastAccelStepper
#ifdef ARDUINO_ARCH_ESP32
  // ESP32 has native open-drain support
  #define PIN_OUTPUT(pin, value)      \
    {                                 \
      digitalWrite(pin, (value));     \
      pinMode(pin, OUTPUT_OPEN_DRAIN);\
    }
#else
  // For other platforms, use standard output
  // Note: External pull-up resistors required for open-drain operation
  #define PIN_OUTPUT(pin, value)  \
    {                             \
      digitalWrite(pin, (value)); \
      pinMode(pin, OUTPUT);       \
    }
#endif

// Now include the original FastAccelStepper library
#include <FastAccelStepper.h>

// Create aliases for ODStepper
typedef FastAccelStepperEngine ODStepperEngine;
typedef FastAccelStepper ODStepper;

#endif // ODSTEPPER_H