// ============================================================================
// ODStepper Simple Test
// Minimal test program for ODStepper with essential commands only
// 
// Hardware Configuration:
// - Step Pin: GPIO 7
// - Dir Pin: GPIO 15
// - Enable Pin: GPIO 16 (active LOW)
//
// Commands:
// a - Set acceleration
// v - Set max speed
// g - Go to position
// f - Forward
// b - Backward  
// s - Stop (with deceleration)
// e - Emergency stop (immediate)
// p - Print status
// ============================================================================

#include <ODStepper.h>

// Pin definitions
const uint8_t STEP_PIN = 7;
const uint8_t DIR_PIN = 15;
const uint8_t ENABLE_PIN = 16;  // Active LOW - driver is enabled when pin is LOW

// Create engine and stepper
ODStepperEngine engine = ODStepperEngine();
ODStepper *stepper = NULL;

// Default parameters
uint32_t currentSpeed = 1000;      // Steps per second
uint32_t currentAccel = 2000;      // Steps per second^2

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000);
  
  Serial.println(F("\n========================================"));
  Serial.println(F("      ODStepper Simple Test v1.0"));
  Serial.println(F("========================================"));
  
  // Initialize engine
  Serial.println(F("Initializing stepper engine..."));
  engine.init();
  
  // Connect stepper to step pin
  stepper = engine.stepperConnectToPin(STEP_PIN);
  if (!stepper) {
    Serial.println(F("ERROR: Failed to connect stepper!"));
    while(1);
  }
  
  // Configure pins
  stepper->setDirectionPin(DIR_PIN);
  stepper->setEnablePin(ENABLE_PIN, false); // false = active low (LOW enables the driver)
  stepper->setAutoEnable(true);
  stepper->setDelayToEnable(50);      // 50us delay after enable
  stepper->setDelayToDisable(100);    // 100ms delay before disable
  
  // Set initial parameters
  stepper->setSpeedInHz(currentSpeed);
  stepper->setAcceleration(currentAccel);
  
  Serial.println(F("✓ Stepper initialized"));
  Serial.println();
  printMenu();
}

void loop() {
  // Process serial commands
  if (Serial.available()) {
    char cmd = Serial.read();
    // Clear any extra characters
    while (Serial.available() && Serial.peek() == '\n' || Serial.peek() == '\r') {
      Serial.read();
    }
    processCommand(cmd);
  }
  
  // Print status periodically while running
  static unsigned long lastStatus = 0;
  if (stepper->isRunning() && millis() - lastStatus > 1000) {
    printQuickStatus();
    lastStatus = millis();
  }
}

void printMenu() {
  Serial.println(F("Commands:"));
  Serial.println(F("  a - Set acceleration"));
  Serial.println(F("  v - Set max speed"));
  Serial.println(F("  g - Go to position"));
  Serial.println(F("  f - Forward (continuous)"));
  Serial.println(F("  b - Backward (continuous)"));
  Serial.println(F("  s - Stop (with deceleration)"));
  Serial.println(F("  e - Emergency stop (immediate)"));
  Serial.println(F("  p - Print status"));
  Serial.println(F("  h - Show this help"));
  Serial.println(F("========================================"));
}

void processCommand(char cmd) {
  switch (cmd) {
    case 'a':
    case 'A':
      setAcceleration();
      break;
      
    case 'v':
    case 'V':
      setMaxSpeed();
      break;
      
    case 'g':
    case 'G':
      goToPosition();
      break;
      
    case 'f':
    case 'F':
      Serial.println(F("Running forward..."));
      stepper->runForward();
      break;
      
    case 'b':
    case 'B':
      Serial.println(F("Running backward..."));
      stepper->runBackward();
      break;
      
    case 's':
    case 'S':
      Serial.println(F("Stopping (deceleration)..."));
      stepper->stopMove();
      break;
      
    case 'e':
    case 'E':
      Serial.println(F("EMERGENCY STOP!"));
      stepper->forceStop();
      break;
      
    case 'p':
    case 'P':
      printDetailedStatus();
      break;
      
    case 'h':
    case 'H':
      printMenu();
      break;
      
    case '\n':
    case '\r':
      break;
      
    default:
      Serial.print(F("Unknown command: "));
      Serial.println(cmd);
  }
}

void setAcceleration() {
  Serial.print(F("Current acceleration: "));
  Serial.print(currentAccel);
  Serial.println(F(" steps/s²"));
  Serial.print(F("Enter new acceleration: "));
  
  // Clear serial buffer
  while (Serial.available()) { Serial.read(); }
  
  // Wait for input
  while (!Serial.available()) { delay(10); }
  
  // Read the value
  long newAccel = 0;
  bool validInput = true;
  
  delay(50); // Allow full number to arrive
  
  while (Serial.available()) {
    char c = Serial.read();
    if (c >= '0' && c <= '9') {
      newAccel = newAccel * 10 + (c - '0');
    } else if (c != '\n' && c != '\r' && c != ' ') {
      validInput = false;
      break;
    }
  }
  
  if (validInput && newAccel > 0) {
    currentAccel = newAccel;
    stepper->setAcceleration(currentAccel);
    Serial.print(F("Acceleration set to: "));
    Serial.print(currentAccel);
    Serial.println(F(" steps/s²"));
    
    // Apply immediately if running
    if (stepper->isRunning()) {
      stepper->applySpeedAcceleration();
      Serial.println(F("Applied to running motor"));
    }
  } else {
    Serial.println(F("Invalid input!"));
  }
}

