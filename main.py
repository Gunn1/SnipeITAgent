import platform
import socket
import getpass
import uuid
import subprocess
import requests
import json
import os

# ----------------- CONFIG -----------------
SNIPEIT_API_URL = "https://REDACTED-INVENTORY-URL"
API_KEY = "REDACTED_API_KEY"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# Optional: IDs from Snipe-IT
MODEL_ID = 1
STATUS_ID = 2
LOCATION_ID = 1
ASSIGNED_USER_ID = None  # Optional

# ------------------------------------------

def get_hostname():
    return socket.gethostname()

def get_os():
    return f"{platform.system()} {platform.release()}"

def get_user():
    return getpass.getuser()
def get_model_name():
    try:
        system = platform.system()

        if system == "Windows":
            # Uses WMIC (Windows Management Instrumentation Command-line)
            output = subprocess.check_output("wmic computersystem get model", shell=True).decode()
            lines = output.strip().split("\n")
            if len(lines) > 1:
                return lines[1].strip()
        
        elif system == "Darwin":
            # macOS: uses sysctl
            output = subprocess.check_output(["sysctl", "-n", "hw.model"]).decode().strip()
            return output

        elif system == "Linux":
            # Reads from standard DMI path (requires no extra packages)
            with open("/sys/class/dmi/id/product_name", "r") as f:
                return f.read().strip()
    except Exception as e:
        return f"UNKNOWN ({e})"
def get_serial_number():
    try:
        system = platform.system()
        if system == "Windows":
            output = subprocess.check_output("wmic bios get serialnumber", shell=True).decode()
            return output.split("\n")[1].strip()
        elif system == "Darwin":
            output = subprocess.check_output(["system_profiler", "SPHardwareDataType"]).decode()
            for line in output.splitlines():
                if "Serial Number" in line:
                    return line.split(":")[1].strip()
        elif system == "Linux":
            with open("/sys/class/dmi/id/product_serial", "r") as f:
                return f.read().strip()
    except Exception as e:
        return f"ERROR-{uuid.getnode()}"
    return "UNKNOWN"
def find_model(model_name):
    url  = f"{SNIPEIT_API_URL}/models?search={model_name}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    rows = resp.json().get("rows", [])
    return rows[0] if rows else None

def create_model(model_name):
    url     = f"{SNIPEIT_API_URL}/models"
    payload = {"name": model_name}
    resp    = requests.post(url, headers=HEADERS, json=payload)
    resp.raise_for_status()
    new = resp.json().get("payload")
    if not new or "id" not in new:
        print(f"[ERROR] Unexpected create_model response: {resp.json()}")
        return None
    return new

def get_or_create_model_id(model_name):
    model = find_model(model_name)
    if model:
        return model["id"]
    print(f"[INFO] Model '{model_name}' not found. Creating it…")
    new = create_model(model_name)
    if not new:
        raise RuntimeError(f"Failed to create model '{model_name}'")
    return new["id"]



def find_existing_asset(serial):
    try:
        response = requests.get(f"{SNIPEIT_API_URL}/hardware?search={serial}", headers=HEADERS)
        results = response.json().get("rows", [])
        return results[0] if results else None
    except Exception as e:
        print(f"[ERROR] Failed to check existing asset: {e}")
        return None

def create_or_update_asset(data, asset_id=None):
    try:
        url = f"{SNIPEIT_API_URL}/hardware"
        method = requests.post

        if asset_id:
            url += f"/{asset_id}"
            data.pop("serial", None)
            method = requests.put

        response = method(url, headers=HEADERS, data=json.dumps(data))
        print(f"[{response.status_code}] {response.json().get('messages', response.text)}")

    except Exception as e:
        print(f"[ERROR] Failed to sync asset: {e}")

def main():
    hostname = get_hostname()
    os_info = get_os()
    user = get_user()
    serial = get_serial_number()

    print(f"Detected device:\n - Hostname: {hostname}\n - Serial: {serial}\n - OS: {os_info}\n - User: {user}")

    model_name = get_model_name()
    model_info = get_or_create_model_id(model_name)
    asset_data = {
        "name": hostname,
        "serial": serial,
        "model_id": model_info,
        "status_id": STATUS_ID,
        "location_id": LOCATION_ID,
        "assigned_to": ASSIGNED_USER_ID,
        "notes": f"Model: {model_name}, OS: {os_info}, User: {user}"
    }

    existing_asset = find_existing_asset(serial)

    if existing_asset:
        print("[INFO] Existing asset found. Updating...")
        create_or_update_asset(asset_data, asset_id=existing_asset['id'])
    else:
        print("[INFO] Asset not found. Creating new...")
        create_or_update_asset(asset_data)

if __name__ == "__main__":
    hostname = get_hostname()
    os_info = get_os()
    user = get_user()
    serial = get_serial_number()
    model = get_model_name()
    print(f"Detected device:\n - Hostname: {hostname}\n - Serial: {serial}\n - OS: {os_info}\n - User: {user}\n - Model: {model}")
    main()
