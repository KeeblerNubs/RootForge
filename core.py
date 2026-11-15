"""
RootForge - core device layer
Handles ADB / fastboot communication and device identification.
Requires the Android SDK Platform Tools (adb.exe / fastboot.exe) on PATH
or in a folder named 'platform-tools' next to this file.
"""
import os, re, subprocess, time, logging
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
PLATFORM_TOOLS = os.path.join(HERE, "platform-tools")
if os.path.isdir(PLATFORM_TOOLS):
    os.environ["PATH"] = PLATFORM_TOOLS + os.pathsep + os.environ["PATH"]

LOG_DIR = os.path.join(HERE, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

def new_log(client_name=""):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", client_name) or "session"
    path = os.path.join(LOG_DIR, f"{ts}_{safe}.log")
    logging.basicConfig(filename=path, level=logging.INFO,
                        format="%(asctime)s  %(message)s")
    logging.info(f"=== RootForge session start | client={client_name} ===")
    return path

def run(cmd, timeout=60):
    """Run an adb/fastboot command, log it, return (ok, output)."""
    logging.info("CMD: " + " ".join(cmd))
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        out = (p.stdout + p.stderr).strip()
        logging.info("OUT: " + out.replace("\n", " | "))
        return p.returncode == 0, out
    except subprocess.TimeoutExpired:
        logging.error(f"TIMEOUT after {timeout}s: {' '.join(cmd)}")
        return False, "TIMEOUT"

def adb(*args, timeout=60):
    return run(["adb"] + list(args), timeout)

def fastboot(*args, timeout=120):
    return run(["fastboot"] + list(args), timeout)

# ---------------------------------------------------------------- detection

def wait_for_device(mode="adb", timeout=120):
    """Poll until a device shows up in the requested mode ('adb' or 'fastboot')."""
    lister = adb if mode == "adb" else fastboot
    t0 = time.time()
    while time.time() - t0 < timeout:
        ok, out = lister("devices")
        lines = [l for l in out.splitlines() if l.strip() and not l.startswith("List of")]
        if lines and not lines[0].endswith("offline"):
            return True
        time.sleep(2)
    return False

def get_state():
    """Returns 'device' | 'recovery' | 'fastboot' | 'sideload' | None"""
    ok, out = adb("get-state")
    if ok and out in ("device", "recovery", "sideload"):
        return out
    ok, out = fastboot("devices")
    if ok and out.strip():
        return "fastboot"
    return None

def get_props():
    """Pull key device properties via adb (device must be booted & authorized)."""
    props = {}
    ok, out = adb("shell", "getprop")
    if not ok:
        return props
    wanted = {
        "ro.product.manufacturer": "manufacturer",
        "ro.product.model": "model",
        "ro.product.device": "device",
        "ro.build.display.id": "build_display",
        "ro.build.version.release": "android_version",
        "ro.build.PDA": "pda",            # Samsung firmware id
        "sys.oem_unlock_allowed": "oem_unlock_allowed",
    }
    for line in out.splitlines():
        m = re.match(r'\[(.+?)\]:\s*\[(.*)\]', line.strip())
        if m and m.group(1) in wanted:
            props[wanted[m.group(1)]] = m.group(2)
    # secure status / bootloader state
    ok, out = adb("shell", "getprop", "ro.secure")
    props["ro_secure"] = out.strip()
    ok, out = adb("shell", "getprop", "init.svc.adbd")  # just extra context
    return props

def get_battery():
    ok, out = adb("shell", "dumpsys", "battery")
    m = re.search(r"level:\s*(\d+)", out)
    return int(m.group(1)) if m else None

def is_bootloader_unlocked():
    """Query fastboot (device must be in fastboot mode)."""
    ok, out = fastboot("oem", "device-info")
    m = re.search(r"Device unlocked:\s*(\w+)", out, re.I)
    if m:
        return m.group(1).lower() == "true"
    ok, out = fastboot("getvar", "unlocked")
    m = re.search(r"unlocked:\s*(\w+)", out, re.I)
    return m.group(1).lower() == "true" if m else None

def reboot(mode):
    """mode: 'bootloader', 'recovery', or None (normal reboot)."""
    if mode:
        adb("reboot", mode)
    else:
        adb("reboot")

def unlock_bootloader():
    """Standard fastboot unlock. NOTE: wipes data on most devices."""
    ok, out = fastboot("flashing", "unlock")
    if not ok:
        ok, out = fastboot("oem", "unlock")
    return ok, out