void setMaxSpeed() {
  Serial.print(F("Current max speed: "));
  Serial.print(currentSpeed);
  Serial.println(F(" steps/s"));
  Serial.print(F("Enter new max speed: "));
  
  // Clear serial buffer
  while (Serial.available()) { Serial.read(); }
  
  // Wait for input
  while (!Serial.available()) { delay(10); }
  
  // Read the value
  long newSpeed = 0;
  bool validInput = true;
  
  delay(50); // Allow full number to arrive
  
  while (Serial.available()) {
    char c = Serial.read();
    if (c >= '0' && c <= '9') {
      newSpeed = newSpeed * 10 + (c - '0');
    } else if (c != '\n' && c != '\r' && c != ' ') {
      validInput = false;
      break;
    }
  }
  
  if (validInput && newSpeed > 0) {
    currentSpeed = newSpeed;
    stepper->setSpeedInHz(currentSpeed);
    Serial.print(F("Max speed set to: "));
    Serial.print(currentSpeed);
    Serial.println(F(" steps/s"));
    
    // Apply immediately if running
    if (stepper->isRunning()) {
      stepper->applySpeedAcceleration();
      Serial.println(F("Applied to running motor"));
    }
  } else {
    Serial.println(F("Invalid input!"));
  }
}

void goToPosition() {
  Serial.print(F("Current position: "));
  Serial.println(stepper->getCurrentPosition());
  Serial.print(F("Enter target position: "));
  
  // Clear serial buffer
  while (Serial.available()) { Serial.read(); }
  
  // Wait for input
  while (!Serial.available()) { delay(10); }
  
  // Read the value
  long targetPos = 0;
  bool negative = false;
  bool validInput = true;
  
  delay(50); // Allow full number to arrive
  
  // Check for negative sign
  if (Serial.peek() == '-') {
    negative = true;
    Serial.read();
  }
  
  while (Serial.available()) {
    char c = Serial.read();
    if (c >= '0' && c <= '9') {
      targetPos = targetPos * 10 + (c - '0');
    } else if (c != '\n' && c != '\r' && c != ' ') {
      validInput = false;
      break;
    }
  }
  
  if (validInput) {
    if (negative) targetPos = -targetPos;
    Serial.print(F("Moving to position: "));
    Serial.println(targetPos);
    stepper->moveTo(targetPos);
  } else {
    Serial.println(F("Invalid input!"));
  }
}

void printQuickStatus() {
  Serial.print(F("[Status] Pos: "));
  Serial.print(stepper->getCurrentPosition());
  Serial.print(F(" | Target: "));
  Serial.print(stepper->targetPos());
  Serial.print(F(" | Speed: "));
  Serial.print(abs(stepper->getCurrentSpeedInMilliHz()) / 1000.0);
  Serial.println(F(" Hz"));
}

void printDetailedStatus() {
  Serial.println(F("\n--- DETAILED STATUS ---"));
  
  Serial.println(F("Position:"));
  Serial.print(F("  Current: ")); 
  Serial.println(stepper->getCurrentPosition());
  Serial.print(F("  Target: ")); 
  Serial.println(stepper->targetPos());
  
  Serial.println(F("Speed:"));
  Serial.print(F("  Set speed: ")); 
  Serial.print(currentSpeed);
  Serial.println(F(" Hz"));
  Serial.print(F("  Current speed: ")); 
  Serial.print(abs(stepper->getCurrentSpeedInMilliHz()) / 1000.0);
  Serial.println(F(" Hz"));
  
  Serial.println(F("Acceleration:"));
  Serial.print(F("  Set: ")); 
  Serial.print(currentAccel);
  Serial.println(F(" steps/s²"));
  
  Serial.println(F("State:"));
  Serial.print(F("  Running: ")); 
  Serial.println(stepper->isRunning() ? "Yes" : "No");
  Serial.print(F("  Stopping: ")); 
  Serial.println(stepper->isStopping() ? "Yes" : "No");
  
  uint8_t state = stepper->rampState();
  Serial.print(F("  Ramp state: "));
  if (state & RAMP_STATE_ACCELERATE) Serial.print(F("ACCELERATING"));
  else if (state & RAMP_STATE_DECELERATE) Serial.print(F("DECELERATING"));
  else if (state & RAMP_STATE_COAST) Serial.print(F("COASTING"));
  else Serial.print(F("IDLE"));
  
  if (stepper->isRunning()) {
    if (state & RAMP_DIRECTION_COUNT_UP) Serial.print(F(" (Forward)"));
    else if (state & RAMP_DIRECTION_COUNT_DOWN) Serial.print(F(" (Backward)"));
  }
  Serial.println();
  
  Serial.println(F("--- END STATUS ---\n"));
}