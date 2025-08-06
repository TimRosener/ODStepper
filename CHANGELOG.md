# Changelog

All notable changes to the ODStepper library will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-XX

### Added
- Initial release (CC BY-NC 4.0 - Non-commercial use only)
- Automatic open-drain pin configuration for ESP32 platforms
- Full compatibility with FastAccelStepper API
- SimpleTest example with interactive serial commands
- Comprehensive documentation and wiring guide
- Support for multiple platforms (ESP32, AVR, etc.)
- PlatformIO support via library.json

### Features
- Zero-overhead wrapper implementation
- Platform-aware pin configuration
- Type aliases for easy migration from FastAccelStepper
- Detailed hardware requirements documentation
- Pull-up resistor guidance for proper operation

### Supported Platforms
- ESP32 (with native open-drain support)
- AVR (Arduino Uno, Mega, etc.) with standard output mode
- Other Arduino-compatible platforms with fallback support

[1.0.0]: https://github.com/TimRosener/ODStepper/releases/tag/v1.0.0
