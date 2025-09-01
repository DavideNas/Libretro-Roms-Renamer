import os
import re
import sys
import requests
from bs4 import BeautifulSoup
import urllib.parse

# --- funzione per leggere un singolo tasto (cross-platform) ---
def get_single_key() -> str:
    try:
        import msvcrt
        return msvcrt.getch().decode("utf-8").lower()
    except ImportError:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

# --- Dizionario categorie e console ---
CATEGORIES = {
    "1": ("Atari", [
        "Atari - 8-bit", "Atari - 2600", "Atari - 5200", "Atari - 7800",
        "Atari - Jaguar", "Atari - Lynx", "Atari - ST"
    ]),
    "2": ("Microsoft", [
        "DOS", "Microsoft - MSX", "Microsoft - MSX2", "Microsoft - Xbox", "Microsoft - Xbox 360"
    ]),
    "3": ("Nintendo", [
        "Nintendo - Family Computer Disk System", "Nintendo - Game Boy", "Nintendo - Game Boy Advance",
        "Nintendo - Game Boy Color", "Nintendo - GameCube", "Nintendo - Nintendo 3DS", "Nintendo - Nintendo 64",
        "Nintendo - Nintendo 64DD", "Nintendo - Nintendo DS", "Nintendo - Nintendo DSi",
        "Nintendo - Nintendo Entertainment System", "Nintendo - Pokemon Mini", "Nintendo - Satellaview",
        "Nintendo - Sufami Turbo", "Nintendo - Super Nintendo Entertainment System", "Nintendo - Virtual Boy",
        "Nintendo - Wii", "Nintendo - Wii U"
    ]),
    "4": ("Cabinet", [
        "Atomiswave", "FBNeo - Arcade Games", "MAME", "SNK - Neo Geo", "SNK - Neo Geo CD",
        "SNK - Neo Geo Pocket", "SNK - Neo Geo Pocket Color"
    ]),
    "5": ("Sega", [
        "Sega - 32X", "Sega - Dreamcast", "Sega - Game Gear", "Sega - Master System - Mark III",
        "Sega - Mega-CD - Sega CD", "Sega - Mega Drive - Genesis", "Sega - Naomi", "Sega - Naomi 2",
        "Sega - SG-1000", "Sega - Saturn"
    ]),
    "6": ("Sony", [
        "Sony - PlayStation", "Sony - PlayStation 2", "Sony - PlayStation 3", "Sony - PlayStation 4",
        "Sony - PlayStation Portable", "Sony - PlayStation Vita"
    ]),
}

# --- Selezione categoria aggiornata ---
print("Quale categoria di console ti interessa? (1-7) :")
for key, (cat_name, _) in CATEGORIES.items():
    print(f"({key}) {cat_name}")
print("(7) Other - Manual Insert")  # nuova voce

cat_choice = input("Inserisci il numero della categoria: ").strip()
while cat_choice not in list(CATEGORIES.keys()) + ["7"]:
    cat_choice = input("Scelta non valida. Inserisci il numero della categoria: ").strip()

if cat_choice == "7":
    # inserimento manuale
    SYSTEM = input("Enter the name of your console from libretro.com: ").strip()
    if not SYSTEM:
        print("Console name not found !")
        sys.exit(1)
    category_name = "Other"
    consoles = [SYSTEM]
else:
    category_name, consoles = CATEGORIES[cat_choice]

    # --- Selezione console ---
    print(f"\nQuale console {category_name} vuoi analizzare ? (1-{len(consoles)}) :")
    for i, console in enumerate(consoles, start=1):
        print(f"({i}) {console}")
    console_choice = input("Inserisci il numero della console: ").strip()
    while not console_choice.isdigit() or not (1 <= int(console_choice) <= len(consoles)):
        console_choice = input("Scelta non valida. Inserisci il numero della console: ").strip()
    SYSTEM = consoles[int(console_choice) - 1]

# --- Cartella ROMs ---
LOCAL_ROM_PATH = input(f"\nDove sono le tue roms per {SYSTEM}? (inserisci il percorso su disco) : ").strip()
while not os.path.isdir(LOCAL_ROM_PATH):
    LOCAL_ROM_PATH = input("Percorso non valido. Inserisci una cartella esistente: ").strip()

