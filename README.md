# RootForge - Shop Rooting Station (Windows)

A recipe-driven toolkit for rooting Android phones in a repair-shop setting.
It does NOT contain exploits - it automates the standard, legitimate flow
(ADB -> unlock bootloader -> flash Magisk-patched boot image -> verify)
and forces your disclaimers + logging on every session.

## Setup (one time per PC)

1. Install Python 3.10+ from python.org (check "Add to PATH").
2. Download **Android SDK Platform Tools** (Google, official):
   https://developer.android.com/tools/releases/platform-tools
   Extract the folder so you have:  RootForge/platform-tools/adb.exe  (and fastboot.exe)
   RootForge auto-adds it to PATH - no system changes needed.
3. Install USB drivers:
   - Google Pixel / generic:  Google USB Driver (via SDK Manager) or OEM driver
   - Samsung:  Samsung USB Driver ( samsung.com )
   - Xiaomi:   Mi USB Driver
   - MediaTek devices (Tecno/Infinix/Itel):  MediaTek SP Driver (Vcom)
4. Copy **Magisk-vXX.X.apk** onto phones (they can sideload it) - needed for patching boot.img.
5. Run:  python app.py

## Daily workflow

1. On the phone: enable Developer Options (tap Build number 7x),
   turn on USB debugging (and OEM unlocking where it exists).
2. Plug into PC, authorize the USB-debugging prompt ON THE PHONE.
3. RootForge: enter client name -> Detect -> tick disclaimer -> START.
4. Follow any MANUAL steps shown (Odin / Mi Unlock / etc.) - those are
   OEM tools RootForge deliberately does not bundle.
5. Every command is logged to  logs/  with the client name + timestamp.

## Adding models (the important part)

Edit `devices.json`. Copy an existing recipe, key it like "samsung:a15" or
use wildcards "samsung:*". Fill in the `fastboot_flash` image path after you
pull/patch the boot.img for that model. This file becomes your shop's
knowledge base - the more jobs you do, the more models it covers.

## Hard truths your techs must know

- Xiaomi: 168-hour Mi-Unlock wait. No software shortcut exists.
- Samsung: Knox trips permanently (0x0 -> 0x1). Banking apps may break. Flash via Odin only.
- Bootloader unlock wipes data on virtually everything. Tell the client BEFORE.
- If `fastboot devices` shows nothing: drivers. Always drivers first.
