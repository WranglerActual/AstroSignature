#
# ***********************************************
#
# AstroSignature.py — Custom Text Signature Tool for Siril
# Author: Randy Holder
# Contact: randy.holder7@gmail.com
# Version: 1.3.8
#
# Copyright (C) 2026 Randy Holder
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
#
# ***********************************************
#
# Description:
# Adds a two-line italic text signature to the currently loaded Siril image.
# Line 1: Your name + target name (editable each time)
# Line 2: Session details (editable each time)
# Features: 9-position grid selector, font dropdown, independent font size
# sliders for each line, opacity control, and vertical flip correction.
#
# VERTICAL FLIP CORRECTION CHECKBOX:
# Check ON  — for images that have been plate-solved in Siril (Siril flips
#             the image during plate solving). Also applies to smart scopes
#             such as Dwarf 3, Seestar, Vespera whose raw data is natively
#             vertically flipped. This is the correct setting for most users.
# Check OFF — for images whose pixel data is correctly oriented and has NOT
#             been flipped by Siril. If unsure, try ON first.
#
# IMPORTANT: The signature is permanently written into the image pixel data.
# Always save the signed image as a NEW file after applying to preserve
# your unsigned master image.
#
# Tested with Siril 1.4.2 on Windows. Requires sirilpy >= 0.6.37.
# Should work on any telescope/camera combination supported by Siril.
#
# Version History:
# 1.0.0 - Initial release — two-line text signature, flip correction
# 1.1.0 - Added 9-position grid selector (dropdown)
# 1.2.0 - Added font selection dropdown from available Windows fonts
# 1.3.0 - Added independent font size sliders for Line 1 and Line 2
#          QA verified across all 9 positions and both flip states
# 1.3.1 - Cross-platform font support — Windows, macOS, Linux
# 1.3.2 - Preserve source bit depth/range for FITS, 16-bit TIFF, and 8-bit JPEG/TIFF
# 1.3.3 - Fix 8-bit JPEG write-back by sending normalized float pixel data to Siril
# 1.3.4 - Fix blank output for TIFF inputs; smart image pipeline handles
#          HW/CHW/HWC layouts and 8-bit/16-bit/float ranges automatically
#          Enhancement credit: Don Heffernan (Issue #7)
# 1.3.5 - GUI version label corrected; default fields restored to author defaults
# 1.3.6 - Generic default field values for friendlier first-run experience
#          (pipe-separated placeholders guide new users on formatting)
# 1.3.7 - Dialog window made resizable (minsize 620x680) to prevent clipping
#          on high-DPI displays or systems with large UI fonts (Issue #7)
# 1.3.8 - Settings persistence: last-used values saved to astrosignature.json
#          and restored on next launch; profile-ready JSON structure for
#          future named profiles (Issue #2)
#
# ***********************************************

VERSION = "1.3.8"

import sys
import os

# ── Siril interface ───────────────────────────────────────────────────────────
try:
    import sirilpy as s
    if not s.check_module_version('>=0.6.37'):
        print("Error: requires sirilpy module >= 0.6.37 (Siril >= 1.4.0)")
        sys.exit(1)
    from sirilpy import SirilError
    s.ensure_installed("numpy", "Pillow")
except ImportError as e:
    print(f"ERROR: Could not import sirilpy: {e}")
    sys.exit(1)

import numpy as np
from PIL import Image, ImageDraw, ImageFont


# ── Settings persistence ──────────────────────────────────────────────────────
SETTINGS_FILENAME = "astrosignature.json"

DEFAULTS = {
    "name":     "Your Name  |  Target Name",
    "session":  "Your Location  |  Exposure  |  Subs  |  Filter",
    "opacity":  40,
    "flipped":  True,
    "position": "Bottom Right",
    "font":     None,   # None -> resolved to Georgia Italic / OS default at runtime
    "size1":    28,
    "size2":    22,
}

