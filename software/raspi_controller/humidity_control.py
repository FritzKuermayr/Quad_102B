from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Optional

# Standard humidity-control configuration.
HUMIDITY_THRESHOLD = 45.0
SENSOR_POLL_INTERVAL_SEC = 2.0
HUMIDIFIER_GPIO = 17
ENABLE_SWITCH_GPIO = 27
I2C_SENSOR = "SHT40 on Raspberry Pi I2C1: GPIO2/SDA1 and GPIO3/SCL1"
SWITCH_DEBOUNCE_MS = 50


@dataclass(frozen=True)
class HumidityControlConfig:
    humidity_threshold: float = HUMIDITY_THRESHOLD
    sensor_poll_interval_sec: float = SENSOR_POLL_INTERVAL_SEC
    humidifier_gpio: int = HUMIDIFIER_GPIO
    enable_switch_gpio: int = ENABLE_SWITCH_GPIO
    switch_debounce_ms: int = SWITCH_DEBOUNCE_MS


class HumidityController:
    """
    Non-blocking SHT40 humidity controller for a MOSFET-switched humidifier.

    The control loop runs in its own daemon thread. Any sensor read error or
    disabled enable switch forces the humidifier GPIO low.
    """

    def __init__(self, config: Optional[HumidityControlConfig] = None) -> None:
        self.config = config or HumidityControlConfig()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._humidifier_output = None
        self._enable_switch = None
        self._sensor = None

    def start(self) -> None:
        if self._thread is not None:
            return

        try:
            self._setup_gpio()
            self._humidifier_off()
        except Exception:
            self._humidifier_off()
            self._close_gpio()
            raise

        self._thread = threading.Thread(
            target=self._loop, name="humidity-control", daemon=True
        )
        self._thread.start()
        print(
            "[humidity] started "
            f"threshold={self.config.humidity_threshold:.1f}% "
            f"poll={self.config.sensor_poll_interval_sec:.1f}s"
        )

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(
                timeout=max(1.0, self.config.sensor_poll_interval_sec + 0.5)
            )
            self._thread = None

        self._humidifier_off()
        self._close_gpio()
        print("[humidity] stopped")

    # STATE MACHINE DRIVER:
    # Periodically runs the humidity-control state machine without blocking the
    # quadruped movement loop.
    def _loop(self) -> None:
        while not self._stop_event.is_set():
            self._control_once()
            self._stop_event.wait(self.config.sensor_poll_interval_sec)

    # STATE MACHINE TRANSITION LOGIC:
    # State is represented by the physical humidifier output:
    # - OFF when the enable switch is off
    # - OFF when the sensor read fails
    # - ON when the switch is enabled and humidity is below threshold
    # - OFF when humidity is at or above threshold
    def _control_once(self) -> None:
        if not self._switch_enabled():
            self._humidifier_off()
            return

        humidity = self._read_humidity()
        if humidity is None:
            self._humidifier_off()
            return

        if humidity < self.config.humidity_threshold:
            self._humidifier_on()
        else:
            self._humidifier_off()

    # SERVICE FUNCTION:
    # Initializes GPIO devices for the MOSFET output and enable-switch input.
    def _setup_gpio(self) -> None:
        try:
            from gpiozero import Button, DigitalOutputDevice
        except ImportError as exc:
            raise RuntimeError(
                "gpiozero is required for humidity control. Run software/setup_pi.sh on the Raspberry Pi."
            ) from exc

        self._humidifier_output = DigitalOutputDevice(
            self.config.humidifier_gpio,
            active_high=True,
            initial_value=False,
        )
        self._enable_switch = Button(
            self.config.enable_switch_gpio,
            pull_up=True,
            bounce_time=self.config.switch_debounce_ms / 1000.0,
        )

    # SERVICE FUNCTION:
    # Releases GPIO resources during shutdown.
    def _close_gpio(self) -> None:
        for device in (self._humidifier_output, self._enable_switch):
            if device is not None:
                device.close()
        self._humidifier_output = None
        self._enable_switch = None

    # EVENT CHECKER:
    # Checks whether the dedicated humidifier enable switch is ON.
    # GPIO27 uses an internal pull-up, so a pressed/closed switch to GND means ON.
    def _switch_enabled(self) -> bool:
        return bool(self._enable_switch is not None and self._enable_switch.is_pressed)

    # SERVICE FUNCTION:
    # Turns the humidifier ON by driving GPIO17 high to enable the MOSFET module.
    def _humidifier_on(self) -> None:
        if self._humidifier_output is not None:
            self._humidifier_output.on()

    # SERVICE FUNCTION:
    # Turns the humidifier OFF by driving GPIO17 low. This is the fail-safe state.
    def _humidifier_off(self) -> None:
        if self._humidifier_output is not None:
            self._humidifier_output.off()

    # EVENT CHECKER:
    # Reads relative humidity from the SHT40 sensor. Returning None represents
    # a sensor fault event and forces the state machine to turn the humidifier OFF.
    def _read_humidity(self) -> Optional[float]:
        sensor = self._get_sensor()
        if sensor is None:
            return None

        try:
            _temperature_c, relative_humidity = sensor.measurements
        except Exception as exc:
            print(f"[humidity] sensor read failed; humidifier off: {exc}")
            self._sensor = None
            return None

        return float(relative_humidity)

    # SERVICE FUNCTION:
    # Lazily initializes the SHT40 I2C sensor on Raspberry Pi I2C1
    # using GPIO2/SDA1 and GPIO3/SCL1.
    def _get_sensor(self):
        if self._sensor is not None:
            return self._sensor

        try:
            import adafruit_sht4x
            import board

            self._sensor = adafruit_sht4x.SHT4x(board.I2C())
        except Exception as exc:
            print(f"[humidity] sensor init failed; humidifier off: {exc}")
            self._sensor = None

        return self._sensor
