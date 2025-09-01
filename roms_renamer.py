import os
import sys
import requests
from bs4 import BeautifulSoup

# ---------------------------
# Cross-platform key reader
# ---------------------------
def get_key():
    try:
        # --- Windows ---
        import msvcrt
        return msvcrt.getch().decode("utf-8").lower()
    except ImportError:
        # --- Linux / macOS ---
        import tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1).lower()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


# ---------------------------
# Download official names from libretro
# ---------------------------
def fetch_official_names(console_name):
    url = f"https://thumbnails.libretro.com/{console_name}/Named_Boxarts/"
    print(f"[INFO] Downloading official roms list for {console_name}...")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"[ERROR] Unable to fetch list from {url}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    names = [a["href"] for a in soup.find_all("a", href=True) if a["href"].endswith(".png")]
    names = [os.path.splitext(name)[0] for name in names]
    print(f"[INFO] Found {len(names)} official rom names")
    return names


# ---------------------------
# Main renamer function
# ---------------------------
def rename_roms(roms_path, console_name):
    official_names = fetch_official_names(console_name)
    if not official_names:
        return

    log_lines = []
    any_changes_needed = False

    for filename in os.listdir(roms_path):
        if not os.path.isfile(os.path.join(roms_path, filename)):
            continue

        base, ext = os.path.splitext(filename)

        # Replace underscores with spaces for better matching
        base_clean = base.replace("_", " ")

        # Find matches
        candidates = [name for name in official_names if base_clean.lower() in name.lower()]
        if not candidates:
            print(f"[WARN] No match found for {filename}")
            log_lines.append(f"[NOT FOUND] {filename}")
            any_changes_needed = True
            continue

        for idx, new_name in enumerate(candidates):
            new_filename = f"{new_name}{ext}"
            old_path = os.path.join(roms_path, filename)
            new_path = os.path.join(roms_path, new_filename)

            print(f"{filename} → {new_filename} [{idx+1}/{len(candidates)}] - (y/n/r/b/d): ", end="", flush=True)
            answer = get_key()
            print(answer)  # echo del tasto premuto

            if answer == "y":
                if os.path.exists(new_path):
                    print(f"[ERROR] {new_filename} already exists! Skipped.")
                    log_lines.append(f"[SKIPPED EXISTS] {filename} → {new_filename}")
                else:
                    os.rename(old_path, new_path)
                    print(f"[OK] Renamed {filename} → {new_filename}")
                    log_lines.append(f"[RENAMED] {filename} → {new_filename}")
                any_changes_needed = True
                break
            elif answer == "d":
                deletable_filename = f"deletable_{filename}"
                deletable_path = os.path.join(roms_path, deletable_filename)
                os.rename(old_path, deletable_path)
                print(f"[OK] Marked as deletable: {filename} → {deletable_filename}")
                log_lines.append(f"[DELETABLE] {filename} → {deletable_filename}")
                any_changes_needed = True
                break
            elif answer == "n":
                print(f"[SKIP] Kept {filename}")
                break
            elif answer == "r":
                continue  # try next candidate
            elif answer == "b":
                print("[BACK] Returning to previous file...")
                break
            else:
                print("[INVALID] Skipped")
                break

    # Summary
    if not any_changes_needed:
        print(f"✅ All files for {console_name} are already correctly named!")
    else:
        log_file = os.path.join(roms_path, "renamer_log.txt")
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("\n".join(log_lines))
        print(f"[INFO] Log written to {log_file}")


# ---------------------------
# Example usage
# ---------------------------
if __name__ == "__main__":
    console_name = input("Enter console name (as on libretro site, e.g. 'Nintendo - Game Boy'): ")
    roms_path = input(f"Where are your roms for {console_name}? (folder path): ")

    if os.path.isdir(roms_path):
        rename_roms(roms_path, console_name)
    else:
        print(f"[ERROR] Path not found: {roms_path}")
