"""
RootForge - shop GUI (Windows / tkinter)
Run:  python app.py
"""
import threading, tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import core, recipes

DISCLAIMER = (
    "By proceeding the client CONFIRMS:\n"
    "  1. They own the device / are authorized to modify it.\n"
    "  2. They were told unlocking will ERASE ALL DATA and may void warranty.\n"
    "  3. Banking/payment apps may stop working after rooting.\n"
    "  4. RootForge logs this session for shop records."
)

class RootForgeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RootForge - Shop Rooting Station")
        self.geometry("820x640")
        self.props = {}
        self.recipe_key = None

        top = ttk.Frame(self, padding=10); top.pack(fill="x")
        ttk.Label(top, text="Client name:").pack(side="left")
        self.client = ttk.Entry(top, width=30); self.client.pack(side="left", padx=5)
        self.log_path = core.new_log("")
        ttk.Label(top, text=f"log: {self.log_path}").pack(side="right")

        mid = ttk.Frame(self, padding=10); mid.pack(fill="x")
        self.btn_detect = ttk.Button(mid, text="1. Detect connected phone", command=self.detect)
        self.btn_detect.pack(side="left")
        self.device_lbl = ttk.Label(mid, text="No device detected", font=("Segoe UI", 10, "bold"))
        self.device_lbl.pack(side="left", padx=15)

        self.warn_box = scrolledtext.ScrolledText(self, height=6, wrap="word", state="disabled")
        self.warn_box.pack(fill="x", padx=10)

        self.agree = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text=DISCLAIMER, variable=self.agree, wraplength=780).pack(padx=10, pady=5, anchor="w")

        self.btn_start = ttk.Button(self, text="2. START ROOTING PROCEDURE", state="disabled",
                                    command=self.start_root)
        self.btn_start.pack(pady=5)

        self.out = scrolledtext.ScrolledText(self, wrap="word", bg="#111", fg="#0f0",
                                             insertbackground="#0f0")
        self.out.pack(fill="both", expand=True, padx=10, pady=10)

    def log(self, msg):
        self.out.insert("end", msg + "\n"); self.out.see("end")
        self.update_idletasks()

    def set_warnings(self, lines):
        self.warn_box.config(state="normal"); self.warn_box.delete("1.0", "end")
        for l in lines: self.warn_box.insert("end", "!! " + l + "\n")
        self.warn_box.config(state="disabled")

    def detect(self):
        core.new_log(self.client.get())
        state = core.get_state()
        if state != "device":
            messagebox.showwarning("No device",
                f"Phone must be ON, booted to Android, USB debugging ON, and this PC authorized.\n"
                f"Current state: {state or 'none'}\n\n"
                "On the phone: Settings > About > tap Build number 7x, then "
                "Developer Options > USB debugging.")
            return
        self.props = core.get_props()
        man = self.props.get("manufacturer", "?").title()
        model = f"{self.props.get('model','?')} ({self.props.get('device','?')})"
        ver = self.props.get("android_version", "?")
        batt = core.get_battery()
        self.device_lbl.config(text=f"{man} {model} | Android {ver} | Battery {batt}%")
        key, recipe = recipes.find_recipe(self.props)
        if recipe:
            self.recipe_key, self.recipe = key, recipe
            warns = recipes.preflight_check(self.props, recipe)
            self.set_warnings([f"Matched recipe: {recipe.get('label', key)}"] + warns)
            self.btn_start.config(state="normal" if self.agree.get() else "disabled")
        else:
            self.recipe = None
            self.set_warnings(["NO RECIPE for this model yet. Add it to devices.json"])
        self.agree.trace_add("write", lambda *_: self.btn_start.config(
            state="normal" if (self.agree.get() and getattr(self, 'recipe', None)) else "disabled"))

    def start_root(self):
        self.btn_start.config(state="disabled"); self.btn_detect.config(state="disabled")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self.log(">>> Starting procedure - DO NOT unplug the phone <<<")
        ok, msg = recipes.execute(self.recipe, log_fn=self.log)
        self.log(("SUCCESS: " if ok else "STOPPED: ") + msg)
        if ok:
            self.log("Verify in Magisk app on the phone, then hand back to client.")

if __name__ == "__main__":
    RootForgeApp().mainloop()
