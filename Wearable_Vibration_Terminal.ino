int Pin = D10;  // connected to digital pin 

void setup() {

}

void loop() {
  // fade in from min to max in increments of 5 points:
  for (int fadeValue = 0; fadeValue <= 255; fadeValue += 5) {
    // sets the value (range from 0 to 255):
    analogWrite(Pin, fadeValue);
    // wait for 30 milliseconds to see the dimming effect
    delay(500);
  }

  // fade out from max to min in increments of 5 points:
  for (int fadeValue = 255; fadeValue >= 0; fadeValue -= 5) {
    // sets the value (range from 0 to 255):
    analogWrite(Pin, fadeValue);
    // wait for 30 milliseconds to see the dimming effect
    delay(2000);
  }

  // for (int fadeValue = 0; fadeValue >= 0; fadeValue -= 5) {
  //   // sets the value (range from 0 to 255):
  //   analogWrite(ledPin, fadeValue);
  //   // wait for 30 milliseconds to see the dimming effect
  //   delay(1000);
  // }
}
