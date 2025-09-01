# 🎮 Libretro ROMs Renamer

A Python script to **align ROM filenames with Libretro’s official boxart naming convention**, ensuring correct previews in RetroArch.

---

## 🔧 Installation Guide

### 1️⃣ Check Python Installation

Open a terminal and run:

```sh
python --version
```

or (depending on your system):

```sh
py --version
```

👉 If Python is not installed, download it here: [🐍 Official Python Website](https://www.python.org/downloads/)
⚠️ During installation, make sure to check **“Add Python to PATH”**.

---

### 2️⃣ Check pip Installation

Run:

```sh
python -m pip --version
```

or

```sh
py -m pip --version
```

👉 If pip is missing, follow the guide here: [📦 pip Installation Guide](https://packaging.python.org/en/latest/tutorials/installing-packages/).

---

### 3️⃣ Install Required Packages

Install the dependencies with:

```sh
pip install requests
pip install beautifulsoup4
```

✅ Notes:

* `urllib` is included in Python, no installation required.
* Use the correct package name: `beautifulsoup4` (not `BeautifulSoup`).

Check installed packages with:

```sh
pip list
```

---

## ▶️ Run the Script

Once installed, simply run:

```sh
python roms_renamer.py
```

---

## 🕹️ How It Works

1. **Choose a Console Category**

   ```
   (1) Atari
   (2) Microsoft
   (3) Nintendo
   (4) Cabinet
   (5) Sega
   (6) Sony
   ```

2. **Pick a Console**
   Example (Nintendo):

   ```
   (1) Nintendo - Game Boy
   (2) Nintendo - Game Boy Advance
   (3) Nintendo - Super Nintendo Entertainment System
   ...
   ```

3. **Select ROM Folder**
   Example prompt:

   ```
   Where are your roms for Nintendo - Game Boy? :
   ```

4. **Official Name Fetch**
   Script downloads official names from:

   ```
   https://thumbnails.libretro.com/<CONSOLE>/Named_Boxarts/
   ```

5. **Rename Process**

   * ✅ Exact match → file renamed automatically.
   * 🔎 No exact match → script suggests possible candidates.
   * 👤 You decide the action interactively.

---

## 🎛️ Interactive Commands

| Command | Action                               |
| ------- | ------------------------------------ |
| `y`     | ✅ Accept and rename the file         |
| `n`     | ⏭️ Skip (leave file unchanged)       |
| `r`     | 🔽 Show **next candidate**           |
| `b`     | 🔼 Show **previous candidate**       |
| `d`     | 🗑️ Rename but prepend `_deletable_` |

---

## 📝 Logging

After execution, a log file `roms_log.txt` is created in the ROMs folder.
It records only:

* ✨ Renamed files
* ⏭️ Skipped files
* 🗑️ Deletable files
* ❌ Files not found in the official list

⚡ Files already matching the official name are not logged (to keep the log clean).

---

## 📌 Example Run

Local ROM:

```
Super Mario Land.gb
```

Official name:

```
Super Mario Land (World)
```

Script suggestion:

```
Super Mario Land.gb → Super Mario Land (World).gb
```

User input:

```
y
```

✅ File renamed successfully!

