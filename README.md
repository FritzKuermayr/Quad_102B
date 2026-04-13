# Quadruped Keyboard Control

Dieses Repo ist auf die direkte Movement-Control des Quadrupeds reduziert. Wristband,
EMG, Research, CAD und alte Experimente wurden entfernt.

## Was uebrig ist

```text
software/
├── raspi_controller/
│   ├── main.py
│   ├── g_key_leg_test.py
│   ├── humidity_control.py
│   ├── keyboard_interface.py
│   └── q8gait/
│       ├── config_rx24f.py
│       ├── gait_generator.py
│       ├── gait_manager.py
│       ├── kinematics_solver.py
│       ├── motion_runner.py
│       └── robot.py
├── dynamixel_tools/
├── requirements.txt
└── setup_pi.sh
```

## Steuerung

Die Steuerung laeuft auf dem Raspberry Pi. Dein Laptop verbindet sich per SSH mit
dem Pi; die Pfeiltasten werden dann ueber das SSH-Terminal gelesen.

```text
↑  vorwaerts gehen
↓  rueckwaerts gehen
←  links drehen
→  rechts drehen
Space  stoppen und neutral stehen
q  sauber beenden, Torque aus
```

## Raspberry Pi mit WLAN verbinden

Wichtig: Beim Raspberry Pi 4 ist der USB-C-Port normalerweise nur fuer Strom.
Du verbindest den Laptop also nicht einfach per USB-C-Kabel zum Steuern. Die
Tastatursteuerung laeuft ueber SSH im WLAN. Der Laptop und der Raspberry Pi
muessen dafuer im gleichen Netzwerk sein.

### Variante A: Headless Setup mit Raspberry Pi Imager

Diese Variante ist am einfachsten, wenn du keinen Monitor und keine Tastatur am
Pi hast.

1. MicroSD-Karte in den Laptop stecken.
2. Raspberry Pi Imager oeffnen.
3. Raspberry Pi OS auswaehlen.
4. Die MicroSD-Karte als Storage auswaehlen.
5. In den Imager-Einstellungen SSH aktivieren.
6. Benutzername und Passwort setzen, zum Beispiel:

```text
username: pi
password: raspberry
```

7. WLAN konfigurieren:

```text
SSID: <DEIN_WLAN_NAME>
Password: <DEIN_WLAN_PASSWORT>
Wireless LAN country: US
```

8. Image auf die MicroSD-Karte schreiben.
9. MicroSD-Karte auswerfen und in den Raspberry Pi einsetzen.
10. Raspberry Pi mit USB-C-Netzteil einschalten.
11. 1-2 Minuten warten, bis der Pi gebootet und im WLAN ist.

Jetzt musst du die IP-Adresse des Pi finden. Auf dem Laptop kannst du zuerst den
Hostname probieren:

```bash
ssh pi@raspberrypi.local
```

Wenn das nicht funktioniert, die IP-Adresse im Router nachschauen oder auf dem
Pi mit Monitor/Tastatur auslesen:

```bash
hostname -I
```

Dann vom Laptop verbinden:

```bash
ssh pi@<PI_IP_ADRESSE>
```

### Variante B: Setup direkt am Raspberry Pi mit Monitor/Tastatur

Diese Variante benutzt Monitor, Tastatur und Maus direkt am Raspberry Pi.

1. MicroSD-Karte mit Raspberry Pi OS flashen.
2. MicroSD-Karte in den Pi einsetzen.
3. Monitor per HDMI anschliessen.
4. Tastatur/Maus per USB anschliessen.
5. Raspberry Pi per USB-C-Netzteil einschalten.
6. Im Raspberry-Pi-Desktop oben rechts das WLAN auswaehlen.
7. WLAN-Passwort eingeben und verbinden.
8. SSH aktivieren:

```bash
sudo systemctl enable --now ssh
```

9. IP-Adresse anzeigen:

```bash
hostname -I
```

10. Vom Laptop aus verbinden:

```bash
ssh pi@<PI_IP_ADRESSE>
```

