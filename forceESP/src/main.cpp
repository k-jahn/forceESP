#include <HX711.h>

HX711 loadcell;

// hx711 pins
const int LOADCELL_SCK_PIN = 19;
const int LOADCELL_DOUT_PIN = 21;

// 2. Adjustment settings -- TODO Calibration
const int TARA_INIT_READINGS = 10;
const float LOADCELL_DIVIDER = 9072.6; // default cal

// led pins
const int taraLEDPin = 17;
const int measuringLEDPin = 16;
const int hx711ConnectedLEDPin = 22;
const int bleConnectedLEDPin = 23;

#include <ArduinoBLE.h>

// ENV
boolean MONITOR_STATE = false;

// names
const char *localName = "ForceESP";

// BLE
BLEService forceService("fce04277");
// BLEFloatCharacteristic forceChar("0x2723", BLERead | BLENotify);
BLEFloatCharacteristic forceChar("0x1312", BLERead | BLENotify);

BLEService commandService("cd1102");
BLEIntCharacteristic taraChar("0x1001", BLERead | BLEWrite);
BLEFloatCharacteristic calibrateChar("0x1002", BLERead | BLEWrite);
BLEBoolCharacteristic measureChar("0x1003", BLERead | BLEWrite);

void beginForceBLE()
{
  if (BLE.begin())
  {
    BLE.setLocalName(localName);

    forceService.addCharacteristic(forceChar);
    commandService.addCharacteristic(taraChar);
    commandService.addCharacteristic(calibrateChar);
    commandService.addCharacteristic(measureChar);

    BLE.setAdvertisedService(forceService);
    BLE.setAdvertisedService(commandService);

    BLE.addService(forceService);
    BLE.addService(commandService);

    BLE.advertise();
    Serial.println("BLE device active, waiting for connections...");
  }
  else
  {
    Serial.println("failed! Aborting...\n");
    while (1)
      ;
  }
}

void setup()
{
  pinMode(taraLEDPin, OUTPUT);
  pinMode(measuringLEDPin, OUTPUT);
  pinMode(bleConnectedLEDPin, OUTPUT);
  pinMode(hx711ConnectedLEDPin, OUTPUT);

  Serial.begin(115200);

  // Init HX711
  Serial.print("starting HX711...");
  loadcell.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  loadcell.set_scale(LOADCELL_DIVIDER);
  loadcell.tare(TARA_INIT_READINGS);
  Serial.print(" done");
  digitalWrite(hx711ConnectedLEDPin, HIGH);

  Serial.print("\nstarting BLE... ");
  beginForceBLE();
}

void loop()
{
  // acquire reading
  float reading;
  if (loadcell.wait_ready_timeout(2000))
  {
    reading = loadcell.get_units(1);
    if (MONITOR_STATE)
    {
      Serial.print("Weight: ");
      Serial.print(reading, 2);
    }
  }
  else
  {
    Serial.print("HX711 Error!");
    while (1)
      ;
  }

  // bluetooth
  BLEDevice central = BLE.central();

  if (central)
  {
    BLE.poll();
    if (MONITOR_STATE)
      Serial.print(" BLE connected");

    if (reading && measureChar.value())
    {
      forceChar.writeValue(reading);
    }
    if (taraChar.written())
    {
      int taraReadings = taraChar.value();

      Serial.print("\ntara, n=");
      Serial.print(taraReadings);
      Serial.print("...");
      digitalWrite(taraLEDPin, HIGH);
      loadcell.tare(taraReadings);
      digitalWrite(taraLEDPin, LOW);
      Serial.print("done\n");
    }
    if (calibrateChar.written())
    {
      float divider = calibrateChar.value();
      Serial.print("\ncalibrating: ");
      Serial.println(divider);
      loadcell.set_scale(divider);
    }
  }
  else
  {
    // deflag measurement in case of connection drop
    measureChar.writeValue(false);
  }

  digitalWrite(bleConnectedLEDPin, central ? HIGH : LOW);
  digitalWrite(measuringLEDPin, measureChar.value() ? HIGH : LOW);

  if (MONITOR_STATE)
    Serial.print('\n');
}
