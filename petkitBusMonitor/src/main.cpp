#include <Arduino.h>
#include <Adafruit_TinyUSB.h>

#define CRC_POLY_CCITT 0x1021
#define CRC_START_CCITT_FFFF 0xFFFF

const int uart1_tx = 0; // connect to uart2_rx
const int uart1_rx = 1; // connect to uart2_tx
const int uart1_tx_alt = 12;

const int uart2_tx = 4;
const int uart2_rx = 5;
const int uart2_tx_alt = 8;

uint16_t crc_tab16[256];
bool crc_tab16_init = false;
uint16_t crc_16(const unsigned char *input_str, size_t num_bytes, uint16_t start_value);
void init_crc16_tab(void);

struct Frame
{
  uint32_t timestamp;
  uint8_t length;
  uint8_t type;
  uint8_t sequence;
  uint8_t payload[257];
  uint16_t crc;
  uint16_t calcCrc;
  uint8_t raw[257];
  bool isValid;
};

bool parseFrame(HardwareSerial &ser, Frame *frame, uint32_t timeout);
void printFrame(Frame *frame);

void setup()
{
  Serial1.setRX(uart1_rx); // start uarts with the TX pins set to alternate pins. listen only mode
  Serial1.setTX(uart1_tx_alt);

  Serial2.setRX(uart2_rx);
  Serial2.setTX(uart2_tx_alt);

  Serial1.setFIFOSize(1024);
  Serial2.setFIFOSize(1024);

  pinMode(uart1_tx, INPUT); // these pins are on the bus, set them to hi-Z
  pinMode(uart2_tx, INPUT);
  pinMode(LED_BUILTIN, OUTPUT);

  Serial.begin(115200);
  Serial1.begin(115200);
  Serial2.begin(115200);
}

void loop()
{
  uint8_t buf[128] = {0};
  if (Serial1.available())
  {

    digitalWrite(LED_BUILTIN, HIGH);
    Frame frame = {0};
    while (Serial1.available())
    {

      if (parseFrame(Serial1, &frame, 10))
      {
        Serial.print("ISD91230: ");
        printFrame(&frame);
      }
    }
    // while (Serial1.available())
    // {
    //  Serial.write(Serial1.readBytesUntil(0xaa,buf, 20));
    //}
    digitalWrite(LED_BUILTIN, LOW);
  }
  if (Serial2.available())
  {
    digitalWrite(LED_BUILTIN, HIGH);
    Frame frame = {0};
    while (Serial2.available())
    {

      if (parseFrame(Serial2, &frame, 10))
      {
        Serial.print("ESP8266: ");
        printFrame(&frame);
      }
      // while (Serial1.available())
      // {
      //  Serial.write(Serial1.readBytesUntil(0xaa,buf, 20));
      //}
    }
    digitalWrite(LED_BUILTIN, LOW);
  }
  delay(20);
}

bool parseFrame(HardwareSerial &ser, Frame *frame, uint32_t timeout)
{
  uint32_t startTime = millis();
  // uint8_t buf[128];
  ser.setTimeout(timeout);
  Frame f = {0};

  if (ser.peek() == 0xaa)
  {
    ser.read();
    if (ser.peek() == 0xaa)
    {
      f.timestamp = millis();
      f.raw[0] = (uint8_t)0xaa;
      f.raw[1] = (uint8_t)ser.read();
      f.raw[2] = (uint8_t)ser.read();
      f.length = f.raw[2];
      if(f.length >32) return false;
      ser.readBytes(&f.raw[3], f.length - 3);
      f.type = f.raw[3];
      f.sequence = f.raw[4];
      f.crc = (((uint16_t)f.raw[f.length - 2] << 8) | ((uint16_t)f.raw[f.length - 1]));
      f.raw[f.length] = '\0';
      f.calcCrc = crc_16(f.raw, f.length, CRC_START_CCITT_FFFF);
      if (f.calcCrc == 0)
        f.isValid = true;
      else
        f.isValid = false;
      memcpy(frame, &f, sizeof(Frame));
      return true;
    }
  }
  else
    ser.read();

  return false;
}

void printFrame(Frame *frame)
{
  Serial.printf("packet type: %hhu, length: %hhu, seq: %hhu, crc: %04X", frame->type, frame->length, frame->sequence, frame->crc);

  if (frame->isValid)
    Serial.print(" [Valid!], ");
  else
  {
    Serial.print(" [Bad], calc:");
    Serial.print(frame->calcCrc, HEX);
  }
  if (frame->length >= 8)
  {
    Serial.print(" Data: 0x");
    for (int i = 5; i < frame->length - 2; i++)
    {
      if (frame->raw[i] < 0xF)
        Serial.print("0");
      Serial.print(frame->raw[i], HEX);
    }
  }
  Serial.println();
}

uint16_t crc_16(const unsigned char *input_str, size_t num_bytes, uint16_t start_value)
{

  uint16_t crc;
  const unsigned char *ptr;
  size_t a;

  if (!crc_tab16_init)
    init_crc16_tab();

  crc = start_value;
  ptr = input_str;

  if (ptr != NULL)
    for (a = 0; a < num_bytes; a++)
    {

      crc = (crc << 8) ^ crc_tab16[((crc >> 8) ^ (uint16_t)*ptr++) & 0x00FF];
    }

  return crc;

} /* crc_ccitt_generic */

void init_crc16_tab(void)
{

  uint16_t i;
  uint16_t j;
  uint16_t crc;
  uint16_t c;

  for (i = 0; i < 256; i++)
  {

    crc = 0;
    c = i << 8;

    for (j = 0; j < 8; j++)
    {

      if ((crc ^ c) & 0x8000)
        crc = (crc << 1) ^ CRC_POLY_CCITT;
      else
        crc = crc << 1;

      c = c << 1;
    }

    crc_tab16[i] = crc;
  }

  crc_tab16_init = true;

} /* init_crcccitt_tab */