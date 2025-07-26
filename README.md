# Tigo Local Optimizer Monitor

This Python script retrieves real-time data from a **Tigo Energy Gateway** (CCA/TAP) using its local HTTP API.

Gateway kit:
https://www.tigoenergy.com/product/cloud-connect-advanced

It collects:
- **Power** (W)
- **Voltage** (V)
- **Current** (A)
- **RSSI** (dBm)
- **Temperature** (if available, otherwise `N/A`)

---

## Requirements

- Python 3.8 or newer
- Internet access to your Tigo gateway (local network)
- Installed Python modules:
  ```bash
  pip install requests
Configuration
Create a secret.txt file in the same directory with your Tigo gateway parameters:


URL = "http://192.168.1.333/cgi-bin/summary_data"
USERNAME = "Tigo"
PASSWORD = "$olar"
Tip: Replace URL, USERNAME, and PASSWORD with your actual gateway credentials.

Usage
Run the script:

python3 tm.py [OPTIONS]
Options
Option	Description
--json-only	Output only JSON data (raw structure).
--csv	Output CSV formatted data (for spreadsheets or automation).
--human-only	Output human-readable text (default if no format selected).
--url URL	Override gateway URL (defaults to value from secret.txt).
--login USER	Override gateway username (defaults to value from secret.txt).
--password PASS	Override gateway password (defaults to value from secret.txt).
--debug	Enable verbose debug output (shows API calls and dataset content).

Examples
Default human-readable output:

python3 main.py
CSV output to file:

python3 main.py --csv > output.csv
JSON output (for API or script integration):

python3 main.py --json-only
Debugging API calls:

python3 main.py --debug
Custom gateway address & credentials:

python3 main.py --url http://192.168.1.50/cgi-bin/summary_data --login MyUser --password MyPass
Temperature Support
Temperature values are shown as N/A if the local API does not provide optimizer temperature.

Some Tigo gateways only provide temperature via the cloud API.

Output Example
Human-readable:

=== Last measurement (16:30) ===
Panel A1: Power=122 W | Voltage=32 V | Current=3.66 A | Temperature=N/A °C | RSSI=101 dBm
Panel A2: Power=114 W | Voltage=33 V | Current=3.42 A | Temperature=N/A °C | RSSI=105 dBm
Panel A3: Power=111 W | Voltage=33 V | Current=3.33 A | Temperature=N/A °C | RSSI=72 dBm
...
JSON:
json
{
  "time": "16:30",
  "values": {
    "A1": {"power": 122, "voltage": 32, "current": 3.66, "temperature": "N/A", "rssi": 101},
    ...
  }
}

Limitations
Temperature may not be available locally (depends on gateway firmware).

Only tested with Tigo CCA local web interface (firmware 3.x+).

