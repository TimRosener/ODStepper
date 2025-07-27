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
