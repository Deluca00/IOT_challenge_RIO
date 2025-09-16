#include <WiFi.h>
#include <Firebase_ESP_Client.h>

// ==== WiFi Config ====
const char* ssid = "DL";
const char* password = "Hnk010203";

// ==== Firebase Config ====
#define FIREBASE_HOST "https://iotclhn-default-rtdb.firebaseio.com/"
#define FIREBASE_AUTH "ryVhawVi1nxfQDrvpHV65FkvZGdUN95j9Ykyu17O"

FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

String uartData = "";

// ==== UART2 pins (ESP32) ====
#define RXD2 16   // ESP32 RX2 <- UNO TX (chân 1)
#define TXD2 17   // ESP32 TX2 -> UNO RX (chân 0)

void setup() {
  // Debug USB
  Serial.begin(9600);

  // UART2 cho UNO
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);

  // ==== Kết nối WiFi ====
  WiFi.begin(ssid, password);
  Serial.print("Connecting to Wi-Fi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Connected!");

  // ==== Firebase ====
  config.host = FIREBASE_HOST;
  config.signer.tokens.legacy_token = FIREBASE_AUTH;
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  Serial.println("ESP32 ready, waiting UART data from UNO (via Serial2)...");
}

void loop() {
  // Nhận dữ liệu từ UNO qua UART2
  if (Serial2.available()) {
    uartData = Serial2.readStringUntil('\n');
    uartData.trim();

    if (uartData.length() > 0) {
      Serial.println("Received from UNO: " + uartData);

      if (uartData == "TAKE") {
        Firebase.RTDB.setString(&fbdo, "/conveyor/status", "TAKE");
      } else if (uartData == "UNTAKE") {
        Firebase.RTDB.setString(&fbdo, "/conveyor/status", "UNTAKE");
      }
    }
  }
}
