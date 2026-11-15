"""
RootForge - recipe engine
Each recipe is a JSON entry in devices.json keyed by "manufacturer:device".
Steps are executed in order; every step is logged by core.py.
Add your own recipes as you gain shop experience - that's the whole point.
"""
import os, json, time
import core

HERE = os.path.dirname(os.path.abspath(__file__))
DEVICES_FILE = os.path.join(HERE, "devices.json")

def load_recipes():
    with open(DEVICES_FILE, encoding="utf-8") as f:
        return json.load(f)

def find_recipe(props):
    """Match connected device to a recipe."""
    recs = load_recipes()
    man = (props.get("manufacturer") or "").lower()
    dev = (props.get("device") or "").lower()
    for key in (f"{man}:{dev}", f"*:{dev}", f"{man}:*", "*:*"):
        if key in recs:
            return key, recs[key]
    return None, None

def preflight_check(props, recipe):
    """Returns list of warnings to show the tech BEFORE proceeding."""
    warns = []
    batt = core.get_battery()
    if batt is not None and batt < 50:
        warns.append(f"Battery at {batt}% - charge above 50% first.")
    if recipe.get("wipes_data", True):
        warns.append("Bootloader unlock will FACTORY RESET this device.")
    if recipe.get("knox_void", False):
        warns.append("Samsung Knox will be VOIDED (Samsung Pay/Secure Folder stop working).")
    for w in recipe.get("warnings", []):
        warns.append(w)
    return warns

def execute(recipe, log_fn=print):
    """Run the recipe's step list. log_fn is how the GUI receives messages."""
    steps = recipe.get("steps", [])
    for i, step in enumerate(steps, 1):
        action = step.get("action")
        log_fn(f"[{i}/{len(steps)}] {step.get('label', action)}")

        if action == "wait_adb":
            if not core.wait_for_device("adb", step.get("timeout", 180)):
                return False, "Device did not appear in ADB mode. Check USB drivers & USB debugging."
        elif action == "wait_fastboot":
            if not core.wait_for_device("fastboot", step.get("timeout", 120)):
                return False, "Device did not appear in fastboot mode."
        elif action == "reboot_bootloader":
            core.reboot("bootloader")
        elif action == "reboot_normal":
            core.reboot(None)
        elif action == "unlock_bootloader":
            ok, out = core.unlock_bootloader()
            if not ok:
                return False, f"Unlock command failed: {out}"
            log_fn("  -> Confirm the unlock on the PHONE SCREEN if prompted.")
        elif action == "fastboot_flash":
            img = step.get("image")
            part = step.get("partition", "boot")
            if not img or not os.path.isfile(img):
                return False, f"Image file missing: {img}"
            ok, out = core.fastboot("flash", part, img, timeout=300)
            if not ok:
                return False, f"flash {part} failed: {out}"
        elif action == "manual":
            # Steps that need human/shop tools (Odin, SP Flash, etc.)
            log_fn("  MANUAL STEP - follow your shop SOP:")
            for line in step.get("instructions", []):
                log_fn("    " + line)
            proceed = step.get("auto_continue", False)
            if not proceed:
                return False, "Recipe paused at manual step (edit devices.json to auto_continue)."
        elif action == "verify_root":
            ok, out = core.adb("shell", "which su")
            if not ok or "su" not in out:
                return False, "su binary not found - root verification FAILED."
            log_fn("  -> su found: " + out)
        else:
            return False, f"Unknown action in recipe: {action}"
        time.sleep(step.get("pause", 2))

    return True, "Recipe complete."
