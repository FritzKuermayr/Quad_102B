# Quadruped Keyboard Control

Dieses Repo enthaelt die aktuelle Raspberry-Pi-Steuerung fuer den Quadruped.
Der Roboter wird direkt auf dem Raspberry Pi ueber ein SSH-Terminal gesteuert.
Es wird kein Hotspot-Setup verwendet.

## Aktuelles Setup

- Raspberry Pi und Laptop sind im gleichen normalen WLAN.
- Der Code liegt auf dem Pi in `~/Quad_102B`.
- Updates kommen per Git von GitHub:
  `https://github.com/FritzKuermayr/Quad_102B.git`
- Die Bewegung wird mit `h/j/k/l` gesteuert. Pfeiltasten bleiben als Fallback
  aktiv, sind aber je nach Terminal/SSH-Client weniger zuverlaessig.
- Standard-Dynamixel-Port ist `/dev/ttyUSB0`.
- Standard-Baudrate ist `1000000`.
- Motoren: Dynamixel RX-24F, Protocol `1.0`.

## Projektstruktur

```text
software/
├── raspi_controller/
│   ├── main.py
│   ├── g_key_leg_test.py
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

## Raspberry Pi vorbereiten

1. Raspberry Pi OS auf die MicroSD-Karte flashen.
2. Beim Flashen oder danach SSH aktivieren.
3. Den Pi mit dem normalen WLAN verbinden. Kein Hotspot ist noetig.
4. IP-Adresse des Pi finden:

```bash
hostname -I
```

Oder vom Laptop aus den Hostnamen probieren:

```bash
ssh pi@raspberrypi.local
```

Falls der Hostname nicht funktioniert:

```bash
ssh pi@<PI_IP_ADRESSE>
```

## Code auf dem Pi installieren

Auf dem Pi:

```bash
cd ~
git clone https://github.com/FritzKuermayr/Quad_102B.git
cd ~/Quad_102B
chmod +x software/setup_pi.sh
./software/setup_pi.sh
```

Wenn das Repo schon auf dem Pi existiert, aktualisieren:

```bash
cd ~/Quad_102B
git pull origin main
```

Danach den Dynamixel USB-Adapter einstecken und pruefen:

```bash
ls /dev/ttyUSB* /dev/ttyACM*
```

Meist ist der Adapter `/dev/ttyUSB0`. Falls noetig, Port-Rechte setzen:

```bash
sudo chmod a+rw /dev/ttyUSB0
```

## Python-Abhaengigkeiten

Normalerweise erledigt `software/setup_pi.sh` alles. Falls ein Python-Modul
fehlt, im aktiven Projektordner nachinstallieren:

```bash
cd ~/Quad_102B
source .venv/bin/activate
python -m pip install -r software/requirements.txt
```

## Keyboard-Control starten

Roboter fuer den ersten Test aufbocken, damit die Beine frei haengen.

```bash
cd ~/Quad_102B
source .venv/bin/activate
python software/raspi_controller/main.py --port /dev/ttyUSB0 --gait TROT_LOW --torque-limit 400
```

Tasten:

```text
k      vorwaerts gehen
j      rueckwaerts gehen
h      links drehen
l      rechts drehen
Space  stoppen und neutral stehen
s      stoppen und neutral stehen
q      sauber beenden, Torque aus
```

Pfeiltasten funktionieren zusaetzlich, falls das Terminal sie sauber weitergibt:

```text
↑  vorwaerts gehen
↓  rueckwaerts gehen
←  links drehen
→  rechts drehen
```

Wenn ein Input erkannt wird, steht im Terminal zum Beispiel:

```text
[keyboard] k -> forward
```

Falls die Motoren auf dem Stand zu schwach reagieren, Torque-Limit erhoehen:

```bash
python software/raspi_controller/main.py --port /dev/ttyUSB0 --gait TROT_LOW --torque-limit 500
```

Alternative Gaits:

```bash
python software/raspi_controller/main.py --port /dev/ttyUSB0 --gait WALK --torque-limit 500
python software/raspi_controller/main.py --port /dev/ttyUSB0 --gait TROT --torque-limit 500
```

## Einzelbein-Test

Dieses separate Skript bewegt nur das vordere linke Bein kurz aus der
Neutralstellung und danach wieder zurueck. Es ist nur fuer Motor-/Mapping-Tests.

```bash
cd ~/Quad_102B
source .venv/bin/activate
python software/raspi_controller/g_key_leg_test.py --port /dev/ttyUSB0
```

Tasten:

```text
g  vorderes linkes Bein kurz bewegen
q  beenden, Torque aus
```

Mapping fuer diesen Test:

```text
FL_q1 = Motor ID 1
Neutral = 150 deg
Testbewegung = 165 deg fuer 0.35 s, danach zurueck auf 150 deg
```

## Wichtige Checks

- Motor-IDs und Reihenfolge stehen in `software/raspi_controller/q8gait/config_rx24f.py`.
- Beim Start bewegt `main.py` alle Motoren in die Neutralstellung.
- Beim Beenden mit `q` oder `Ctrl+C` wird Torque deaktiviert.
- Vor dem ersten Lauf-Test den Roboter aufbocken.
- Wenn `dynamixel_sdk` fehlt: `python -m pip install -r software/requirements.txt`.
- Wenn `/dev/ttyUSB0` nicht erreichbar ist: USB-Adapter pruefen und ggf.
  `sudo chmod a+rw /dev/ttyUSB0` ausfuehren.
