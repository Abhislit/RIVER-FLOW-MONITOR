# 🌊 River IoT Flow Meter

An internet-connected flow meter that continuously measures a river's flow rate and streams real-time data to the cloud via Soracom and AWS IoT.

---

## Hardware Requirements

| Component | Qty |
|---|---|
| Raspberry Pi 3 Model B+ | 1 |
| SORACOM Air Global IoT SIM | 1 |
| Huawei 3G USB Dongle (MS2131i) | 1 |
| Adafruit YF-S201 Liquid Flow Meter | 1 |
| External Battery Pack (9000 mAh) | 1 |
| Male/Female Jumper Wires | 3 |
| 1" PVC Pipe (5 ft) | 2 |

---

## Software Requirements

- Python 3
- Raspbian OS
- SORACOM Account (Harvest + Funnel enabled)
- AWS Account (IoT + CloudWatch)

Install dependencies:

```bash
sudo apt-get install python-requests
pip3 install RPi.GPIO
```

---

## Wiring

| Flow Meter Wire | Raspberry Pi GPIO Pin |
|---|---|
| Red (DC Power) | Pin 1 — 3.3V |
| Black (Ground) | Pin 6 — Ground |
| Yellow (Output) | Pin 7 — GPIO4 |

---

## Running the Script

```bash
cd /home/pi/Desktop/flowmeter
python3 flowmeter.py
```

To auto-start on boot, add to `/etc/rc.local` (above `exit 0`):

```bash
python3 /home/pi/Desktop/flowmeter/flowmeter.py &
```

---

## Cloud Architecture

```
YF-S201 Sensor
     ↓
Raspberry Pi (flowmeter.py)
     ↓  HTTP POST
SORACOM Unified Endpoint
     ↓              ↓
Soracom Harvest   Soracom Funnel
(Real-time graph)      ↓
                   AWS IoT
                       ↓
                  AWS CloudWatch
                       ↓
                  Email Alerts
```

---

## AWS IoT Rule Query

```sql
SELECT * FROM 'funnel/flowmeter'
```

CloudWatch metric config:
- **Metric name:** `flow_rate`
- **Namespace:** `flowmeter`
- **Value:** `${payloads.flow_rate}`

---

## Configuration

Edit `flowmeter.py` to change measurement interval:

```python
time.sleep(60)  # collect every 60 seconds for deployment
```

Set CloudWatch alarm threshold based on your river's normal flow baseline (e.g., `flow_rate >= 1.0`).

---

## License

Apache-2.0 — Bob Hammell, 2019
