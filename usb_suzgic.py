#!/usr/bin/env python3
"""
USB Süzgüç: flesh çatylanda diňe rugsat berlen faýl görnüşlerini göçürýär.

Ulanylyşy:
    python3 usb_suzgic.py
"""
import getpass
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

CONFIG_FILE = Path.home() / ".config" / "usb_suzgic" / "config.json"
DEFAULT_CONFIG = {
    "allowed_extensions": [],
    "destination": str(Path.home() / "USB_Import"),
    "unmount_after": True,
}
SKIP_DIRS = {"system volume information", "$recycle.bin", "lost+found"}


# ---------- Sazlamalar ----------
def load_config():
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return {**DEFAULT_CONFIG, **data}
        except (json.JSONDecodeError, OSError):
            print("Sazlama faýly bozulypdyr, täzeden başlaýaryn.")
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_ext(text):
    exts = set()
    for part in text.replace(";", ",").replace(" ", ",").split(","):
        part = part.strip().lower()
        if part:
            exts.add(part if part.startswith(".") else "." + part)
    return sorted(exts)


def set_extensions(cfg):
    print("\nGöçürmäge rugsat berlen faýl giňeltmelerini giriziň.")
    print("Mysal: pdf, txt, jpg, png, docx")
    text = input("Giňeltmeler: ")
    exts = normalize_ext(text)
    if not exts:
        print("Hiç zat girizilmedi, üýtgetmedim.")
        return
    cfg["allowed_extensions"] = exts
    save_config(cfg)
    print("Rugsat berlen:", ", ".join(exts))


def set_destination(cfg):
    text = input(f"Täze papka [{cfg['destination']}]: ").strip()
    if text:
        cfg["destination"] = str(Path(text).expanduser())
        save_config(cfg)
    print("Papka:", cfg["destination"])


def toggle_unmount(cfg):
    cfg["unmount_after"] = not cfg["unmount_after"]
    save_config(cfg)
    print("Göçürenden soň fleşi aýyrmak:", "hawa" if cfg["unmount_after"] else "ýok")


def show_config(cfg):
    exts = ", ".join(cfg["allowed_extensions"]) or "(entek girizilmedi)"
    print("\n--- Häzirki sazlamalar ---")
    print("Rugsat berlen giňeltmeler:", exts)
    print("Göçürilýän papka:", cfg["destination"])
    print("Soňundan fleşi aýyrmak:", "hawa" if cfg["unmount_after"] else "ýok")


def notify(title, text):
    try:
        subprocess.run(["notify-send", title, text], check=False, timeout=5)
    except (FileNotFoundError, subprocess.SubprocessError):
        pass


# ---------- USB ýüze çykarmak ----------
def media_roots():
    user = getpass.getuser()
    return [Path("/media") / user, Path("/run/media") / user]


def current_mounts():
    found = set()
    for root in media_roots():
        if root.is_dir():
            for p in root.iterdir():
                if p.is_dir():
                    found.add(p)
    return found


def unique_target(dest: Path) -> Path:
    if not dest.exists():
        return dest
    i = 1
    while True:
        candidate = dest.with_name(f"{dest.stem}_{i}{dest.suffix}")
        if not candidate.exists():
            return candidate
        i += 1


def process_drive(mount: Path, cfg):
    allowed = set(cfg["allowed_extensions"])
    target_root = Path(cfg["destination"]).expanduser() / mount.name
    copied, skipped = [], []

    print(f"\n>>> Flesh tapyldy: {mount}")
    for path in mount.rglob("*"):
        try:
            rel = path.relative_to(mount)
            if any(part.lower() in SKIP_DIRS for part in rel.parts):
                continue
            if path.is_symlink() or not path.is_file():
                continue
            if path.suffix.lower() in allowed:
                dest = unique_target(target_root / rel)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest)
                copied.append(str(rel))
            else:
                skipped.append(str(rel))
        except OSError as e:
            print(f"Ýalňyşlyk ({path.name}): {e}")

    print(f"Göçürildi: {len(copied)} faýl  ->  {target_root}")
    print(f"Rugsat berilmedi (göçürilmedi): {len(skipped)} faýl")
    for name in skipped[:20]:
        print("   x", name)
    if len(skipped) > 20:
        print(f"   ... we ýene {len(skipped) - 20} faýl")

    notify(
        "USB Süzgüç",
        f"Göçürildi: {len(copied)} faýl\nRugsat berilmedi: {len(skipped)} faýl\nPapka: {target_root}",
    )

    if cfg["unmount_after"]:
        unmount(mount)


def unmount(mount: Path):
    try:
        dev = subprocess.run(
            ["findmnt", "-n", "-o", "SOURCE", str(mount)],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        subprocess.run(["udisksctl", "unmount", "-b", dev], check=True, capture_output=True)
        print("Flesh aýryldy, ony çykaryp bilersiňiz.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Fleşi awtomatiki aýryp bolmady, ony el bilen aýyryň.")


def monitor(cfg):
    if not cfg["allowed_extensions"]:
        print("Ilki rugsat berlen giňeltmeleri giriziň (1-nji menýu).")
        return
    print("\nFlesh garaşylýar... (durmak üçin Ctrl+C)")
    known = current_mounts()
    try:
        while True:
            now = current_mounts()
            for mount in sorted(now - known):
                time.sleep(2)  # fleşiň doly mount bolmagyna garaşýarys
                process_drive(mount, cfg)
                print("\nFlesh garaşylýar...")
            known = current_mounts()
            time.sleep(1.5)
    except KeyboardInterrupt:
        print("\nDurduryldy.")


# ---------- Menýu ----------
def main():
    cfg = load_config()
    if "--watch" in sys.argv:  # awtobaşlatma ýagdaýy: menýusyz işleýär
        monitor(cfg)
        return
    while True:
        show_config(cfg)
        print(
            "\n1) Rugsat berlen giňeltmeleri girizmek\n"
            "2) Göçürilýän papkany üýtgetmek\n"
            "3) Göçürenden soň fleşi aýyrmagy açmak/ýapmak\n"
            "4) Gözegçiligi başlamak\n"
            "0) Çykmak"
        )
        choice = input("Saýlaw: ").strip()
        if choice == "1":
            set_extensions(cfg)
        elif choice == "2":
            set_destination(cfg)
        elif choice == "3":
            toggle_unmount(cfg)
        elif choice == "4":
            monitor(cfg)
        elif choice == "0":
            break


if __name__ == "__main__":
    main()
