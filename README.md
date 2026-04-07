# AREA 51: Lab Escape

A top-down survival horror game built with Python and Pygame. Explore dark rooms, collect 8 passcodes, and escape before the alien catches you.

---

## Requirements

- Python **3.12** (recommended — Python 3.13+ is not supported by pygame)
- pygame 2.6.1 (installed automatically via requirements.txt)

---

## How to Run

### Option A — Git Clone (recommended)

**1. Clone the repository**
```bash
git clone https://github.com/jaxpacleb/Area-51-Lab-Escape.git
```

**2. Navigate into the folder**
```bash
cd Area-51-Lab-Escape
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```
> If you have multiple Python versions, use: `py -3.12 -m pip install -r requirements.txt`

**4. Run the game**
```bash
python area51.py
```
> Or with a specific version: `py -3.12 area51.py`

---

### Option B — Download ZIP

**1.** Download the ZIP file from GitHub and extract it into a folder of your choice.

**2.** Open the folder in VS Code, then open the terminal inside VS Code.

**3.** Navigate into the project folder:
```bash
cd Area-51-Lab-Escape-main
```
Your terminal path should look like:
```
C:\YourFolder\Area-51-Lab-Escape-main>
```

**4.** Install dependencies:
```bash
pip install -r requirements.txt
```
You should see something like:
```
Requirement already satisfied: pygame in c:\...\site-packages (2.6.1)
```

**5.** Run the game:
```bash
python area51.py
```

---

## How to Play

| Key / Input | Action |
|---|---|
| `W A S D` | Move the scientist |
| Mouse | Aim flashlight |
| Hold `E` | Decrypt a passcode terminal |
| `F` (near exit door) | Open passcode entry panel |
| `Enter` | Submit passcode |
| `Backspace` | Delete last digit |
| `F` (in panel) | Cancel / close panel |
| `Escape` | Quit to menu |

---

## Objective

1. Explore the rooms and find all **8 passcode terminals**
2. Hold `E` near a terminal to decrypt it — watch the progress bar
3. Once all 8 passcodes are collected, find the **gold exit door**
4. Press `F` near the exit door and type the 8-digit code to escape
5. Avoid the **alien** — it patrols the rooms and will chase you if you get too close

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'pygame'`**
> You are likely on Python 3.13+. Install Python 3.12 and run:
> ```bash
> py -3.12 -m pip install pygame
> py -3.12 area51.py
> ```

**Install Python 3.12 via terminal (Windows)**
```bash
winget install Python.Python.3.12
```
Then close and reopen your terminal before running again.

---

## Credits

Pacleb, Germin P. & Clyde Cello
Bachelor of Science in Computer Science — 3B