REMOTE_URL = f"https://thumbnails.libretro.com/{SYSTEM}/Named_Boxarts/"

# --- scarica lista nomi dal sito ---
print(f"\n[INFO] Scarico lista rom ufficiali per {SYSTEM}...")
resp = requests.get(REMOTE_URL)
soup = BeautifulSoup(resp.text, "html.parser")

remote_names = []
for link in soup.find_all("a"):
    href = link.get("href")
    if href.endswith(".png"):
        rom_name = urllib.parse.unquote(href.replace(".png", ""))
        remote_names.append(rom_name)

print(f"[INFO] Trovati {len(remote_names)} nomi ufficiali dal sito\n")

# --- normalizzazione parole ---
def normalize_words(name: str):
    """Rimuove underscore, minuscola, parentesi, virgole, trattini e divide in parole"""
    name = name.replace("_", " ")
    name = re.sub(r"[(),\-]", " ", name)
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    return [w.lower() for w in name.split() if w.strip()]

# --- confronto rom locali con match permissivo ---
any_changes_needed = False
log_entries = []

for filename in os.listdir(LOCAL_ROM_PATH):
    name, ext = os.path.splitext(filename)

    # --- match esatto ---
    if name in remote_names:
        new_name = name + ext
        old_path = os.path.join(LOCAL_ROM_PATH, filename)
        new_path = os.path.join(LOCAL_ROM_PATH, new_name)
        if old_path != new_path:
            os.rename(old_path, new_path)
            print(f"[AUTO] Match esatto → Rinomina: {filename} -> {new_name}")
            any_changes_needed = True
            log_entries.append(f"{filename} → {new_name}")
        continue

    # --- ricerca avanzata permissiva ---
    local_words = normalize_words(name)
    candidates = []
    for r in remote_names:
        remote_words = normalize_words(r)
        if not remote_words:
            continue
        # match se almeno 70% delle parole della boxart sono presenti nel nome locale
        match_count = sum(1 for w in remote_words if w in local_words)
        if match_count / len(remote_words) >= 0.7:
            candidates.append(r)

    if not candidates:
        print(f"[WARN] Nessuna corrispondenza trovata per {filename}")
        log_entries.append(f"{filename} → Nessuna corrispondenza")
        any_changes_needed = True
        continue

    any_changes_needed = True
    idx = 0
    while True:
        new_name = candidates[idx] + ext
        old_path = os.path.join(LOCAL_ROM_PATH, filename)
        new_path = os.path.join(LOCAL_ROM_PATH, new_name)

        print(f"{filename} → {new_name} [{idx+1}/{len(candidates)}] - (y/n/r/b/d): ", end="", flush=True)
        answer = get_single_key()
        print(answer)

        if answer == "y":
            if os.path.exists(new_path):
                print(f"[WARN] File {new_name} già esistente! Usa 'd' per aggiungere '_deletable_'")
            else:
                os.rename(old_path, new_path)
                print(f"[OK] Rinomina completata: {filename} -> {new_name}")
            log_entries.append(f"{filename} → {new_name}")
            break
        elif answer == "n":
            print(f"[SKIP] Lasciato invariato: {filename}")
            log_entries.append(f"{filename} → Lasciato invariato")
            break
        elif answer == "r":
            idx = (idx + 1) % len(candidates)
        elif answer == "b":
            idx = (idx - 1) % len(candidates)
        elif answer == "d":
            new_name_d = "_deletable_" + new_name
            new_path_d = os.path.join(LOCAL_ROM_PATH, new_name_d)
            os.rename(old_path, new_path_d)
            print(f"[OK] Rinomina con '_deletable_' completata: {filename} -> {new_name_d}")
            log_entries.append(f"{filename} → {new_name_d}")
            break
        else:
            print("[INFO] Comando non valido, premi y/n/r/b/d.")

# --- messaggio finale ---
if not any_changes_needed:
    print(f"\nTutti i file per {SYSTEM} hanno già i nomi corretti!")

# --- crea log file solo per modifiche o mancanti ---
if log_entries:
    log_file = os.path.join(LOCAL_ROM_PATH, "roms_log.txt")
    with open(log_file, "w", encoding="utf-8") as f:
        for entry in log_entries:
            f.write(entry + "\n")
    print(f"\n[INFO] Log creato (solo modifiche/mancanti): {log_file}")
