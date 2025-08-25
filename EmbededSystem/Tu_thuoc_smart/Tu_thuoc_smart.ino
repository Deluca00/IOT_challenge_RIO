// ==== KHAI BÁO CHÂN RELAY ====
#define RELAY1 2
#define RELAY2 3
#define RELAY3 5
#define RELAY4 4

// ==== KHAI BÁO CHÂN CẢM BIẾN HỒNG NGOẠI ====
#define SENSOR1 6
#define SENSOR2 7
#define SENSOR3 8
#define SENSOR4 9

// Biến trạng thái motor

void setup() {
  Serial.begin(9600);

  pinMode(RELAY1, OUTPUT);
  pinMode(RELAY2, OUTPUT);
  pinMode(RELAY3, OUTPUT);
  pinMode(RELAY4, OUTPUT);

  pinMode(SENSOR1, INPUT);
  pinMode(SENSOR2, INPUT);
  pinMode(SENSOR3, INPUT);
  pinMode(SENSOR4, INPUT);

  // ban đầu tắt motor
  digitalWrite(RELAY1, LOW);
  digitalWrite(RELAY2, LOW);
  digitalWrite(RELAY3, LOW);
  digitalWrite(RELAY4, LOW);
}

void loop() {
  // In giá trị cảm biến ra Serial Monitor
  Serial.print("S1=");
  Serial.print(digitalRead(SENSOR1));
  Serial.print(" | S2=");
  Serial.print(digitalRead(SENSOR2));
  Serial.print(" | S3=");
  Serial.print(digitalRead(SENSOR3));
  Serial.print(" | S4=");
  Serial.println(digitalRead(SENSOR4));

  delay(300); // in ra mỗi 0.3 giây cho dễ đọc

  // ==== KIỂM TRA CẢM BIẾN TỰ ĐỘNG DỪNG ====
  if (digitalRead(SENSOR1) == 0) {
    digitalWrite(RELAY1, HIGH);
    Serial.println("Motor1 STOP by Sensor");
  }else{
    digitalWrite(RELAY1, LOW);
    Serial.println("Motor1 STOP by Sensor");
  }
    
    

  if (digitalRead(SENSOR2) == 0) {
    digitalWrite(RELAY2, HIGH);
    Serial.println("Motor2 STOP by Sensor");
  }else{
    digitalWrite(RELAY2, LOW);
    Serial.println("Motor1 STOP by Sensor");
  }

  if (digitalRead(SENSOR3) == 0) {
   
    digitalWrite(RELAY3, HIGH);
    Serial.println("Motor3 STOP by Sensor");
  }else{
    digitalWrite(RELAY3, LOW);
    Serial.println("Motor1 STOP by Sensor");
  }

  if (digitalRead(SENSOR4) == 0) {
    
    digitalWrite(RELAY4, HIGH);
    Serial.println("Motor4 STOP by Sensor");
  }else{
    digitalWrite(RELAY4, LOW);
    Serial.println("Motor1 STOP by Sensor");
  }
}
