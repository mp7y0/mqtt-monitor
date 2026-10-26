
#!/usr/bin/env python3

import argparse
import json
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt


SENSITIVE_KEYS = {
    "password", "passwd", "pwd", "token", "access_token",
    "refresh_token", "secret", "authorization", "api_key",
    "apikey", "private_key", "credential"
}


def redact(value, key=""):
    """Hide likely secret values before displaying or logging JSON."""
    if key.casefold() in SENSITIVE_KEYS:
        return "[REDACTED]"

    if isinstance(value, dict):
        return {
            k: redact(v, k)
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [redact(item) for item in value]

    return value


def parse_args():
    parser = argparse.ArgumentParser(
        description="MQTT monitor for authorized brokers"
    )

    parser.add_argument("ip", help="Broker hostname or IP")
    parser.add_argument("port", type=int, nargs="?", default=1883)
    parser.add_argument("-t", "--topic", default="lab/#")
    parser.add_argument("-f", "--filter", help="Filter by payload text")
    parser.add_argument("-n", "--limit", type=int, default=0)
    parser.add_argument("-u", "--username")
    parser.add_argument("-P", "--password")
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--hex", action="store_true",
                        help="Show payload bytes as hexadecimal")
    parser.add_argument("--save", help="Save redacted events to JSONL")
    parser.add_argument("--show-payload", action="store_true",
                        help="Show full decoded payload, with JSON secrets redacted")

    args = parser.parse_args()

    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    if args.limit < 0:
        parser.error("--limit cannot be negative")
    if args.timeout < 1:
        parser.error("--timeout must be positive")

    return args


def main():
    args = parse_args()
    received = 0
    connected = False
    output_file = None

    if args.save:
        output_file = open(args.save, "a", encoding="utf-8")

    def on_connect(client, userdata, flags, reason_code, properties):
        nonlocal connected

        if reason_code.is_failure:
            print(f"[-] Connection rejected: {reason_code}")
            client.disconnect()
            return

        connected = True
        print(f"[+] Connected: {args.ip}:{args.port}")
        print(f"[*] Topic filter: {args.topic}")

        result, _ = client.subscribe(args.topic)
        if result != mqtt.MQTT_ERR_SUCCESS:
            print("[-] Subscribe request failed")
            client.disconnect()

    def on_subscribe(client, userdata, mid, reason_code_list, properties):
        for code in reason_code_list:
            if code.is_failure:
                print(f"[-] Subscription rejected: {code}")

    def on_message(client, userdata, msg):
        nonlocal received

        raw = bytes(msg.payload)
        payload = raw.decode("utf-8", errors="replace")

        if args.filter and args.filter.casefold() not in payload.casefold():
            return

        try:
            parsed = json.loads(payload)
            is_json = True
        except (json.JSONDecodeError, UnicodeDecodeError):
            parsed = None
            is_json = False

        if args.json_only and not is_json:
            return

        received += 1
        now_utc = datetime.now(timezone.utc)
        now_local = now_utc.astimezone()

        safe_data = parsed if is_json else None

        event = {
            "received_at_utc": now_utc.isoformat(),
            "received_at_local": now_local.isoformat(),
            "broker": {
                "host": args.ip,
                "port": args.port
            },
            "topic": msg.topic,
            "qos": msg.qos,
            "retained": msg.retain,
            "payload_bytes": len(raw),
            "payload_sha256": hashlib.sha256(raw).hexdigest(),
            "format": "json" if is_json else "text_or_binary",
            "payload": safe_data if is_json else "[omitted: non-JSON]",
        }

        print(f"\n{'=' * 60}")
        print(f"Message #{received}")
        print(f"UTC:      {event['received_at_utc']}")
        print(f"Local:    {event['received_at_local']}")
        print(f"Broker:   {args.ip}:{args.port}")
        print(f"Topic:    {msg.topic}")
        print(f"QoS:      {msg.qos}")
        print(f"Retained: {msg.retain}")
        print(f"Bytes:    {len(raw)}")
        print(f"SHA-256:  {event['payload_sha256']}")
        print(f"Format:   {event['format']}")

        if is_json:
            print("JSON:")
            print(json.dumps(safe_data, indent=2, ensure_ascii=False))
        elif args.show_payload:
            print("Payload text (non-JSON):")
            print(payload)
        else:
            print("Payload: [not displayed; use --show-payload for authorized test data]")

        if args.hex:
            print("Payload HEX:")
            print(raw.hex(" "))

        if output_file:
            output_file.write(json.dumps(event, ensure_ascii=False) + "\n")
            output_file.flush()

        if args.limit and received >= args.limit:
            client.disconnect()

    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="mqtt-monitor-cli"
    )

    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.on_message = on_message

    if args.username:
        client.username_pw_set(args.username, args.password)

    try:
        client.connect(args.ip, args.port, keepalive=60)
        client.loop_forever(timeout=args.timeout)

    except KeyboardInterrupt:
        print("\n[*] Stopped by user")

    except (OSError, ValueError) as exc:
        print(f"[-] Error: {exc}", file=sys.stderr)
        return 1

    finally:
        if client.is_connected():
            client.disconnect()
        if output_file:
            output_file.close()

    if connected:
        print(f"\n[*] Messages displayed: {received}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
