#include <Servo.h>

Servo horizontal;
Servo vertical;
Servo trigger;


int pos = 0;
int x = 0;
int y = 0;
int horizontal_pos;
int vertical_pos;

int greenLed = 13;
int redLed = 12;
int greenBtn = 7;
int redBtn = 8;

bool mode = false;

int rotor_angle;

void write_to_rotor(int angle) {
  horizontal.attach(9);

  if (angle > 180) angle = 180;
  if (angle < 0) angle = 0;
  rotor_angle = angle;
  horizontal.write(rotor_angle);
  
  delay(200);
  horizontal.detach();
}

void pull_the_trigger() {
  trigger.write(0);
  delay(500);
  trigger.write(135);
}

void setup()
{
  Serial.begin(9600);
  pinMode(greenLed, OUTPUT);
  pinMode(redLed, OUTPUT);
  pinMode(greenBtn, INPUT);
  pinMode(redBtn, INPUT);

  horizontal.attach(9);
  vertical.attach(10);
  trigger.attach(11);

  horizontal.write(horizontal_pos = 90);
  vertical.write(vertical_pos = 150);
  trigger.write(135);

  write_to_rotor(90);
}

void loop(){
  digitalWrite(greenLed, HIGH);
  while(mode == false){
    digitalWrite(greenLed, HIGH);
    x = analogRead(A0);
    y = analogRead(A1);

    //horizontal
    if(x < 100){
      if(horizontal_pos + 1 > 180){
        horizontal.write(180);
        delay(50);
      } else {
        horizontal.write(horizontal_pos += 1);
        delay(50);
      }
    } 
    
    if (x > 900){
      if(horizontal_pos - 1 < 0){
        horizontal.write(0);
        delay(50);
      } else {
        horizontal.write(horizontal_pos -= 1);
        delay(50);
      }
    }

    //vertical
    if(y < 100){
      if(vertical_pos - 1 < 125){
        vertical.write(125);
        delay(50);
      } else {
        vertical.write(vertical_pos -= 1);
        delay(50);
      }
    }

    if(y > 900){
      if(vertical_pos + 1 > 180){
        vertical.write(180);
        delay(50);
      } else {
        vertical.write(vertical_pos += 1);
        delay(50);
      }
    }
    
    if(digitalRead(redBtn) == HIGH){
      mode = true;
        digitalWrite(greenLed, LOW);
        Serial.write("a");
        break;
    }
  }

  while(mode == true){
    digitalWrite(redLed, HIGH);
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

    if(digitalRead(greenBtn) == HIGH){
      mode = false;
        digitalWrite(redLed, LOW);
        Serial.write("m");
        break;
    }
  }
}