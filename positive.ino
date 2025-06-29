int motorPin[3] = {3, 4, 5};
int motor_number = 0;
int experiment_number = 0;
bool sensitivity_point = false;
int comfort_level = 255;
int min_intensity = 255;
int max_intensity = 0;
int min_signal_continious = 151;
int min_delay_continious = 151;
bool experiment_running = false;

const int IndicatorButton = 6;

void setup() {
  for (int i = 0; i < 3; i++) {
    pinMode(motorPin[i], OUTPUT);
    analogWrite(motorPin[i], 0);
  }
  pinMode(IndicatorButton, INPUT);
  Serial.begin(9600);
  Serial.println("Arduino Ready");
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "L1" && !experiment_running) {
      experiment_number = (experiment_number - 1 + 4) % 4;
      Serial.print("Switch to experiment: ");
      Serial.println(experiment_number);
    }
    else if (command == "R1" && !experiment_running) {
      experiment_number = (experiment_number + 1) % 4;
      Serial.print("Switch to experiment: ");
      Serial.println(experiment_number);
    }
    else if (command == "X") {
      experiment_running = true;
      Serial.println("Experiment started");
    }
    else if (command == "O") {
      experiment_running = false;
      stopMotors();
      Serial.println("Experiment paused");
    }
    else if (command.startsWith("S:")) {
      if (experiment_number == 3 && experiment_running) {
        runStickExperiment(command);
      }
    }
  }

  if (experiment_running) {
    switch (experiment_number) {
      case 0: runIntensityExperiment(); break;
      case 1: runSignalDurationExperiment(); break;
      case 2: runDelayExperiment(); break;
      case 3: break;
    }
  }
}

void stopMotors() {
  for (int i = 0; i < 3; i++) {
    analogWrite(motorPin[i], 0);
    Serial.print("V:"); Serial.print(i); Serial.print(":0\n");
  }
}

void runIntensityExperiment() {
  if (digitalRead(IndicatorButton) == HIGH) {
    delay(200);
    for (int i = 0; i <= 255; i++) {
      analogWrite(motorPin[motor_number], i);
      Serial.print("V:"); Serial.print(motor_number); Serial.print(":"); Serial.println(i);
      Serial.print("P:intensity:"); Serial.println(i);
      delay(50);
      if (digitalRead(IndicatorButton) == HIGH) {
        delay(200);
        if (!sensitivity_point) {
          sensitivity_point = true;
          Serial.print("Begin staring Intensity: ");
          Serial.println(i);
          min_intensity = i;
          Serial.print("MIN_I:"); Serial.println(min_intensity);
        } else {
          sensitivity_point = false;
          comfort_level = i;
          stopMotors();
          Serial.print("End comfort Intensity: ");
          Serial.println(i);
          max_intensity = i;
          Serial.print("MAX_I:"); Serial.println(max_intensity);
          motor_number = (motor_number + 1) % 3;
          if (motor_number == 0) experiment_number = 1;
          experiment_running = false;
          break;
        }
      }
      if (i == 255) {
        stopMotors();
        comfort_level = i;
        Serial.println("Max intensity reached: 255");
        max_intensity = i;
        Serial.print("MAX_I:"); Serial.println(max_intensity);
        motor_number = (motor_number + 1) % 3;
        if (motor_number == 0) experiment_number = 1;
        experiment_running = false;
      }
    }
  }
}

void runSignalDurationExperiment() {
  if (digitalRead(IndicatorButton) == HIGH) {
    delay(200);
    for (int i = 150; i >= 0; i -= 10) {
      for (int j = 0; j < 5; j++) {
        analogWrite(motorPin[0], comfort_level);
        analogWrite(motorPin[1], comfort_level);
        analogWrite(motorPin[2], comfort_level);
        Serial.print("V:0:"); Serial.println(comfort_level);
        Serial.print("V:1:"); Serial.println(comfort_level);
        Serial.print("V:2:"); Serial.println(comfort_level);
        Serial.print("P:duration:"); Serial.println(i);
        delay(i);
        stopMotors();
        delay(500);
        if (digitalRead(IndicatorButton) == HIGH) {
          delay(200);
          min_signal_continious = i;
          Serial.print("MIN_S:"); Serial.println(min_signal_continious);
          Serial.print("Min signal duration: ");
          Serial.println(i);
          experiment_number = 2;
          experiment_running = false;
          break;
        }
      }
      if (min_signal_continious != 151) break;
      if (i == 0) {
        min_signal_continious = 0;
        Serial.print("MIN_S:"); Serial.println(min_signal_continious);
        Serial.println("Min signal duration: 0");
        experiment_number = 2;
        experiment_running = false;
      }
    }
  }
}

void runDelayExperiment() {
  if (digitalRead(IndicatorButton) == HIGH) {
    delay(200);
    for (int i = 500; i >= 0; i -= 10) {
      for (int j = 0; j < 5; j++) {
        analogWrite(motorPin[0], comfort_level);
        analogWrite(motorPin[1], comfort_level);
        analogWrite(motorPin[2], comfort_level);
        Serial.print("V:0:"); Serial.println(comfort_level);
        Serial.print("V:1:"); Serial.println(comfort_level);
        Serial.print("V:2:"); Serial.println(comfort_level);
        Serial.print("P:delay:"); Serial.println(i);
        delay(min_signal_continious);
        stopMotors();
        delay(i);
        if (digitalRead(IndicatorButton) == HIGH) {
          delay(200);
          min_delay_continious = i;
          Serial.print("MIN_D:"); Serial.println(min_delay_continious);
          Serial.print("Min delay: ");
          Serial.println(i);
          experiment_number = 0;
          experiment_running = false;
          break;
        }
      }
      if (min_delay_continious != 151) break;
      if (i == 0) {
        min_delay_continious = 0;
        Serial.print("MIN_D:"); Serial.println(min_delay_continious);
        Serial.println("Min delay: 0");
        experiment_number = 0;
        experiment_running = false;
      }
    }
  }
}

void runStickExperiment(String command) {
  int stickX, stickY, l2Value;
  sscanf(command.c_str(), "S:%d:%d:%d", &stickX, &stickY, &l2Value);
  
  stopMotors();

  if (abs(stickX) > 20 || abs(stickY) > 20) {
    if (abs(stickX) > abs(stickY)) {
      motor_number = (stickX > 0) ? 1 : 0;
    } else {
      motor_number = (stickY > 0) ? 2 : 0;
    }
    analogWrite(motorPin[motor_number], l2Value);
    Serial.print("V:"); Serial.print(motor_number); Serial.print(":"); Serial.println(l2Value);
    Serial.print("P:power:"); Serial.println(l2Value);
  }
}