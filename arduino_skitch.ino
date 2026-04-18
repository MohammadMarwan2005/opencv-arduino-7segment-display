#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

#define SERVO_COUNT 7
#define SERVO_MIN 150
#define SERVO_MAX 400
#define SEG_ON  180
#define SEG_OFF 0

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

int servoAngles[SERVO_COUNT];
String input = "";  // serial input buffer


// ---------- Utility ----------

int angleToPulse(int angle) {
  return map(angle, 0, 180, SERVO_MIN, SERVO_MAX);
}


// ---------- Initialization ----------

void initServos() {
  pwm.begin();
  pwm.setPWMFreq(50);
  for (int i = 0; i < SERVO_COUNT; i++) {
    servoAngles[i] = -1;
  }
}


// ---------- Core Control ----------

void setServoAngle(int channel, int angle) {
  if (channel < 0 || channel >= SERVO_COUNT) return;
  angle = constrain(angle, 0, 180);
  if (servoAngles[channel] == angle) return;
  servoAngles[channel] = angle;
  pwm.setPWM(channel, 0, angleToPulse(angle));
}

void setAllServos(int angle) {
  for (int i = 0; i < SERVO_COUNT; i++) {
    setServoAngle(i, angle);
  }
}


// ---------- Display ----------

void displayDigit(int digit) {
  if (digit < 0 || digit > 9) return;

  const bool digits[10][7] = {
    {1,1,1,1,1,1,0}, // 0
    {0,1,1,0,0,0,0}, // 1
    {1,1,0,1,1,0,1}, // 2
    {1,1,1,1,0,0,1}, // 3
    {0,1,1,0,0,1,1}, // 4
    {1,0,1,1,0,1,1}, // 5
    {1,0,1,1,1,1,1}, // 6
    {1,1,1,0,0,0,0}, // 7
    {1,1,1,1,1,1,1}, // 8
    {1,1,1,1,0,1,1}  // 9
  };

  for (int i = 0; i < 7; i++) {
    setServoAngle(i, digits[digit][i] ? SEG_ON : SEG_OFF);
  }
}


// ---------- Input Handling ----------

void processInput(String data) {
  int commaIndex = data.indexOf(',');
  if (commaIndex == -1) return;

  int left  = data.substring(0, commaIndex).toInt();
  int right = data.substring(commaIndex + 1).toInt();

  displayDigit(left + right);
}

void handleSerial() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      processInput(input);
      input = "";
    } else {
      input += c;
    }
  }
}

// ---------- Count forever ----------

void infiniteCount() {
    for (int i = 0; i <= 9; i++) {
      displayDigit(i);  // directly control servos for digit
      delay(500);
  }
}

// ---------- Arduino ----------

void setup() {
  Serial.begin(9600);
  initServos();
}

void loop() {
  handleSerial();

  // if you want to just count on the 7 segments without, just uncomment this line
  // infiniteCount();
}
