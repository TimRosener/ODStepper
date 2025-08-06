# Publishing ODStepper to Arduino Library Manager

This guide outlines the steps to publish and maintain the ODStepper library.

## Pre-flight Checklist

Before publishing, ensure:
- [x] library.properties has correct author information
- [x] library.json has correct author information for PlatformIO
- [x] LICENSE file has correct copyright holder
- [x] README.md has correct GitHub URLs
- [ ] All examples compile without errors on target platforms
- [x] Documentation is complete and accurate
- [x] No sensitive information in code
- [ ] Version number is appropriate (semantic versioning)

## Repository Structure Verification

Ensure the following files are present and up to date:
- `ODStepper.h` - Main library header
- `README.md` - Comprehensive documentation
- `LICENSE` - MIT License with correct copyright
- `library.properties` - Arduino library metadata
- `library.json` - PlatformIO metadata
- `keywords.txt` - Syntax highlighting for Arduino IDE
- `examples/SimpleTest/SimpleTest.ino` - Basic usage example
- `.gitignore` - Excludes unnecessary files

## Testing Before Release

1. **Test on ESP32 (Primary Platform)**
   - Verify open-drain functionality works correctly
   - Test with common stepper drivers (A4988, DRV8825, TMC2208)
   - Verify pull-up resistors work as expected

2. **Test on AVR Platforms**
   - Arduino Uno/Mega
   - Verify fallback to standard output mode
   - Ensure examples compile without errors

3. **Test Examples**
   - SimpleTest: Basic motion control
   - ComprehensiveTest: All features (if available)

## Version Management

Current version: 1.0.0

When updating:
- **Patch version (1.0.x)**: Bug fixes, documentation updates
- **Minor version (1.x.0)**: New features, backward compatible
- **Major version (x.0.0)**: Breaking changes

Update version in:
- `library.properties`
- `library.json`
- Tag in git

## Git Commands for Release

```bash
# Ensure all changes are committed
git add .
git commit -m "Prepare for v1.0.0 release"

# Create and push tag
git tag -a v1.0.0 -m "Initial release - Open-drain wrapper for FastAccelStepper"
git push origin main
git push origin v1.0.0
```

## Submit to Arduino Library Manager

1. Go to https://github.com/arduino/library-registry/issues/new/choose
2. Select "Submit Library" template
3. Fill in:
   - Library name: ODStepper
   - Library URL: https://github.com/TimRosener/ODStepper
   - Category: Device Control

## After Publishing

- Monitor the submission issue for feedback
- Address any requested changes promptly
- Once approved, library will be available in Arduino IDE within 24-48 hours

## Maintenance

- Respond to issues and pull requests
- Keep FastAccelStepper dependency updated
- Test with new Arduino core releases
- Update documentation as needed

## PlatformIO Registry

The library will automatically be available on PlatformIO registry once it's public on GitHub with proper library.json file.

Users can install with:
```ini
lib_deps = 
    https://github.com/TimRosener/ODStepper
```

Or after Arduino Library Manager approval:
```ini
lib_deps = 
    ODStepper
```