def _config_path():
    """Return the config file path, preferring the script directory with a home-dir fallback."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    primary = os.path.join(script_dir, SETTINGS_FILENAME)
    try:
        test = primary + ".tmp"
        with open(test, "w") as f:
            f.write("")
        os.remove(test)
        return primary
    except OSError:
        return os.path.join(os.path.expanduser("~"), SETTINGS_FILENAME)


def load_settings():
    """Load last-used settings from JSON config. Returns merged dict with DEFAULTS as fallback."""
    import json
    path = _config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            saved = data.get("last_used", {})
            merged = dict(DEFAULTS)
            merged.update({k: v for k, v in saved.items() if k in DEFAULTS})
            print(f"Settings loaded from: {path}")
            return merged
        except Exception as e:
            print(f"WARNING: Could not read settings file ({e}) -- using defaults.")
    return dict(DEFAULTS)


def save_settings(params, font_name):
    """Persist last-used settings to JSON config. Called only on Apply."""
    import json
    path = _config_path()
    try:
        existing = {}
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                existing = {}

        existing["last_used"] = {
            "name":     params["name"],
            "session":  params["session"],
            "opacity":  params["opacity"],
            "flipped":  params["flipped"],
            "position": params["position"],
            "font":     font_name,
            "size1":    params["size1"],
            "size2":    params["size2"],
        }
        if "profiles" not in existing:
            existing["profiles"] = {}

        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)
        print(f"Settings saved to: {path}")
    except Exception as e:
        print(f"WARNING: Could not save settings ({e})")

# ── GUI dialog ────────────────────────────────────────────────────────────────
def get_user_input():
    try:
        import tkinter as tk
        from tkinter import messagebox

        # ── Load last-used settings ──
        cfg = load_settings()

        root = tk.Tk()
        root.title("AstroSignature Tool v1.3.8")
        root.resizable(True, True)
        root.configure(bg="#2b2b2b")

        root.update_idletasks()
        w, h = 620, 680
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        root.geometry(f"{w}x{h}+{x}+{y}")
        root.minsize(620, 680)

        # ── Corrected: version label matches VERSION constant ──
        tk.Label(root, text="AstroSignature Tool  v1.3.8",
                bg="#1a1a2e", fg="#c9a84c",
                font=("Arial", 13, "bold"), pady=10).pack(fill="x")

        tk.Label(root, text="Line 1 — Your name + Target  (use  |  to separate fields):",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(12, 0))

        # ── Pre-populate from saved settings (falls back to generic defaults on first run) ──
        name_var = tk.StringVar(value=cfg["name"])
        name_entry = tk.Entry(root, textvariable=name_var, width=58,
                bg="#3c3f41", fg="#ffffff",
                font=("Arial", 10),
                relief="flat", bd=4)
        name_entry.pack(padx=20, pady=(2, 0))

        tk.Label(root, text="Line 2 — Session details  (use  |  to separate fields):",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(10, 0))

        session_var = tk.StringVar(value=cfg["session"])
        session_entry = tk.Entry(root, textvariable=session_var, width=58,
                                 bg="#3c3f41", fg="#ffffff",
                                 font=("Arial", 10), relief="flat", bd=4)
        session_entry.pack(padx=20, pady=(2, 0))
        session_entry.focus()
        session_entry.select_range(0, "end")

        tk.Label(root, text="Opacity (%):",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(10, 0))
        opacity_var = tk.IntVar(value=cfg["opacity"])
        oframe = tk.Frame(root, bg="#2b2b2b")
        oframe.pack(fill="x", padx=20)
        tk.Scale(oframe, from_=10, to=80, orient="horizontal",
                variable=opacity_var, bg="#2b2b2b", fg="#ffffff",
                highlightthickness=0, troughcolor="#3c3f41",
                activebackground="#c9a84c", length=400).pack(side="left")
        tk.Label(oframe, textvariable=opacity_var,
                bg="#2b2b2b", fg="#c9a84c",
                font=("Arial", 10, "bold"), width=3).pack(side="left", padx=4)

        # Flip checkbox
        flipped_var = tk.BooleanVar(value=cfg["flipped"])
        tk.Checkbutton(root,
                      text="Apply vertical flip correction\n"
                           "(ON for plate-solved images and smart scopes — Dwarf 3, Seestar, Vespera etc.)",
                      variable=flipped_var,
                      bg="#2b2b2b", fg="#ffffff", selectcolor="#3c3f41",
                      activebackground="#2b2b2b", activeforeground="#c9a84c",
                      font=("Arial", 9), justify="left").pack(anchor="w", padx=20, pady=(8, 0))

        # Position selector — dropdown
        tk.Label(root, text="Signature Position:",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(12, 4))

        pos_var = tk.StringVar(value=cfg["position"])
        positions = [
            "Top Left", "Top Center", "Top Right",
            "Middle Left", "Center", "Middle Right",
            "Bottom Left", "Bottom Center", "Bottom Right"
        ]
        pos_dropdown = tk.OptionMenu(root, pos_var, *positions)
        pos_dropdown.config(bg="#3c3f41", fg="#ffffff", font=("Arial", 10),
                           activebackground="#4a6fa5", activeforeground="#ffffff",
                           highlightthickness=0, relief="flat", width=20)
        pos_dropdown["menu"].config(bg="#3c3f41", fg="#ffffff",
                                   activebackground="#4a6fa5", activeforeground="#ffffff",
                                   font=("Arial", 10))
        pos_dropdown.pack(anchor="w", padx=20, pady=(0, 4))

        # Font selector dropdown
        tk.Label(root, text="Font:",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(10, 4))

        available_fonts = get_available_fonts()
        font_names = [f[0] for f in available_fonts]
        font_paths = {f[0]: f[1] for f in available_fonts}

        # Resolve saved font name; fall back to Georgia Italic then first available
        default_font = font_names[0]
        for name in font_names:
            if "Georgia" in name and "Bold" not in name:
                default_font = name
                break
        saved_font = cfg.get("font")
        if saved_font and saved_font in font_names:
            default_font = saved_font

        font_var = tk.StringVar(value=default_font)
        font_dropdown = tk.OptionMenu(root, font_var, *font_names)
        font_dropdown.config(bg="#3c3f41", fg="#ffffff", font=("Arial", 10),
                            activebackground="#4a6fa5", activeforeground="#ffffff",
                            highlightthickness=0, relief="flat", width=25)
        font_dropdown["menu"].config(bg="#3c3f41", fg="#ffffff",
                                    activebackground="#4a6fa5", activeforeground="#ffffff",
                                    font=("Arial", 10))
        font_dropdown.pack(anchor="w", padx=20, pady=(0, 4))

        # Font size controls — Line 1 and Line 2 independent
        tk.Label(root, text="Font Size — Line 1 (Name / Target):",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(10, 0))
        size1_var = tk.IntVar(value=cfg["size1"])
        sf1 = tk.Frame(root, bg="#2b2b2b")
        sf1.pack(fill="x", padx=20)
        tk.Scale(sf1, from_=12, to=120, orient="horizontal",
                variable=size1_var, bg="#2b2b2b", fg="#ffffff",
                highlightthickness=0, troughcolor="#3c3f41",
                activebackground="#c9a84c", length=440).pack(side="left")
        tk.Label(sf1, textvariable=size1_var,
                bg="#2b2b2b", fg="#c9a84c",
                font=("Arial", 10, "bold"), width=3).pack(side="left", padx=4)

        tk.Label(root, text="Font Size — Line 2 (Session Details):",
                bg="#2b2b2b", fg="#ffffff",
                font=("Arial", 9)).pack(anchor="w", padx=20, pady=(8, 0))
        size2_var = tk.IntVar(value=cfg["size2"])
        sf2 = tk.Frame(root, bg="#2b2b2b")
        sf2.pack(fill="x", padx=20)
        tk.Scale(sf2, from_=12, to=120, orient="horizontal",
                variable=size2_var, bg="#2b2b2b", fg="#ffffff",
                highlightthickness=0, troughcolor="#3c3f41",
                activebackground="#c9a84c", length=440).pack(side="left")
        tk.Label(sf2, textvariable=size2_var,
                bg="#2b2b2b", fg="#c9a84c",
                font=("Arial", 10, "bold"), width=3).pack(side="left", padx=4)

        result = {"ok": False}

        # Save warning
        warn_frame = tk.Frame(root, bg="#3a1a00", bd=1, relief="solid")
        warn_frame.pack(fill="x", padx=20, pady=(12, 0))
        tk.Label(warn_frame,
                text="⚠  The signature is permanently baked into the image pixels.\n"
                     "After applying, save as a NEW file — do not overwrite your master.",
                bg="#3a1a00", fg="#ffcc66",
                font=("Arial", 9, "bold"), pady=6, justify="center").pack()

        def on_apply():
            if not session_var.get().strip():
                messagebox.showwarning("Missing", "Please enter session details.")
                return
            chosen_font_name = font_var.get()
            result.update({
                "ok": True,
                "name": name_var.get().strip(),
                "session": session_var.get().strip(),
                "opacity": opacity_var.get(),
                "flipped": flipped_var.get(),
                "position": pos_var.get(),
                "font_path": font_paths[chosen_font_name],
                "font_name": chosen_font_name,
                "size1": size1_var.get(),
                "size2": size2_var.get()
            })
            save_settings(result, chosen_font_name)
            root.destroy()

        def on_cancel():
            root.destroy()

        bframe = tk.Frame(root, bg="#2b2b2b")
        bframe.pack(pady=14)
        tk.Button(bframe, text="  Apply Signature  ", command=on_apply,
                 bg="#4a6fa5", fg="white", font=("Arial", 10, "bold"),
                 relief="flat", padx=12, pady=6,
                 cursor="hand2").pack(side="left", padx=8)
        tk.Button(bframe, text="  Cancel  ", command=on_cancel,
                 bg="#555555", fg="white", font=("Arial", 10),
                 relief="flat", padx=12, pady=6,
                 cursor="hand2").pack(side="left", padx=8)

        root.mainloop()
        return result if result["ok"] else None

    except Exception as e:
        print(f"ERROR opening dialog: {e}")
        return None


def get_font_dirs():
    """Return a list of font directories for the current OS."""
    import platform
    system = platform.system()
    if system == "Windows":
        return ["C:/Windows/Fonts/"]
    elif system == "Darwin":  # macOS
        return [
            "/Library/Fonts/",
            "/System/Library/Fonts/",
            os.path.expanduser("~/Library/Fonts/"),
        ]
    else:  # Linux
        return [
            "/usr/share/fonts/",
            "/usr/local/share/fonts/",
            os.path.expanduser("~/.fonts/"),
            os.path.expanduser("~/.local/share/fonts/"),
        ]


def get_available_fonts():
    """Scan system font directories and return available (display_name, file_path) tuples."""
    import platform
    system = platform.system()

    # Curated font candidates per OS
    if system == "Windows":
        candidates = [
            ("Georgia Italic",              "georgiai.ttf"),
            ("Georgia Bold Italic",         "georgiaz.ttf"),
            ("Times New Roman Italic",      "timesi.ttf"),
            ("Times New Roman Bold Italic", "timesbi.ttf"),
            ("Palatino Italic",             "palatinoi.ttf"),
            ("Garamond Italic",             "garamondi.ttf"),
            ("Calibri Italic",              "calibrii.ttf"),
            ("Calibri Bold Italic",         "calibriz.ttf"),
            ("Cambria Italic",              "cambriai.ttf"),
            ("Cambria Bold Italic",         "cambriaz.ttf"),
            ("Arial Italic",                "ariali.ttf"),
            ("Arial Bold Italic",           "arialbi.ttf"),
            ("Verdana Italic",              "verdanai.ttf"),
            ("Verdana Bold Italic",         "verdanaz.ttf"),
            ("Trebuchet Italic",            "trebucit.ttf"),
            ("Book Antiqua Italic",         "bkanti.ttf"),
            ("Century Gothic Italic",       "gothici.ttf"),
            ("Comic Sans MS Italic",        "comicsi.ttf"),
            ("Segoe UI Italic",             "segoeuii.ttf"),
            ("Consolas Italic",             "consolasbi.ttf"),
        ]
    elif system == "Darwin":  # macOS
        candidates = [
            ("Georgia Italic",              "Georgia Italic.ttf"),
            ("Georgia Bold Italic",         "Georgia Bold Italic.ttf"),
            ("Times New Roman Italic",      "Times New Roman Italic.ttf"),
            ("Times New Roman Bold Italic", "Times New Roman Bold Italic.ttf"),
            ("Palatino Italic",             "Palatino.ttc"),
            ("Baskerville Italic",          "Baskerville.ttc"),
            ("Didot Italic",                "Didot.ttc"),
            ("Garamond Italic",             "EBGaramond-Italic.ttf"),
            ("Helvetica Italic",            "Helvetica.ttc"),
            ("Arial Italic",                "Arial Italic.ttf"),
            ("Arial Bold Italic",           "Arial Bold Italic.ttf"),
            ("Verdana Italic",              "Verdana Italic.ttf"),
            ("Verdana Bold Italic",         "Verdana Bold Italic.ttf"),
            ("Trebuchet Italic",            "Trebuchet MS Italic.ttf"),
            ("Futura Italic",               "Futura.ttc"),
            ("Optima Italic",               "Optima.ttc"),
            ("Comic Sans MS Italic",        "Comic Sans MS Italic.ttf"),
        ]
    else:  # Linux
        candidates = [
            ("DejaVu Serif Italic",         "DejaVuSerif-Italic.ttf"),
            ("DejaVu Serif Bold Italic",    "DejaVuSerif-BoldItalic.ttf"),
            ("DejaVu Sans Italic",          "DejaVuSans-Oblique.ttf"),
            ("DejaVu Sans Bold Italic",     "DejaVuSans-BoldOblique.ttf"),
            ("Liberation Serif Italic",     "LiberationSerif-Italic.ttf"),
            ("Liberation Serif Bold Italic","LiberationSerif-BoldItalic.ttf"),
            ("Liberation Sans Italic",      "LiberationSans-Italic.ttf"),
            ("Liberation Sans Bold Italic", "LiberationSans-BoldItalic.ttf"),
            ("FreeSerif Italic",            "FreeSerif.ttf"),
            ("FreeSans Italic",             "FreeSans.ttf"),
            ("Ubuntu Italic",               "Ubuntu-RI.ttf"),
            ("Ubuntu Bold Italic",          "Ubuntu-BI.ttf"),
            ("Noto Serif Italic",           "NotoSerif-Italic.ttf"),
            ("Noto Sans Italic",            "NotoSans-Italic.ttf"),
        ]

    font_dirs = get_font_dirs()
    available = []

    for name, filename in candidates:
        for font_dir in font_dirs:
            # Search recursively for Linux which has subdirectories
            if system == "Linux":
                for root_dir, dirs, files in os.walk(font_dir):
                    if filename in files:
                        available.append((name, os.path.join(root_dir, filename)))
                        break
            else:
                path = os.path.join(font_dir, filename)
                if os.path.exists(path):
                    available.append((name, path))
                    break

    # Fallback — use Pillow's default if nothing found
    if not available:
        available.append(("Default Font", "default"))
        print("WARNING: No system fonts found — using Pillow default font.")

    return available


def find_font(size, font_path=None):
    """Load a font by path, with cross-platform fallback chain."""
    # Try the requested font first
    if font_path and font_path != "default" and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass

    # Cross-platform fallback chain
    import platform
    system = platform.system()

    if system == "Windows":
        fallbacks = [
            "C:/Windows/Fonts/georgiai.ttf",
            "C:/Windows/Fonts/timesi.ttf",
            "C:/Windows/Fonts/calibrii.ttf",
            "C:/Windows/Fonts/ariali.ttf",
            "C:/Windows/Fonts/verdanai.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    elif system == "Darwin":
        fallbacks = [
            "/Library/Fonts/Arial Italic.ttf",
            "/Library/Fonts/Verdana Italic.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
        ]
    else:  # Linux
        fallbacks = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSerif.ttf",
        ]

    for path in fallbacks:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue

    # Final fallback — Pillow default (no path needed)
    print(f"WARNING: No fonts found — using Pillow default (no size control).")
    return ImageFont.load_default()


def _data_to_hwc_rgb_float01(data):
    """Return (HWC RGB float image in 0..1, metadata needed to restore original layout/range).

    Handles all image layouts Siril may deliver:
      HW       — 2D grayscale
      CHW      — Siril native channel-first (1 or 3 channels)
      HWC      — channel-last (1, 3, or 4 channels)

    Also handles all common bit depths:
      uint8    — standard 8-bit
      uint16   — 16-bit TIFF / FITS
      float32  — normalized FITS float
      uint16 container with 8-bit values — JPEG loaded by Siril into wide array
    """
    arr = np.asarray(data)
    meta = {
        "shape": arr.shape,
        "dtype": arr.dtype,
        "layout": "unknown",
        "channels": None,
        "scale": 1.0,
        "output_scale": 1.0,
        "float_input": np.issubdtype(arr.dtype, np.floating),
        "looks_8bit": False,
    }

    # Identify Siril/Python image layout
    if arr.ndim == 2:
        meta["layout"] = "HW"
        meta["channels"] = 1
        work = arr[..., None]
    elif arr.ndim == 3 and arr.shape[0] in (1, 3):
        meta["layout"] = "CHW"
        meta["channels"] = arr.shape[0]
        work = np.transpose(arr, (1, 2, 0))
    elif arr.ndim == 3 and arr.shape[-1] in (1, 3, 4):
        meta["layout"] = "HWC"
        meta["channels"] = arr.shape[-1]
        work = arr[..., :3]
    else:
        raise ValueError(f"Unsupported image array shape from Siril: {arr.shape}")

    work = work.astype(np.float32, copy=False)

    # Determine source range.
    # Siril can load 8-bit JPEGs into a uint16 container while actual pixel
    # values remain 0..255. Inspecting the actual finite max (not just dtype)
    # lets us detect this and avoid scaling errors that produce blank output.
    # The same logic correctly identifies 16-bit TIFFs (max near 65535).
    finite = work[np.isfinite(work)]
    maxv = float(finite.max()) if finite.size else 1.0

    if np.issubdtype(arr.dtype, np.integer):
        dtype_max = float(np.iinfo(arr.dtype).max)
        if maxv <= 255.0 and dtype_max > 255.0:
            # 8-bit image (JPEG) stored in a wider Siril array
            scale = 255.0
            output_scale = dtype_max
            meta["looks_8bit"] = True
            print(f"  Image range detected: 8-bit values in {arr.dtype} container (JPEG-like)")
        else:
            # True 16-bit (TIFF/FITS) or 8-bit uint8
            scale = dtype_max
            output_scale = dtype_max
            print(f"  Image range detected: {arr.dtype} full range (scale={dtype_max:.0f})")
    else:
        # Float input (FITS float32 etc.)
        if maxv <= 1.0:
            scale = 1.0
            output_scale = 1.0
        elif maxv <= 255.0:
            scale = 255.0
            output_scale = 1.0
            meta["looks_8bit"] = True
        elif maxv <= 65535.0:
            scale = 65535.0
            output_scale = 1.0
        else:
            scale = maxv
            output_scale = 1.0
        print(f"  Image range detected: float input, max={maxv:.4f}, scale={scale:.0f}")

    meta["scale"] = scale
    meta["output_scale"] = output_scale

    work01 = np.clip(work / scale, 0.0, 1.0)

    # Pillow drawing is RGB. For mono images, make temporary RGB.
    if work01.shape[-1] == 1:
        work01 = np.repeat(work01, 3, axis=-1)
    elif work01.shape[-1] >= 3:
        work01 = work01[..., :3]

    return work01, meta


def _hwc_rgb_float01_to_layout(img01, meta, *, scaled=True):
    """Convert HWC RGB float 0..1 data back to the original Siril layout.

    scaled=True  — preserve the original dtype/range (default, used for FITS/TIFF)
    scaled=False — return float32 normalized 0..1 in the original layout
                   (used for 8-bit JPEG write-back to avoid uint8 black-image bug)
    """
    img01 = np.clip(img01, 0.0, 1.0).astype(np.float32, copy=False)

    # If the source was mono, convert the signed RGB result back to luminance
    if meta["channels"] == 1:
        out_hwc = (0.2126 * img01[..., 0] +
                   0.7152 * img01[..., 1] +
                   0.0722 * img01[..., 2])[..., None].astype(np.float32, copy=False)
    else:
        out_hwc = img01

    if scaled:
        out = out_hwc * float(meta.get("output_scale", meta["scale"]))
        if meta["float_input"]:
            out = out.astype(meta["dtype"], copy=False)
        else:
            info = np.iinfo(meta["dtype"])
            out = np.rint(out)
            out = np.clip(out, info.min, info.max).astype(meta["dtype"])
    else:
        out = out_hwc.astype(np.float32, copy=False)

    if meta["layout"] == "HW":
        return out[..., 0]
    if meta["layout"] == "CHW":
        return np.transpose(out, (2, 0, 1))
    if meta["layout"] == "HWC":
        return out

    raise ValueError(f"Unsupported original layout: {meta['layout']}")


def _hwc_rgb_float01_to_original_layout(img01, meta):
    """Convert HWC RGB float 0..1 data back to original Siril layout/range/dtype."""
    return _hwc_rgb_float01_to_layout(img01, meta, scaled=True)


def apply_signature(siril, line1, line2, opacity_pct, flipped=True, position="Bottom Right", font_path=None, size1=28, size2=22):
    print(f"Applying signature — opacity {opacity_pct}% — position: {position} — font: {os.path.basename(font_path) if font_path else 'default'} — sizes: {size1}/{size2}")

    try:
        with siril.image_lock():
            fit = siril.get_image(True)
            if fit is None:
                print("ERROR: No image loaded in Siril.")
                return False

            img_hwc, meta = _data_to_hwc_rgb_float01(fit.data)
            print(f"  Image shape from Siril: {meta['shape']}; dtype: {meta['dtype']}; detected scale: {meta['scale']}")

            height, width = img_hwc.shape[:2]

            pil_size = (width, height)

            # Font loading
            font1 = find_font(size1, font_path)
            font2 = find_font(size2, font_path)

            # Measure text
            dummy_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
            bb1 = dummy_draw.textbbox((0, 0), line1, font=font1)
            bb2 = dummy_draw.textbbox((0, 0), line2, font=font2)
            tw1, th1 = bb1[2] - bb1[0], bb1[3] - bb1[1]
            tw2, th2 = bb2[2] - bb2[0], bb2[3] - bb2[1]
            gap = max(6, int(height * 0.005))

            print(f"  Flip correction: {flipped}")

            pos = position.lower()
            mx = int(width  * 0.025)
            my = int(height * 0.025)
            block_h = th1 + gap + th2

            # Horizontal alignment
            if "left" in pos:
                if flipped:
                    x1 = mx
                    x2 = mx
                else:
                    x1 = width - mx - tw1
                    x2 = width - mx - tw2
            elif "right" in pos:
                if flipped:
                    x1 = width - mx - tw1
                    x2 = width - mx - tw2
                else:
                    x1 = mx
                    x2 = mx
            else:  # center
                x1 = (width - tw1) // 2
                x2 = (width - tw2) // 2

            # Vertical alignment
            if "top" in pos:
                y1 = my
                y2 = y1 + th1 + gap
            elif "bottom" in pos:
                y1 = height - my - block_h
                y2 = y1 + th1 + gap
            else:  # middle / center
                y1 = (height - block_h) // 2
                y2 = y1 + th1 + gap

            # Draw text on a transparent overlay
            overlay = Image.new("RGBA", pil_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            alpha = int(255 * opacity_pct / 100.0)
            shadow_alpha = max(20, int(alpha * 0.35))

            draw.text((x1 + 1, y1 + 1), line1, font=font1, fill=(0, 0, 0, shadow_alpha))
            draw.text((x2 + 1, y2 + 1), line2, font=font2, fill=(0, 0, 0, shadow_alpha))
            draw.text((x1, y1), line1, font=font1, fill=(255, 255, 255, alpha))
            draw.text((x2, y2), line2, font=font2, fill=(255, 255, 255, alpha))

            if flipped:
                print("  Plate-solve flip detected — correcting text orientation.")
                overlay = overlay.transpose(Image.FLIP_TOP_BOTTOM)
            # Note: no horizontal flip applied when flipped=False.
            # The overlay is drawn directly without mirroring for unflipped images.

            # Blend overlay into normalized float image
            overlay_np = np.asarray(overlay, dtype=np.float32) / 255.0
            overlay_rgb = overlay_np[..., :3]
            overlay_alpha = overlay_np[..., 3:4]
            result_hwc = img_hwc * (1.0 - overlay_alpha) + overlay_rgb * overlay_alpha

            # Restore original Siril layout, then write back.
            # JPEG/8-bit path: write normalized float32 to avoid black-image
            # artifacts that occur when uint8 data is written into a 16-bit container.
            if meta.get("looks_8bit"):
                print("  8-bit/JPEG-like image detected — writing normalized float pixel data for safe save.")
                result_data = _hwc_rgb_float01_to_layout(result_hwc, meta, scaled=False)
                if result_data.shape != fit.data.shape:
                    raise ValueError(f"Internal shape mismatch: result {result_data.shape}, original {fit.data.shape}")
                siril.set_image_pixeldata(result_data)
            else:
                # Standard path — FITS, 16-bit TIFF, float FITS
                result_data = _hwc_rgb_float01_to_original_layout(result_hwc, meta)
                if result_data.shape != fit.data.shape:
                    raise ValueError(f"Internal shape mismatch: result {result_data.shape}, original {fit.data.shape}")
                fit.data[:] = result_data
                siril.set_image_pixeldata(fit.data)

            print("Signature applied successfully.")
            print(f"  Line 1 : {line1}")
            print(f"  Line 2 : {line2}")
            return True

    except Exception as e:
        print(f"ERROR applying signature: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 55)
    print("  AstroSignature Tool v1.3.8 — Randy Holder")
    print("  Two-line text signature for Siril 1.4+")
    print("=" * 55)

    params = get_user_input()
    if params is None:
        print("Cancelled.")
        return

    siril = s.SirilInterface()
    try:
        siril.connect()
        print("Connected to Siril.")
        success = apply_signature(siril, params["name"],
                                  params["session"], params["opacity"],
                                  params["flipped"], params["position"],
                                  params["font_path"], params["size1"],
                                  params["size2"])
        if success:
            print("")
            print("Done! Save as a new file to preserve your unsigned master.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        siril.disconnect()


if __name__ == "__main__":
    main()
