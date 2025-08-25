#include <WiFi.h>
#include <WebServer.h>
#include "driver/spi_slave.h"
#include "driver/gpio.h"

// ====================== WiFi ======================
const char* ssid     = "Kingno";
const char* password = "Hcd010203";

// ====================== SPI pins ==================
// Slave SPI (VSPI_HOST)
#define PIN_NUM_MISO    GPIO_NUM_19
#define PIN_NUM_MOSI    GPIO_NUM_23
#define PIN_NUM_CLK     GPIO_NUM_18
#define PIN_NUM_CS      GPIO_NUM_5
#define PIN_HANDSHAKE   GPIO_NUM_4   // báo hiệu Slave ready

// ====================== Buffers ===================
#define MAX_FRAME_SIZE      (40 * 1024)   // 40KB (dùng PSRAM)
#define SPI_RX_CHUNK        1024

static uint8_t *front_buf = nullptr;
static uint8_t *back_buf  = nullptr;

static volatile size_t front_len = 0;
static size_t back_len = 0;

// ====================== Web server ================
WebServer server(80);

// ====================== Handshake callbacks =======
static void IRAM_ATTR my_post_setup_cb(spi_slave_transaction_t *trans) {
  gpio_set_level(PIN_HANDSHAKE, 1);  // báo Master: Slave sẵn sàng
}
static void IRAM_ATTR my_post_trans_cb(spi_slave_transaction_t *trans) {
  gpio_set_level(PIN_HANDSHAKE, 0);  // xong
}

// ====================== SPI helpers ===============
bool spi_recv_exact(uint8_t* dest, size_t nbytes) {
  size_t remaining = nbytes;
  while (remaining > 0) {
    size_t this_chunk = (remaining > SPI_RX_CHUNK) ? SPI_RX_CHUNK : remaining;

    spi_slave_transaction_t t = {};
    t.length   = this_chunk * 8;
    t.rx_buffer = dest;

    esp_err_t ret = spi_slave_transmit(VSPI_HOST, &t, 1000 / portTICK_PERIOD_MS);
    if (ret != ESP_OK) {
      Serial.printf("spi_slave_transmit fail len: %d\n", this_chunk);
      return false;
    }

    dest      += this_chunk;
    remaining -= this_chunk;

    server.handleClient();
    yield();
  }
  return true;
}

bool spi_recv_length(uint32_t &out_len) {
  uint8_t len4[4] = {0};
  spi_slave_transaction_t t = {};
  t.length    = 4 * 8;
  t.rx_buffer = len4;

  esp_err_t ret = spi_slave_transmit(VSPI_HOST, &t, 1000 / portTICK_PERIOD_MS);
  if (ret != ESP_OK || t.trans_len != 32) return false;

  uint32_t L = ((uint32_t)len4[0] << 24) |
               ((uint32_t)len4[1] << 16) |
               ((uint32_t)len4[2] << 8)  |
               (uint32_t)len4[3];

  if (L == 0 || L > MAX_FRAME_SIZE) return false;
  out_len = L;
  return true;
}

void swap_buffers(size_t new_len) {
  noInterrupts();
  uint8_t *tmp = front_buf;
  front_buf = back_buf;
  back_buf  = tmp;
  front_len = new_len;
  interrupts();
}

// ====================== HTTP handlers =============
void handleRoot() {
  server.send(
    200, "text/html",
    "<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'/>"
    "<title>ESP32 SPI Camera Viewer</title>"
    "<style>body{font-family:system-ui;margin:24px} img{max-width:100%;height:auto;border-radius:12px;box-shadow:0 6px 24px rgba(0,0,0,.15)}"
    "button{padding:10px 16px;border-radius:10px;border:1px solid #ddd;background:#f7f7f7;cursor:pointer}</style>"
    "</head><body>"
    "<h2>ESP32 Slave – JPEG from ESP32-CAM</h2>"
    "<button onclick='reloadImg()'>Reload</button>"
    "<p><img id='img' src='/jpg?ts='+Date.now()></p>"
    "<script>function reloadImg(){const i=document.getElementById('img');i.src='/jpg?ts='+Date.now();} setInterval(reloadImg,1000);</script>"
    "</body></html>"
  );
}

void handleJPG() {
  if (front_len == 0) {
    server.send(200, "text/plain", "No image yet");
    return;
  }
  server.setContentLength(front_len);
  server.send(200, "image/jpeg", "");
  WiFiClient client = server.client();

  noInterrupts();
  size_t len = front_len;
  interrupts();

  client.write(front_buf, len);
}

// ====================== setup/loop =================
void setup() {
  Serial.begin(115200);
  delay(200);

  // ===== WiFi =====
  WiFi.begin(ssid, password);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print(".");
    delay(400);
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  // ===== Web server =====
  server.on("/", handleRoot);
  server.on("/jpg", handleJPG);
  server.begin();

  // ===== Buffer =====
  front_buf = (uint8_t*)ps_malloc(MAX_FRAME_SIZE);
  back_buf  = (uint8_t*)ps_malloc(MAX_FRAME_SIZE);
  if (!front_buf || !back_buf) {
    Serial.println("Malloc failed! Enable PSRAM or reduce MAX_FRAME_SIZE.");
    while (true) { delay(1000); }
  }

  // ===== SPI Slave init =====
  gpio_set_pull_mode(PIN_NUM_MOSI, GPIO_PULLUP_ONLY);
  gpio_set_pull_mode(PIN_NUM_CLK,  GPIO_PULLUP_ONLY);
  gpio_set_pull_mode(PIN_NUM_CS,   GPIO_PULLUP_ONLY);

  gpio_set_direction(PIN_HANDSHAKE, GPIO_MODE_OUTPUT);
  gpio_set_level(PIN_HANDSHAKE, 0);

  spi_bus_config_t buscfg = {};
  buscfg.mosi_io_num   = PIN_NUM_MOSI;
  buscfg.miso_io_num   = PIN_NUM_MISO;
  buscfg.sclk_io_num   = PIN_NUM_CLK;
  buscfg.quadwp_io_num = -1;
  buscfg.quadhd_io_num = -1;

  spi_slave_interface_config_t slvcfg = {};
  slvcfg.spics_io_num   = PIN_NUM_CS;
  slvcfg.flags          = 0;
  slvcfg.queue_size     = 8;  // tăng
  slvcfg.mode           = 0;
  slvcfg.post_setup_cb  = my_post_setup_cb;
  slvcfg.post_trans_cb  = my_post_trans_cb;

  esp_err_t ret = spi_slave_initialize(VSPI_HOST, &buscfg, &slvcfg, SPI_DMA_CH_AUTO);
  if (ret != ESP_OK) {
    Serial.printf("spi_slave_initialize failed: %d\n", ret);
    while (true) { delay(1000); }
  }
  Serial.println("SPI Slave ready.");
}

void loop() {
  server.handleClient();

  uint32_t frame_size = 0;
  if (!spi_recv_length(frame_size)) {
    delay(1);
    return;
  }

  if (frame_size == 0 || frame_size > MAX_FRAME_SIZE) {
    Serial.printf("Invalid frame size: %lu\n", (unsigned long)frame_size);
    return;
  }

  if (!spi_recv_exact(back_buf, frame_size)) {
    Serial.println("Payload receive failed.");
    back_len = 0;
    return;
  }
  back_len = frame_size;

  swap_buffers(back_len);
  Serial.printf("Frame ready: %u bytes\n", (unsigned)front_len);

  delay(1);
}
