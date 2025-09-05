#include <Arduino.h>

// ==== KHAI BÁO CHÂN RELAY ====
#define RELAY1 3
#define RELAY2 2
#define RELAY3 4
#define RELAY4 5
#define RELAYmotor 12

// ==== KHAI BÁO CHÂN CẢM BIẾN HỒNG NGOẠI ====
#define SENSOR1 6
#define SENSOR2 7
#define SENSOR3 8
#define SENSOR4 9

// ==== KHAI BÁO CẢM BIẾN SIÊU ÂM ====
const int trigPin = 11;
const int echoPin = 10;

// ==== KHAI BÁO STEPPER ====
#define STEP_PIN A0   // STEP
#define DIR_PIN  A1   // DIR
#define EN_PIN   A2   // ENABLE

const int quarterTurn = 600;   // 90° = 600 step
const int speedDelay = 1200;   // tốc độ (µs)

const int distanceThreshold = 14; // Ngưỡng phát hiện (cm)
bool moved = false;               // Cờ tránh lặp liên tục

// ================== SETUP ==================
void setup() {
  Serial.begin(9600);

  // Relay
  pinMode(RELAY1, OUTPUT);
  pinMode(RELAY2, OUTPUT);
  pinMode(RELAY3, OUTPUT);
  pinMode(RELAY4, OUTPUT);
  pinMode(RELAYmotor, OUTPUT);

  // Cảm biến hồng ngoại
  pinMode(SENSOR1, INPUT);
  pinMode(SENSOR2, INPUT);
  pinMode(SENSOR3, INPUT);
  pinMode(SENSOR4, INPUT);

  // Stepper
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);
  pinMode(EN_PIN, OUTPUT);
  digitalWrite(EN_PIN, LOW);  // bật driver

  // Tắt hết relay ban đầu
  digitalWrite(RELAY1, LOW);
  digitalWrite(RELAY2, LOW);
  digitalWrite(RELAY3, LOW);
  digitalWrite(RELAY4, LOW);
  digitalWrite(RELAYmotor, LOW);

    // Ultrasonic
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}


// ================== HÀM QUAY STEPPER ==================
void stepMotor(int steps, int dir, int delayTime) {
  digitalWrite(DIR_PIN, dir);
  for (int i = 0; i < steps; i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(delayTime);
  }
}

// ================== HÀM ĐỌC CẢM BIẾN HỒNG NGOẠI + ĐIỀU KHIỂN RELAY ==================
void readInfraSensors() {
  int s1 = digitalRead(SENSOR1);
  int s2 = digitalRead(SENSOR2);
  int s3 = digitalRead(SENSOR3);
  int s4 = digitalRead(SENSOR4);

  Serial.print("S1="); Serial.print(s1);
  Serial.print(" | S2="); Serial.print(s2);
  Serial.print(" | S3="); Serial.print(s3);
  Serial.print(" | S4="); Serial.println(s4);

  digitalWrite(RELAY1, (s1 == 0) ? HIGH : LOW);
  digitalWrite(RELAY2, (s2 == 0) ? HIGH : LOW);
  digitalWrite(RELAY3, (s3 == 0) ? HIGH : LOW);
  digitalWrite(RELAY4, (s4 == 0) ? HIGH : LOW);

  if (s1 == 0) Serial.println("Motor1 STOP by Sensor");
  if (s2 == 0) Serial.println("Motor2 STOP by Sensor");
  if (s3 == 0) Serial.println("Motor3 STOP by Sensor");
  if (s4 == 0) Serial.println("Motor4 STOP by Sensor");
}

// ================== HÀM ĐỌC CẢM BIẾN SIÊU ÂM ==================
long readUltrasonicDistance() {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW); 

  long duration = pulseIn(echoPin, HIGH);
  long distance = duration * 0.034 / 2; // cm
  return distance;
}

// ================== HÀM ĐIỀU KHIỂN STEPPER ==================
void controlStepper(long distance) {
  if (!moved && distance > 0 && distance < distanceThreshold) {
    delay(1000);
    digitalWrite(RELAYmotor, HIGH);
    Serial.println("Bang chuyen STOP");

    // Quay 0° -> 90°
    stepMotor(quarterTurn, HIGH, speedDelay); delay(500);
    stepMotor(quarterTurn, HIGH, speedDelay); delay(500);
    // Quay 90° -> 180°
    stepMotor(quarterTurn, HIGH, speedDelay); delay(500);
    stepMotor(quarterTurn, HIGH, speedDelay); delay(500);

    // Quay 180° -> 90°
    stepMotor(quarterTurn, LOW, speedDelay); delay(500);
    stepMotor(quarterTurn, LOW, speedDelay); delay(500);
    stepMotor(quarterTurn, LOW, speedDelay); delay(500);
    // Quay 90° -> 0°
    stepMotor(quarterTurn, LOW, speedDelay); delay(500);

    moved = true; // Đánh dấu đã quay xong 1 lần
  }

  // Reset khi vật rời đi
  if (distance >= distanceThreshold) {
    moved = false;
    digitalWrite(RELAYmotor, LOW);
    Serial.println("Bang chuyen BAT");
  }
}

// ================== LOOP ==================
void loop() {
  // 1. Đọc và xử lý cảm biến hồng ngoại
  readInfraSensors();

  // 2. Đọc cảm biến siêu âm + điều khiển stepper
  long distance = readUltrasonicDistance();
  Serial.print("Khoang cach: "); Serial.print(distance); Serial.println(" cm");
  controlStepper(distance);

  delay(200);
}
