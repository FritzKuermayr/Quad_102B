from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional

# Standard humidity-control configuration.
HUMIDITY_THRESHOLD = 45.0
SENSOR_POLL_INTERVAL_SEC = 2.0
HUMIDIFIER_GPIO = 17
I2C_SENSOR = "SHT40 on Raspberry Pi I2C1: GPIO2/SDA1 and GPIO3/SCL1"
EXPECTED_I2C_ADDRESS = 0x44


@dataclass(frozen=True)
class HumidityControlConfig:
    humidity_threshold: float = HUMIDITY_THRESHOLD
    sensor_poll_interval_sec: float = SENSOR_POLL_INTERVAL_SEC
    humidifier_gpio: int = HUMIDIFIER_GPIO


class _LgpioOutputDevice:
    """Minimal ON/OFF output wrapper backed by lgpio."""

    def __init__(self, pin: int, *, active_high: bool = True, initial_value: bool = False):
        import lgpio

        self._lgpio = lgpio
        self._pin = pin
        self._active_high = active_high
        self._chip = lgpio.gpiochip_open(0)
        lgpio.gpio_claim_output(self._chip, self._pin)
        self._write(initial_value)

    def _write(self, value: bool) -> None:
        physical_level = 1 if bool(value) == self._active_high else 0
        self._lgpio.gpio_write(self._chip, self._pin, physical_level)

    def on(self) -> None:
        self._write(True)

    def off(self) -> None:
        self._write(False)

    def close(self) -> None:
        if self._chip is not None:
            try:
                self.off()
            finally:
                self._lgpio.gpiochip_close(self._chip)
                self._chip = None


class HumidityController:
    """
    Non-blocking SHT40 humidity controller for a MOSFET-switched humidifier.

    The control loop runs in its own daemon thread. Any sensor read error or
    exception forces the humidifier GPIO low.
    """

    def __init__(self, config: Optional[HumidityControlConfig] = None) -> None:
        self.config = config or HumidityControlConfig()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._humidifier_output = None
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
    # - OFF when the sensor read fails
    # - ON when humidity is below threshold
    # - OFF when humidity is at or above threshold
    def _control_once(self) -> None:
        humidity = self._read_humidity()
        if humidity is None:
            self._humidifier_off()
            return

        if humidity < self.config.humidity_threshold:
            self._humidifier_on()
        else:
            self._humidifier_off()

    # SERVICE FUNCTION:
    # Initializes the GPIO device for the MOSFET output.
    def _setup_gpio(self) -> None:
        try:
            from gpiozero import OutputDevice

            self._humidifier_output = OutputDevice(
                self.config.humidifier_gpio,
                active_high=True,
                initial_value=False,
            )
            print("[humidity] using gpiozero output backend")
            return
        except ImportError:
            pass

        try:
            self._humidifier_output = _LgpioOutputDevice(
                self.config.humidifier_gpio,
                active_high=True,
                initial_value=False,
            )
            print("[humidity] using lgpio output backend")
        except ImportError as exc:
            raise RuntimeError(
                "No usable GPIO output backend found. Run software/setup_pi.sh on the Raspberry Pi."
            ) from exc

    # SERVICE FUNCTION:
    # Releases GPIO resources during shutdown.
    def _close_gpio(self) -> None:
        for device in (self._humidifier_output,):
            if device is not None:
                device.close()
        self._humidifier_output = None

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
            try:
                sensor.i2c_device.i2c.unlock()
            except Exception:
                pass
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
            print(
                "[humidity] sensor initialized "
                f"bus={I2C_SENSOR} address=0x{EXPECTED_I2C_ADDRESS:02X}"
            )
        except Exception as exc:
            print(f"[humidity] sensor init failed; humidifier off: {exc}")
            self._sensor = None

        return self._sensor
