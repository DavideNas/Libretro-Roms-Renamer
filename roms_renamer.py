import os
import re
import sys
import requests
from bs4 import BeautifulSoup
import urllib.parse
import difflib

# --- function to read a single key (cross-platform) ---
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

# --- Category Dictionary and Console ---
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

# --- Category selection ---
print("Which console category are you interested in? (1-7) :")
for key, (cat_name, _) in CATEGORIES.items():
    print(f"({key}) {cat_name}")
print("(7) Other - Manual Insert")

cat_choice = input("Enter the category number: ").strip()
while cat_choice not in list(CATEGORIES.keys()) + ["7"]:
    cat_choice = input("Invalid selection. Please enter the category number: ").strip()

if cat_choice == "7":
    SYSTEM = input("Enter the name of your console from libretro.com: ").strip()
    if not SYSTEM:
        print("Console name not found !")
        sys.exit(1)
    category_name = "Other"
    consoles = [SYSTEM]
else:
    category_name, consoles = CATEGORIES[cat_choice]
    print(f"\nWhich console {category_name} do you want to analyze? (1-{len(consoles)}) :")
    for i, console in enumerate(consoles, start=1):
        print(f"({i}) {console}")
    console_choice = input("Enter the console number: ").strip()
    while not console_choice.isdigit() or not (1 <= int(console_choice) <= len(consoles)):
        console_choice = input("Invalid selection. Please enter your console number: ").strip()
    SYSTEM = consoles[int(console_choice) - 1]

# --- ROMs Folder ---
LOCAL_ROM_PATH = input(f"\nWhere are your roms for {SYSTEM}? (enter the path on disk) : ").strip()
while not os.path.isdir(LOCAL_ROM_PATH):
    LOCAL_ROM_PATH = input("Invalid path. Please enter an existing folder: ").strip()

REMOTE_URL = f"https://thumbnails.libretro.com/{SYSTEM}/Named_Boxarts/"

# --- download list of names from the site ---
print(f"\n[INFO] Download official rom list for {SYSTEM}...")
resp = requests.get(REMOTE_URL)
soup = BeautifulSoup(resp.text, "html.parser")

remote_names = []
for link in soup.find_all("a"):
    href = link.get("href")
    if href.endswith(".png"):
        rom_name = urllib.parse.unquote(href.replace(".png", ""))
        remote_names.append(rom_name)

print(f"[INFO] Found {len(remote_names)} official names from the site\n")

# --- normalize words in title ---
STOPWORDS = set(["the","for","and","of","your","a","an","in","on","per","di","da","del","della","dei","le","la","un","uno","una"])

def normalize_words(name: str):
    """Removes punctuation, underscores, lowercase letters, parentheses, commas, hyphens, and splits words"""
    name = name.replace("_", " ")
    name = re.sub(r"[!\"#$%&'()*+,./:;<=>?@\[\\\]^_`{|}~-]", " ", name)
    name = re.sub(r"\s+", " ", name)
    name = re.sub(r"\[.*?\]", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    return [w.lower() for w in name.split() if w.strip() and w.lower() not in STOPWORDS]

# --- fuzzy similarity ---
def is_word_similar(a: str, b: str, threshold: float = 0.8) -> bool:
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio() >= threshold

# --- comparison of local ROMs with fuzzy permissive match ---
any_changes_needed = False
log_entries = []

for filename in os.listdir(LOCAL_ROM_PATH):
    name, ext = os.path.splitext(filename)
    local_words = normalize_words(name)

    # --- exact match ---
    if name in remote_names:
        new_name = name + ext
        old_path = os.path.join(LOCAL_ROM_PATH, filename)
        new_path = os.path.join(LOCAL_ROM_PATH, new_name)
        if old_path != new_path:
            os.rename(old_path, new_path)
            print(f"[AUTO] Exact Match → Rename: {filename} -> {new_name}")
            log_entries.append(f"{filename} → {new_name}")
        continue

    # --- permissive advanced search ---
    candidates = []
    for r in remote_names:
        remote_words = normalize_words(r)
        if not remote_words:
            continue
        match_count = sum(1 for rw in remote_words if any(is_word_similar(rw, lw) for lw in local_words))
        if match_count / len(remote_words) >= 0.7:
            candidates.append((r, match_count))

    # --- fallback: word-by-word search if no candidates ---
    if not candidates:
        word_candidates = []
        for r in remote_names:
            remote_words = normalize_words(r)
            single_matches = sum(1 for rw in remote_words if any(is_word_similar(rw, lw) for lw in local_words))
            if single_matches > 0:
                similarity = difflib.SequenceMatcher(None, name.lower(), r.lower()).ratio()
                word_candidates.append((r, single_matches, similarity))
        # sort by number of matched words desc, then similarity desc
        word_candidates.sort(key=lambda x: (-x[1], -x[2]))
        candidates = [wc[0] for wc in word_candidates[:10]]  # limit to top 10

    if not candidates:
        print(f"[WARN] No matches found for {filename}")
        log_entries.append(f"{filename} → No match")
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
                print(f"[WARN] File {new_name} already exists! Use 'd' to append '_deletable_'")
            else:
                os.rename(old_path, new_path)
                print(f"[OK] Rename completed: {filename} -> {new_name}")
                log_entries.append(f"{filename} → {new_name}")
                break
        elif answer == "n":
            print(f"[SKIP] Left unchanged: {filename}")
            log_entries.append(f"{filename} → Left unchanged")
            break
        elif answer == "r":
            idx = (idx + 1) % len(candidates)
        elif answer == "b":
            idx = (idx - 1) % len(candidates)
        elif answer == "d":
            new_name_d = "_deletable_" + new_name
            new_path_d = os.path.join
