#include <Servo.h>

Servo trigger;
Servo rotor;

int rotor_angle;

void write_to_rotor(int angle) {
  rotor.attach(10);

  if (angle > 180) angle = 180;
  if (angle <   0) angle =   0;
  rotor_angle = angle;
  rotor.write(rotor_angle);
  
  delay(200);
  rotor.detach();
}

void setup() {
  Serial.begin(9600);

  trigger.attach(9);  // attaches the servo on pin 9 to the servo object
  trigger.write(135);

  write_to_rotor(90);
}

void pull_the_trigger() {
  trigger.write(0);
  delay(500);
  trigger.write(135);
}

void loop() {
  int byte = Serial.read();
  switch (byte) {
    case 't': pull_the_trigger(); break;
    case 'r':
      int rotation;
      do {
        rotation = Serial.read();
      } while (rotation == -1);
      rotation -= 45;
      write_to_rotor(rotor_angle + rotation);
      break;
  }
}
