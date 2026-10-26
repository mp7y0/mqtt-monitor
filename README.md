<h1 align="center">📡 MQTT Monitor</h1>

<p align="center">
  A lightweight, safe-by-default CLI for observing MQTT traffic on brokers you are authorized to test.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/protocol-MQTT-purple" alt="MQTT">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/use-authorized%20testing%20only-red" alt="Authorized use only">
</p>

---

## ✨ Features

- 🔌 Connect to any MQTT broker with optional username/password authentication
- 🎯 Subscribe to any topic filter (wildcards `#` and `+` supported)
- 🔍 Filter messages by payload content (case-insensitive)
- 🧾 Pretty-printed JSON payloads
- 🔐 **Automatic redaction** of sensitive JSON keys (`password`, `token`, `api_key`, ...)
- 🛡️ Non-JSON payloads are hidden by default; opt in with `--show-payload`
- 🔢 Per-message metadata: UTC/local timestamp, topic, QoS, retain flag, size, SHA-256 hash
- 💾 Export events to JSONL for later analysis and reporting
- 🧮 Optional hex dump of raw payload bytes
- ⏱️ Message limit and timeout controls

## 📦 Installation

```bash
git clone https://github.com/mp7y0/mqtt-monitor.git
cd mqtt-monitor

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 🚀 Usage

```bash
python3 mqtt_monitor.py <broker> [port] [options]
```

### Examples

```bash
# Monitor the default lab topic on port 1883
python3 mqtt_monitor.py 192.168.1.50

# Custom port and topic
python3 mqtt_monitor.py broker.example.com 8883 -t "sensors/#"

# Only JSON messages containing "temperature", stop after 20
python3 mqtt_monitor.py 10.0.0.5 -t "#" --json-only -f temperature -n 20

# With credentials, saving evidence to a file
python3 mqtt_monitor.py 10.0.0.5 -u tester -P 'S3cret' --save evidence.jsonl

# Include raw bytes as hex
python3 mqtt_monitor.py 10.0.0.5 --hex --show-payload
```

### Options

| Option | Description | Default |
|---|---|---|
| `ip` | Broker hostname or IP | required |
| `port` | Broker port | `1883` |
| `-t, --topic` | Topic filter to subscribe to | `lab/#` |
| `-f, --filter` | Show only messages whose payload contains this text | none |
| `-n, --limit` | Disconnect after N displayed messages (0 = unlimited) | `0` |
| `-u, --username` | Username | none |
| `-P, --password` | Password | none |
| `--timeout` | Network loop timeout (seconds) | `10` |
| `--json-only` | Ignore non-JSON messages | off |
| `--hex` | Print payload bytes as hexadecimal | off |
| `--save FILE` | Append redacted events to a JSONL file | none |
| `--show-payload` | Display decoded non-JSON payloads | off |

## 🧾 Output Example

```text
============================================================
Message #1
UTC:      2026-10-26T12:00:00.123456+00:00
Topic:    lab/sensor1
QoS:      0
Retained: False
Bytes:    52
SHA-256:  9f86d081884c7d659a2feaa0c55ad015...
Format:   json
JSON:
{
  "temp": 23.5,
  "token": "[REDACTED]"
}
```

