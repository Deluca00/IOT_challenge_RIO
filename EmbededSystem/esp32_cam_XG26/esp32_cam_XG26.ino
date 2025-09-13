#include "esp_camera.h"
#include <WiFi.h>
#include <Firebase_ESP_Client.h>
#include <SPI.h>

// ---------------- WiFi Config ----------------
const char* ssid = "DL";
const char* password = "Hnk010203";

// ---------------- Firebase Config ----------------
#define FIREBASE_HOST "https://iotclhn-default-rtdb.firebaseio.com/"  // link DB
#define DATABASE_SECRET "ryVhawVi1nxfQDrvpHV65FkvZGdUN95j9Ykyu17O"   // database secret

FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig fbConfig;

// ---------------- Camera Config ----------------
// --- Chọn model camera ---//
#define CAMERA_MODEL_AI_THINKER
#if defined(CAMERA_MODEL_AI_THINKER)
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22
#define LED_GPIO_NUM       4   // LED FLASH
#endif
// ---------------- SPI Config ----------------
SPIClass spi(HSPI);
#define PIN_NUM_MISO 12
#define PIN_NUM_MOSI 13
#define PIN_NUM_CLK  14
#define PIN_NUM_CS   15
#define CHUNK_SIZE 512

// ---------------- Camera Init ----------------
static void init_camera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_GRAYSCALE;
  config.frame_size   = FRAMESIZE_QQVGA;
  config.jpeg_quality = 4;
  config.fb_count     = 2;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("Camera init failed!");
    while (1) delay(1000);
  }
}

// ---------------- Setup ----------------
void setup() {
  Serial.begin(115200);
  delay(1500);

  // WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Connected!");

  // Firebase init with Legacy Token
  fbConfig.host = FIREBASE_HOST;
  fbConfig.database_url = FIREBASE_HOST;
  fbConfig.signer.tokens.legacy_token = DATABASE_SECRET;
  Firebase.begin(&fbConfig, &auth);
  Firebase.reconnectWiFi(true);

  // Camera
  init_camera();

  // SPI
  spi.begin(PIN_NUM_CLK, PIN_NUM_MISO, PIN_NUM_MOSI, PIN_NUM_CS);
  pinMode(PIN_NUM_CS, OUTPUT);
  digitalWrite(PIN_NUM_CS, HIGH);

  pinMode(LED_GPIO_NUM, OUTPUT);
  digitalWrite(LED_GPIO_NUM, HIGH);

  Serial.println("ESP32-CAM ready (Firebase trigger + SPI).");
}

// ---------------- Loop ----------------
void loop() {
  // Kiểm tra lệnh capture trong Firebase
  if (Firebase.RTDB.getString(&fbdo, "/conveyor/status")) {
    String cmd = fbdo.stringData();
    if (cmd == "TAKE") {
      Serial.println("Capture command received!");

        for (int i = 0; i < 3; i++) {
        camera_fb_t *fb = esp_camera_fb_get();
        if (!fb) {
          Serial.println("Camera capture failed");
          return;
        }

      uint32_t img_len = fb->len;
      uint8_t *img_buf = fb->buf;

      // Gửi độ dài ảnh trước
      uint8_t len_le[4];
      memcpy(len_le, &img_len, 4);
      spi.beginTransaction(SPISettings(2000000, MSBFIRST, SPI_MODE0));
      digitalWrite(PIN_NUM_CS, LOW);
      spi.transferBytes(len_le, NULL, 4);
      digitalWrite(PIN_NUM_CS, HIGH);
      spi.endTransaction();
      delayMicroseconds(300);

      // Gửi dữ liệu ảnh
      uint32_t sent = 0;
      while (sent < img_len) {
        uint32_t to_send = (img_len - sent > CHUNK_SIZE) ? CHUNK_SIZE : (img_len - sent);

        spi.beginTransaction(SPISettings(2000000, MSBFIRST, SPI_MODE0));
        digitalWrite(PIN_NUM_CS, LOW);
        spi.transferBytes(img_buf + sent, NULL, to_send);
        digitalWrite(PIN_NUM_CS, HIGH);
        spi.endTransaction();

        sent += to_send;
        delayMicroseconds(300);
      }

      Serial.printf("Grayscale image sent: %lu bytes\n", (unsigned long)img_len);

      esp_camera_fb_return(fb);

      // Reset capture command về 0
      Firebase.RTDB.setString(&fbdo, "/conveyor/status", "UNTAKE");
    }
  }
  delay(300);
}
}
