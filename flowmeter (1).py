import json
import time
from datetime import datetime
import RPi.GPIO as GPIO
import requests


# ─── Configuration ────────────────────────────────────────────────────────────

INPUT_PIN     = 7          # GPIO Board pin connected to sensor's yellow wire
SLEEP_SECONDS = 60         # Interval between measurements (seconds)
SORACOM_URL   = "http://unified.soracom.io"


# ─── Flow Meter Class ──────────────────────────────────────────────────────────

class FlowMeter():
    """
    Represents the YF-S201 liquid flow meter sensor.
    Tracks pulse signals from the sensor's magnetic pinwheel
    and calculates the current flow rate in liters per minute (L/min).
    """

    def __init__(self):
        self.flow_rate = 0.0
        self.last_time = datetime.now()

    def pulseCallback(self, p):
        """
        Interrupt callback triggered on each rising edge pulse from the sensor.
        Calculates flow rate from pulse frequency (Hz / 7.5 = L/min).
        """
        current_time = datetime.now()
        diff = (current_time - self.last_time).total_seconds()

        if diff > 0:
            hertz = 1.0 / diff
            self.flow_rate = hertz / 7.5  # YF-S201 datasheet conversion

        self.last_time = current_time

    def getFlowRate(self):
        """
        Returns the current flow rate.
        If no pulse has been received in over 1 second, assumes flow has
        stopped and returns 0.0.
        """
        elapsed = (datetime.now() - self.last_time).total_seconds()
        if elapsed > 1:
            self.flow_rate = 0.0
        return self.flow_rate


# ─── Cloud Publisher ───────────────────────────────────────────────────────────

def publish_to_soracom(payload: dict) -> bool:
    """
    Sends a JSON payload to the SORACOM Unified Endpoint via HTTP POST.
    Returns True on success, False on timeout or connection error.
    """
    headers = {"Content-Type": "application/json"}
    try:
        print("  → Publishing to SORACOM...")
        r = requests.post(
            SORACOM_URL,
            data=json.dumps(payload),
            headers=headers,
            timeout=5
        )
        print(f"  ✓ Response: {r.status_code}")
        return True
    except requests.exceptions.Timeout:
        print("  ✗ Error: Connection timeout.")
    except requests.exceptions.ConnectionError:
        print("  ✗ Error: Could not reach SORACOM endpoint.")
    return False


# ─── GPIO Setup ───────────────────────────────────────────────────────────────

def setup_gpio(flow_meter: FlowMeter):
    """Configures the Raspberry Pi GPIO pin and attaches the pulse callback."""
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(
        INPUT_PIN,
        GPIO.RISING,
        callback=flow_meter.pulseCallback,
        bouncetime=20
    )
    print(f"GPIO configured — listening on Pin {INPUT_PIN}")


# ─── Main Loop ────────────────────────────────────────────────────────────────

def main():
    """
    Entry point. Sets up the sensor, then loops indefinitely:
    - Reads current flow rate
    - Prints to console
    - Pushes data to SORACOM Harvest (and onward to AWS IoT via Funnel)
    """
    print("=" * 50)
    print("  River IoT Flow Meter — Starting Up")
    print("=" * 50)

    flow_meter = FlowMeter()
    setup_gpio(flow_meter)

    print(f"Collecting measurements every {SLEEP_SECONDS}s. Press Ctrl+C to stop.\n")

    try:
        while True:
            timestamp  = str(datetime.now())
            flow_rate  = flow_meter.getFlowRate()

            print(f"[{timestamp}]")
            print(f"  Flow rate: {flow_rate:.4f} L/min")

            payload = {
                "timestamp": timestamp,
                "flow_rate": flow_rate
            }

            publish_to_soracom(payload)
            print()

            time.sleep(SLEEP_SECONDS)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        GPIO.cleanup()
        print("GPIO cleaned up. Goodbye.")


if __name__ == "__main__":
    main()
