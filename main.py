import platform
import socket
import getpass
import uuid
import subprocess
import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime
import pytz
import shutil

# Load .env
load_dotenv()

# Read env vars
SNIPEIT_API_URL = os.getenv("SNIPEIT_API_URL")
API_KEY         = os.getenv("SNIPEIT_API_KEY")

# ----------------- CONFIG -----------------
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}
cst_timezone = pytz.timezone('America/Chicago')
cst_time = datetime.now(cst_timezone)
STATUS_ID = 2
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
            output = subprocess.check_output("wmic computersystem get model", shell=True).decode()
            lines = output.strip().split("\n")
            if len(lines) > 1:
                return lines[1].strip()
        elif system == "Darwin":
            output = subprocess.check_output(["sysctl", "-n", "hw.model"]).decode().strip()
            return output
        elif system == "Linux":
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

def get_mac_address():
    mac = uuid.getnode()
    return ':'.join([f'{(mac >> ele) & 0xff:02x}' for ele in range(40, -1, -8)])

def get_ip_address():
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        # Skip loopback addresses and check for actual active IPs
        if ip.startswith("127.") or ip == "0.0.0.0":
            # Use socket to connect to an external server to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # doesn't have to be reachable
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
            except:
                pass
            finally:
                s.close()
        return ip
    except:
        return "Unavailable"

def get_cpu():
    return platform.processor()

def get_ram():
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output("wmic computersystem get TotalPhysicalMemory", shell=True).decode()
            mem_bytes = int(output.strip().split("\n")[1])
        elif platform.system() == "Darwin":
            mem_bytes = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip())
        elif platform.system() == "Linux":
            with open("/proc/meminfo") as f:
                mem_kb = int(next(line for line in f if "MemTotal" in line).split()[1])
                mem_bytes = mem_kb * 1024
        return f"{round(mem_bytes / (1024 ** 3))} GB"
    except:
        return "Unknown"

def get_storage():
    try:
        total, _, _ = shutil.disk_usage("/")
        return f"{round(total / (1024 ** 3))} GB"
    except:
        return "Unknown"
def get_manufacturer():
    try:
        system = platform.system()
        if system == "Windows":
            output = subprocess.check_output("wmic computersystem get manufacturer", shell=True).decode()
            lines = output.strip().split("\n")
            if len(lines) > 1:
                return lines[1].strip()
        elif system == "Darwin":
            return "Apple"
        elif system == "Linux":
            with open("/sys/class/dmi/id/sys_vendor", "r") as f:
                return f.read().strip()
    except:
        return "Unknown"

def find_model(model_name):
    url  = f"{SNIPEIT_API_URL}/models?search={model_name}"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    rows = resp.json().get("rows", [])
    return rows[0] if rows else None

def create_model(model_name):
    url     = f"{SNIPEIT_API_URL}/models"
    DEVICE_FIELDSET_ID = 4
    payload = {
        "name": model_name,
        "fieldset_id": DEVICE_FIELDSET_ID
               }
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
    model_name = get_model_name()
    mac_address = get_mac_address()
    ip_address = get_ip_address()
    cpu = get_cpu()
    ram = get_ram()
    storage = get_storage()
    manufacturer = get_manufacturer()


    print(f"Detected device:\n - Hostname: {hostname}\n - Serial: {serial}\n - Model: {model_name}\n - Manufacturer: {manufacturer}\n - OS: {os_info}\n - User: {user}\n - MAC: {mac_address}\n - IP: {ip_address}\n - CPU: {cpu}\n - RAM: {ram}\n - Storage: {storage}")

    model_info = get_or_create_model_id(model_name)
    asset_data = {
        "name": hostname,
        "asset_tag": serial,
        "serial": serial,
        "model_id": model_info,
        "status_id": STATUS_ID,
        "notes": f"Model: {model_name}, OS: {os_info}, User: {user}, MAC: {mac_address}, IP: {ip_address}, CPU: {cpu}, RAM: {ram}, Storage: {storage}, Last Sync: {cst_time.strftime('%Y-%m-%d %H:%M:%S')}",
        "_snipeit_ram_size_5": ram,
        "_snipeit_mac_address_1": mac_address,
        "_snipeit_ip_address_3": ip_address,
        "_snipeit_os_info_6": os_info,
        "_snipeit_storage_7": storage,
        "_snipeit_cpu_8": cpu,
        "_snipeit_sync_date_9": cst_time.strftime('%Y-%m-%d %H:%M:%S'),
        "_snipeit_user_10": user

    }

    existing_asset = find_existing_asset(serial)

    if existing_asset:
        print("[INFO] Existing asset found. Updating...")
        create_or_update_asset(asset_data, asset_id=existing_asset['id'])
    else:
        print("[INFO] Asset not found. Creating new...")
        create_or_update_asset(asset_data)

if __name__ == "__main__":
    main()