### Verbindung pruefen

Wenn du verbunden bist, siehst du im Laptop-Terminal eine Shell auf dem Pi. Zum
Test:

```bash
hostname
pwd
```

Wenn das funktioniert, kannst du das Projekt auf den Pi kopieren und die
Controller starten.

## Projekt auf den Raspberry Pi kopieren

Wenn das Projekt noch auf deinem Laptop liegt, kopiere den kompletten Ordner auf
den Pi:

```bash
scp -r Quadruped pi@<PI_IP_ADRESSE>:~/Quadruped
```

Danach per SSH auf den Pi:

```bash
ssh pi@<PI_IP_ADRESSE>
```

In den Projektordner wechseln:

```bash
cd ~/Quadruped
```

Falls du den Ordner schon anders auf den Pi kopiert hast, einfach in diesen
Ordner wechseln.

## Einmaliges Setup auf dem Raspberry Pi

Dieses Setup installierst du einmal auf dem Pi:

```bash
cd ~/Quadruped
chmod +x software/setup_pi.sh
./software/setup_pi.sh
```

Danach den Dynamixel USB-Adapter einstecken und den Port freigeben. Meist ist
es `/dev/ttyUSB0`:

```bash
sudo chmod a+rw /dev/ttyUSB0
```

Falls der Adapter anders heisst:

```bash
ls /dev/ttyUSB* /dev/ttyACM*
```

SHT40 I2C pruefen, falls der Humidity-Sensor angeschlossen ist:

```bash
i2cdetect -y 1
```

Wenn der Humidity-Sensor noch nicht angeschlossen ist, kannst du die Motor-Tests
trotzdem starten.

## Vier-Tasten-Steuerung starten

1. Laptop und Pi muessen im gleichen WLAN sein.
2. Vom Laptop per SSH verbinden:

```bash
ssh pi@<PI_IP_ADRESSE>
```

3. Auf dem Pi den Controller starten:

```bash
cd ~/Quadruped
source .venv/bin/activate
python software/raspi_controller/main.py --port /dev/ttyUSB0
```

Tasten:

```text
↑  vorwaerts gehen
↓  rueckwaerts gehen
←  links drehen
→  rechts drehen
Space  stoppen
q  beenden
```

Mit niedrigerem Torque-Limit starten:

```bash
python software/raspi_controller/main.py --gait TROT_LOW --torque-limit 500
```

Alternative Gaits:

```bash
python software/raspi_controller/main.py --gait TROT
python software/raspi_controller/main.py --gait WALK
```

## G-Button Bein-Test starten

Dieses separate Testskript ist fuer einen einfachen Button-to-motor-Check:
Wenn du `g` auf dem Laptop drueckst, bewegt der Roboter das vordere linke Bein
kurz aus der Neutralstellung und danach wieder zurueck. Die normale
Vier-Tasten-Steuerung wird dabei nicht benutzt.

1. Laptop und Pi muessen im gleichen WLAN sein.
2. Vom Laptop per SSH verbinden:

```bash
ssh pi@<PI_IP_ADRESSE>
```

3. Auf dem Pi den G-Test starten:

```bash
cd ~/Quadruped
source .venv/bin/activate
python software/raspi_controller/g_key_leg_test.py --port /dev/ttyUSB0
```

Tasten:

```text
g  vorderes linkes Bein kurz bewegen
q  beenden, Torque aus
```

Vor diesem Test den Roboter aufbocken, damit das Bein frei laufen kann.

## Humidity / Humidifier Control

Der Humidity-Controller laeuft parallel zur Keyboard-Movement-Control in einem
separaten Python-Thread. Die Bewegungsschleife wird dadurch nicht blockiert.

Konfiguration steht oben in:

```text
software/raspi_controller/humidity_control.py
```

Standardwerte:

