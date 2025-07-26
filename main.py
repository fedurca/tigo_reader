#!/usr/bin/env python3
import requests
import datetime
import json
import csv
import argparse
import sys
import os

DATA_TYPES = {
    "pin": "power",    # W
    "vin": "voltage",  # V
    "iin": "current",  # raw -> scaled
    "rssi": "rssi"     # dBm
    # temperature will be fetched separately
}

DEBUG = False
CURRENT_SCALE = 0.03  # scale current

def debug(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

def load_secret(filename="secret.txt"):
    params = {}
    if not os.path.exists(filename):
        return {}
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                params[key.strip()] = value.strip().strip('"').strip("'")
    return params

def fix_url(url):
    if url.endswith("/summary"):
        url = url.replace("/summary", "/cgi-bin/summary_data")
        debug(f"Auto-corrected URL to JSON API endpoint: {url}")
    return url

def fetch_panel_data(url, username, password, data_type):
    params = {"date": datetime.date.today().strftime("%Y-%m-%d"), "temp": data_type}
    debug(f"Requesting {data_type} from {url} with params {params}")
    try:
        response = requests.get(url, params=params, auth=(username, password), timeout=5)
        debug(f"HTTP status: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] HTTP request failed: {e}")
        return None
    try:
        data = response.json()
        debug(f"JSON parse successful for dataset {data_type}")
        return data
    except json.JSONDecodeError:
        debug(f"Response for dataset '{data_type}' is not JSON:\n{response.text[:300]}")
        return None

def extract_last_values(data):
    dataset = data.get("dataset", [])[0]
    order = dataset.get("order", [])
    records = dataset.get("data", [])
    if not records:
        debug("Dataset empty.")
        return None, None
    last_entry = records[-1]
    timestamp = last_entry["t"]
    values = dict(zip(order, last_entry["d"]))
    debug(f"Dataset keys: {order}, values: {values}")
    return timestamp, values

def combine_all(url, username, password):
    combined = {}
    timestamp_final = None

    # normal datasets
    for key, label in DATA_TYPES.items():
        data = fetch_panel_data(url, username, password, key)
        if not data:
            debug(f"No dataset returned for {key}")
            continue
        timestamp, values = extract_last_values(data)
        if not timestamp:
            continue
        if not timestamp_final:
            timestamp_final = timestamp
        for panel, value in values.items():
            if label == "current":
                value = round(value * CURRENT_SCALE, 3)
            combined.setdefault(panel, {})[label] = value

    # try temperature endpoints
    temp_endpoints = ["temp", "tin", "temperature"]
    temp_found = False
    temp_values = {}
    for ep in temp_endpoints:
        data = fetch_panel_data(url, username, password, ep)
        if data:
            timestamp, values = extract_last_values(data)
            if timestamp and values:
                temp_values = values
                temp_found = True
                debug(f"Temperature dataset found with key '{ep}' -> {values}")
                break
        else:
            debug(f"No dataset for temperature key '{ep}'")

    # detect invalid temp (same as power)
    if temp_found:
        power_values = {p: metrics.get("power") for p, metrics in combined.items()}
        if temp_values == power_values:
            debug("Temperature dataset invalid (matches power values). Marking as N/A.")
            for panel in combined:
                combined[panel]["temperature"] = "N/A"
        else:
            for panel, value in temp_values.items():
                combined.setdefault(panel, {})["temperature"] = value
    else:
        debug("No temperature dataset available.")

    return timestamp_final, combined

def human_readable(timestamp, data):
    lines = [f"\n=== Last measurement ({timestamp}) ==="]
    for panel, metrics in data.items():
        lines.append(
            f"Panel {panel}: "
            f"Power={metrics.get('power','N/A')} W | "
            f"Voltage={metrics.get('voltage','N/A')} V | "
            f"Current={metrics.get('current','N/A')} A | "
            f"Temperature={metrics.get('temperature','N/A')} °C | "
            f"RSSI={metrics.get('rssi','N/A')} dBm"
        )
    return "\n".join(lines)

def output_csv(timestamp, data):
    output = ["Panel,Power (W),Voltage (V),Current (A),Temperature (°C),RSSI (dBm)"]
    for panel, metrics in data.items():
        output.append(f"{panel},{metrics.get('power','')},{metrics.get('voltage','')},"
                      f"{metrics.get('current','')},{metrics.get('temperature','')},{metrics.get('rssi','')}")
    return "\n".join(output)

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch Tigo optimizer data including temperature")
    parser.add_argument("--json-only", action="store_true", help="Output JSON only")
    parser.add_argument("--csv", action="store_true", help="Output CSV format")
    parser.add_argument("--human-only", action="store_true", help="Output human-readable only")
    parser.add_argument("--url", help="Tigo gateway URL (use /cgi-bin/summary_data)")
    parser.add_argument("--login", help="Tigo login username")
    parser.add_argument("--password", help="Tigo login password")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    DEBUG = args.debug

    secrets = load_secret()
    url = fix_url(args.url if args.url else secrets.get("URL", "http://10.24.1.31/cgi-bin/summary_data"))
    username = args.login if args.login else secrets.get("USERNAME", "Tigo")
    password = args.password if args.password else secrets.get("PASSWORD", "$olar")

    timestamp, combined = combine_all(url, username, password)
    if not combined:
        print("[ERROR] No data collected")
        sys.exit(1)

    if args.json_only:
        print(json.dumps({"time": timestamp, "values": combined}, indent=2))
    elif args.csv:
        print(output_csv(timestamp, combined))
    else:
        print(human_readable(timestamp, combined))
