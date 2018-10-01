#include "HX711_ADC.h"

//HX711 constructor (dout pin, sck pin)
HX711_ADC LoadCell(10, 11);

long t;



void setup() {
  Serial.begin(115200);
  Serial.println("#Wait...");
  LoadCell.begin();
  long stabilisingtime = 2000; // tare preciscion can be improved by adding a few seconds of stabilising time
  LoadCell.start(stabilisingtime);
  LoadCell.setCalFactor(1); // return raw data by default
  Serial.println("#Startup + tare complete");
}

void loop() {
  //update() should be called at least as often as HX711 sample rate; >10Hz@10SPS, >80Hz@80SPS
  //longer delay in scetch will reduce effective sample rate (be carefull with delay() in loop)
  LoadCell.update();

  //get smoothed value from data set + current calibration factor
  if (millis() > t + 60) {
    float i = LoadCell.getData();
    Serial.println(i);
    t = millis();
  }

  //receive from serial terminal
  if (Serial.available() > 0) {
    float i;
    char inByte = Serial.read();
    if (inByte == 't') {
      LoadCell.tareNoDelay();
      Serial.println("#tare request set");
    }
    if (inByte == 'c'){
      int parsedInt = Serial.parseInt();
      Serial.println("#calibration complete at " + String(parsedInt));
      LoadCell.setCalFactor(parsedInt);
    }
  }

  //check if last tare operation is complete
  if (LoadCell.getTareStatus() == true) {
    Serial.println("#tare complete at " + String(LoadCell.getTareOffset()));
  }
}
