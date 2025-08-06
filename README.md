# ODStepper Library

[![License: CC BY-NC 4.0](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)

A wrapper library for [FastAccelStepper](https://github.com/gin66/FastAccelStepper) that automatically configures pins for open-drain operation on ESP32 platforms.

> **⚠️ NON-COMMERCIAL USE ONLY**: This library is licensed under Creative Commons BY-NC 4.0. For commercial licensing, please contact tim@rosener.com.

## Overview

ODStepper (Open-Drain Stepper) is a lightweight wrapper that extends FastAccelStepper with automatic open-drain pin configuration. This is particularly useful when interfacing with stepper drivers that require open-drain outputs for level shifting or when using drivers with different voltage levels than your microcontroller.

## Features

- **Automatic Open-Drain Configuration**: On ESP32, all stepper pins (step, direction, enable) are automatically configured as open-drain outputs
- **Full FastAccelStepper Compatibility**: Inherits all features from FastAccelStepper including:
  - High-performance stepper control
  - Smooth acceleration/deceleration
  - Multi-stepper support
  - Non-blocking operation
  - Up to 200,000 steps/second on ESP32
- **Transparent Operation**: Use it exactly like FastAccelStepper - no API changes required
- **Platform Aware**: Falls back to normal output mode on non-ESP32 platforms

## Installation

### Arduino Library Manager
1. Open Arduino IDE
2. Go to Sketch → Include Library → Manage Libraries
3. Search for "ODStepper"
4. Click Install

### Manual Installation
1. Download the library as a ZIP file
2. Open Arduino IDE
3. Go to Sketch → Include Library → Add .ZIP Library
4. Select the downloaded ZIP file

### PlatformIO
Add to your `platformio.ini`:
```ini
lib_deps = 
    https://github.com/TimRosener/ODStepper
```

## Hardware Requirements

### Supported Platforms
- **ESP32** - Full open-drain support (recommended)
- **AVR** (Arduino Uno, Mega, etc.) - Standard output mode (requires external pull-up resistors)
- **Other platforms** - Standard output mode (requires external pull-up resistors)

### Pull-up Resistors
When using open-drain outputs, external pull-up resistors are required:
- **Typical value**: 4.7kΩ for faster rise times, and using 5V logic on the driver I will use a 1.8K resostor on the postive pin in series to the 5V rail. the GPIO attaches to the - pin. The resisitor is large enough to limit the current when the GPIO goes to Gnd. 
- **Connect between**: Each output pin and VCC of the stepper driver
- **ESP32**: Required for proper operation
- **Other platforms**: Required to simulate open-drain behavior

### Wiring Example
```
ESP32/Arduino          Pull-up         Stepper Driver
Step Pin ─────────────┬─────────────→ STEP
                      │
                     4.7kΩ
                      │
                     VCC (3.3V or 5V)

Direction Pin ────────┬─────────────→ DIR
                      │
                     4.7kΩ
                      │
                     VCC (3.3V or 5V)

Enable Pin ───────────┬─────────────→ ENABLE
                      │
                     4.7kΩ
                      │
                     VCC (3.3V or 5V)

GND ──────────────────────────────→ GND
```

## Usage

ODStepper uses the exact same API as FastAccelStepper. Simply replace `FastAccelStepper` with `ODStepper` in your code:

### Basic Example

```cpp
#include <ODStepper.h>

// Define pins
#define STEP_PIN    7
#define DIR_PIN     15
#define ENABLE_PIN  16

// Create engine and stepper
ODStepperEngine engine = ODStepperEngine();
ODStepper *stepper = NULL;

void setup() {
  // Initialize the engine
  engine.init();
  
  // Connect stepper to step pin
  stepper = engine.stepperConnectToPin(STEP_PIN);
  
  if (stepper) {
    // Configure additional pins
    stepper->setDirectionPin(DIR_PIN);
    stepper->setEnablePin(ENABLE_PIN, false); // false = active low
    
    // Enable automatic enable/disable
    stepper->setAutoEnable(true);
    
    // Set motion parameters
    stepper->setSpeedInHz(1000);       // 1000 steps/second
    stepper->setAcceleration(2000);    // 2000 steps/second²
    
    // Move 1000 steps forward
    stepper->move(1000);
  }
}

void loop() {
  // Your code here
}
```

### Advanced Example with Multiple Steppers

```cpp
#include <ODStepper.h>

ODStepperEngine engine = ODStepperEngine();
ODStepper *stepperX = NULL;
ODStepper *stepperY = NULL;

void setup() {
  engine.init();
  
  // Create two steppers
  stepperX = engine.stepperConnectToPin(7);
  stepperY = engine.stepperConnectToPin(8);
  
  // Configure both steppers
  if (stepperX) {
    stepperX->setDirectionPin(15);
    stepperX->setEnablePin(16, false);
    stepperX->setAutoEnable(true);
    stepperX->setSpeedInHz(2000);
    stepperX->setAcceleration(5000);
  }
  
  if (stepperY) {
    stepperY->setDirectionPin(17);
    stepperY->setEnablePin(18, false);
    stepperY->setAutoEnable(true);
    stepperY->setSpeedInHz(2000);
    stepperY->setAcceleration(5000);
  }
}

void loop() {
  // Coordinated movement
  if (!stepperX->isRunning() && !stepperY->isRunning()) {
    stepperX->move(1000);
    stepperY->move(500);
    delay(2000);
  }
}
```

## How It Works

ODStepper is a clever wrapper around FastAccelStepper that works by:

1. **Macro Redefinition**: Before including FastAccelStepper, ODStepper redefines the `PIN_OUTPUT` macro that FastAccelStepper uses internally
2. **Platform Detection**: On ESP32, the macro configures pins as `OUTPUT_OPEN_DRAIN`
3. **Type Aliasing**: Creates aliases so `ODStepper` and `ODStepperEngine` can be used in place of their FastAccelStepper equivalents
4. **Zero Overhead**: All changes happen at compile-time - no runtime performance impact

### Implementation Details

```cpp
// The entire implementation in ODStepper.h:

#ifdef ARDUINO_ARCH_ESP32
  // ESP32: Use native open-drain support
  #define PIN_OUTPUT(pin, value)      \
    {                                 \
      digitalWrite(pin, (value));     \
      pinMode(pin, OUTPUT_OPEN_DRAIN);\
    }
#else
  // Other platforms: Standard output (requires external pull-ups)
  #define PIN_OUTPUT(pin, value)  \
    {                             \
      digitalWrite(pin, (value)); \
      pinMode(pin, OUTPUT);       \
    }
#endif

// Include the original library
#include <FastAccelStepper.h>

// Create convenient aliases
typedef FastAccelStepperEngine ODStepperEngine;
typedef FastAccelStepper ODStepper;
```

## API Reference

ODStepper uses the complete FastAccelStepper API. For detailed API documentation, please refer to:
- [FastAccelStepper API Documentation](https://github.com/gin66/FastAccelStepper/blob/master/extras/doc/FastAccelStepper_API.md)
- [FastAccelStepper README](https://github.com/gin66/FastAccelStepper/blob/master/README.md)

### Key Methods

- `engine.init()` - Initialize the engine
- `engine.stepperConnectToPin(pin)` - Create a stepper instance
- `stepper->setDirectionPin(pin)` - Set direction pin
- `stepper->setEnablePin(pin, activeLow)` - Set enable pin
- `stepper->setSpeedInHz(speed)` - Set maximum speed
- `stepper->setAcceleration(accel)` - Set acceleration
- `stepper->move(steps)` - Move relative steps
- `stepper->moveTo(position)` - Move to absolute position
- `stepper->isRunning()` - Check if motor is moving
- `stepper->getCurrentPosition()` - Get current position

## Examples

The library includes a comprehensive example:
- **SimpleTest** - Interactive motion control with serial commands demonstrating all major features

## Why Use ODStepper?

### Level Shifting
When your microcontroller operates at 3.3V but your stepper driver requires 5V signals, open-drain outputs with pull-up resistors provide safe level shifting without additional hardware.

### Improved Compatibility
Some stepper drivers work better with open-drain signals, especially in noisy environments or with long cable runs.

### Safety
Open-drain outputs prevent potential damage from voltage mismatches or accidental short circuits.

## Troubleshooting

### Motor Not Moving
1. Check pull-up resistors are installed (4.7kΩ typical)
2. Verify wiring connections
3. Ensure common ground between microcontroller and driver
4. Check driver power supply

### Erratic Movement
1. Try different pull-up resistor values (2.2kΩ to 10kΩ)
2. Keep wires short or use shielded cables
3. Ensure solid ground connections
4. Add capacitors near the driver for power supply filtering

### Compilation Errors
- Ensure FastAccelStepper library is installed
- Use a compatible platform (ESP32 recommended)

## Dependencies

- [FastAccelStepper](https://github.com/gin66/FastAccelStepper) - The underlying stepper control library

## License

This library is released under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).

- **Free for non-commercial use**
- **Commercial use requires a license** - Contact tim@rosener.com
- You must give appropriate credit
- You may adapt and build upon this work

See LICENSE file for full details.

**Note**: FastAccelStepper (the underlying library) is MIT licensed. The non-commercial restriction applies only to the ODStepper wrapper code.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

- [gin66](https://github.com/gin66) - Creator of FastAccelStepper
- All contributors to the FastAccelStepper project

## Version History

- 1.0.0 - Initial release with open-drain support for ESP32

---

*For more information about the underlying stepper control capabilities, please visit the [FastAccelStepper repository](https://github.com/gin66/FastAccelStepper).*
