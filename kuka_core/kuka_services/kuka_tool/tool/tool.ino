int power = 2;
int dir[3] = {3,4,5};
char msg = '0';
int tim = 6000;
void setup() {
  Serial.begin(115200);
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
}

void loop() {
  if(Serial.available()>0){
    msg = char(Serial.read());
    if(msg=='l') {
      for(int i=0;i<3;i++){
        digitalWrite(dir[i], HIGH); //przykrecanie
      }
      digitalWrite(power, HIGH);
      delay(tim);
      digitalWrite(power, LOW);
    }  
    if(msg=='r') {
      for(int i=0;i<3;i++){
        digitalWrite(dir[i], LOW); //odkrecanie
      }
      digitalWrite(power, HIGH);
      delay(tim);
      digitalWrite(power, LOW);
    }  
    delay(1000);
    Serial.println('d');
  }
}