```python
HUMIDITY_THRESHOLD = 45.0
SENSOR_POLL_INTERVAL_SEC = 2.0
HUMIDIFIER_GPIO = 17
ENABLE_SWITCH_GPIO = 27
I2C_SENSOR = "SHT40 on Raspberry Pi I2C1: GPIO2/SDA1 and GPIO3/SCL1"
SWITCH_DEBOUNCE_MS = 50
```

Zum Aendern der Ziel-Luftfeuchtigkeit `HUMIDITY_THRESHOLD` anpassen. Zum Aendern
der Pins `HUMIDIFIER_GPIO` und `ENABLE_SWITCH_GPIO` anpassen.

### SHT40 Sensor Wiring

Adafruit SHT40 Breakout, I2C, Standard Raspberry Pi 4 I2C1:

```text
SHT40 VIN  -> Raspberry Pi 3.3V, physical pin 1
SHT40 GND  -> Raspberry Pi GND, physical pin 6
SHT40 SDA  -> Raspberry Pi GPIO2 / SDA1, physical pin 3
SHT40 SCL  -> Raspberry Pi GPIO3 / SCL1, physical pin 5
```

GPIO2 und GPIO3 sind fuer den SHT40 I2C-Bus reserviert. Den Sensor in diesem
Setup mit 3.3V versorgen.

### Humidifier MOSFET Wiring

Der Humidifier wird extern mit 5V versorgt. Der Raspberry Pi versorgt den
Humidifier nicht direkt. GPIO17 gibt nur das Steuersignal fuer ein
GPIO-kompatibles MOSFET Power Controller Modul.

Control-Seite:

```text
MOSFET SIG/IN -> Raspberry Pi GPIO17, physical pin 11
MOSFET GND    -> Raspberry Pi GND, physical pin 9
MOSFET VCC    -> Raspberry Pi 3.3V, physical pin 17, falls das Modul VCC braucht
```

Power-Pfad:

```text
External 5V supply positive -> MOSFET power input positive
MOSFET power output positive -> humidifier 5V input line
External 5V supply ground -> humidifier ground
External 5V supply ground -> MOSFET ground
Raspberry Pi ground -> same common ground
```

Beim Micro-USB-Kabel des Humidifiers wird nur die positive 5V-Leitung ueber den
MOSFET geschaltet. Die Ground-Leitung bleibt direkt mit dem Ground der externen
5V-Versorgung verbunden. Alle Grounds muessen gemeinsam verbunden sein.

### Humidifier Enable Switch

Der Enable-Switch ist ein eigener digitaler Eingang mit internem Pull-up:

```text
Switch signal     -> Raspberry Pi GPIO27, physical pin 13
Switch other side -> Raspberry Pi GND, physical pin 14
```

Logik:

```text
Switch closed to GND = humidifier enable ON
Switch open          = humidifier enable OFF
```

Wenn der Enable-Switch OFF ist, bleibt der Humidifier immer OFF. Wenn der Switch
ON ist und die gemessene Luftfeuchtigkeit unter `HUMIDITY_THRESHOLD` liegt,
schaltet GPIO17 den MOSFET ein. Bei Sensorfehler, Shutdown oder `Ctrl+C` wird
GPIO17 ausgeschaltet und GPIO wird aufgeraeumt.

## Wichtige Checks

- Motor-IDs und Reihenfolge stehen in `software/raspi_controller/q8gait/config_rx24f.py`.
- Standard-Port ist `/dev/ttyUSB0`, Baudrate `1000000`, Dynamixel Protocol `1.0`.
- Beim Beenden mit `q` oder `Ctrl+C` wird Torque deaktiviert.
- Beim Beenden mit `q` oder `Ctrl+C` wird der Humidifier ausgeschaltet.
- Humidity-Control Pins: SHT40 auf GPIO2/GPIO3, MOSFET auf GPIO17, Enable-Switch auf GPIO27.
- Der Humidifier braucht eine externe 5V-Versorgung; der Pi schaltet nur den MOSFET.
- Alle Grounds muessen gemeinsam verbunden sein.
- Vor dem ersten Test den Roboter aufbocken, damit die Beine frei laufen koennen.
