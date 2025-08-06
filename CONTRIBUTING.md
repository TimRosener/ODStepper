# Contributing to ODStepper

Thank you for your interest in contributing to ODStepper! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- Clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Hardware setup (microcontroller, stepper driver model, wiring)
- Code snippet demonstrating the issue
- Error messages or debug output

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- Clear and descriptive title
- Detailed explanation of the proposed feature
- Use case scenarios
- Code examples of how the feature would be used
- Any potential drawbacks or compatibility concerns

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly on actual hardware
5. Update documentation if needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

#### Pull Request Guidelines

- Keep changes focused and atomic
- Follow the existing code style
- Update the README.md if adding new features
- Add examples if introducing new functionality
- Ensure all examples compile on supported platforms
- Test on ESP32 (primary platform) and at least one other platform
- Update CHANGELOG.md with your changes

## Code Style

- Use clear, descriptive variable names
- Comment complex logic
- Keep functions focused and small
- Follow Arduino library conventions
- Maintain compatibility with FastAccelStepper API

## Testing

Before submitting:

1. Test all examples compile without warnings
2. Test on real hardware with actual stepper motors
3. Verify open-drain functionality on ESP32
4. Check standard output mode on non-ESP32 platforms
5. Test with common stepper drivers (A4988, DRV8825, TMC series)

## Documentation

- Update inline code comments
- Keep README.md examples working and up-to-date
- Document any new public methods or constants
- Add entries to keywords.txt for syntax highlighting

## Questions?

Feel free to open an issue for any questions about contributing.

## License

By contributing, you agree that your contributions will be licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).

Contributors retain copyright to their contributions but grant a license to the project maintainers for both non-commercial and commercial use.
