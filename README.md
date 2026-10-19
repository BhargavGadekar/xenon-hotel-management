# XENON · Palace & Residences
### Luxury Hotel & Lodge Point of Sale (POS) Operating System

An **OS-Agnostic** hotel and lodge Point of Sale (POS) system designed to run seamlessly on **Linux, Windows, and macOS**. Inspired by the quiet palatial luxury of **The Leela Palace** and the fluid cursive typography of **Lemon and Olive**.

---

## 💻 Cross-Platform / OS-Agnostic Support

The entire codebase is built with zero hardcoded OS-specific assumptions:
- **`pathlib.Path` & Path Normalization**: All path resolutions in Python dynamically handle POSIX `/`, Windows `\`, and spaces in directory names.
- **Universal Python Launcher (`run.py`)**: Can be run directly with `python run.py` on any platform (Linux, macOS, Windows, BSD, WSL).
- **Dedicated Native Scripts**:
  - **Linux / macOS / BSD / WSL**: [`./run.sh`](file:///Users/bhargav/Downloads/My%20Codes/Xenon%20Hotel%20Management/run.sh)
  - **Windows Command Prompt (CMD)**: [`run.bat`](file:///Users/bhargav/Downloads/My%20Codes/Xenon%20Hotel%20Management/run.bat)
  - **Windows PowerShell**: [`run.ps1`](file:///Users/bhargav/Downloads/My%20Codes/Xenon%20Hotel%20Management/run.ps1)
- **Line Ending Normalization**: [`.gitattributes`](file:///Users/bhargav/Downloads/My%20Codes/Xenon%20Hotel%20Management/.gitattributes) ensures LF for Unix/scripts and CRLF for Windows batch files.
- **Cross-Platform Git Ignore**: [`.gitignore`](file:///Users/bhargav/Downloads/My%20Codes/Xenon%20Hotel%20Management/.gitignore) filters out macOS (`.DS_Store`), Windows (`Thumbs.db`, `desktop.ini`), and Python artifacts.
- **Configurable Binding**: Supports standard `HOST` and `PORT` environment variables (defaults to `127.0.0.1:8000`).

---

## 🚀 How to Run on Any Operating System

### Option A: Universal (Works on Windows, Linux, and Mac)
Open any terminal / command prompt in the project directory:
```bash
python run.py
```
*(or `python3 run.py`)*

### Option B: macOS & Linux
```bash
./run.sh
```

### Option C: Windows Command Prompt (CMD)
Double-click `run.bat` or run:
```cmd
run.bat
```

### Option D: Windows PowerShell
Right-click `run.ps1` -> "Run with PowerShell", or run:
```powershell
.\run.ps1
```

Once started, open your web browser at:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🏛️ Design & Functional Architecture

- **Palatial Color Palette**: Warm travertine ivory (`#faf8f4`, `#f4efe6`, `#ffffff`), deep velvet olive green (`#2c4636`), warm sandstone bronze (`#9c7846`), and royal espresso (`#1b1714`).
- **Typography**: `Pinyon Script` & `Italianno` (romantic fluid cursive calligraphy from *Lemon and Olive*), paired with `Bodoni Moda` and `Marcellus` for royal suite titles.
- **Demo Login Entrance**: Enter any staff name and PIN or click **"⚡ Quick Demo Sign-In"** to jump straight into the POS terminal.
- **Split Workspace**:
  - **Left**: Suites & Residences (`Available`, `Occupied`, `Turnover`), In-Suite Dining & Bar Menu, and Stay Ledger.
  - **Right**: Active Hotel Guest Check ticket with 1-tap **"Charge to Suite Folio"**, **"Direct Settle"**, and **"Check-Out & Finalize"**.

---

## 📂 Directory Layout

```
Xenon Hotel Management/
├── backend/
│   ├── app.py              # FastAPI REST API & static file router (OS-agnostic Path)
│   ├── database.py         # SQLite database schema & starter seeds
│   ├── requirements.txt    # Python dependencies
│   └── xenon_hotel.db      # SQLite database file
├── static/
│   ├── index.html          # Single page application markup
│   ├── style.css           # The Leela Palace & Lemon and Olive quiet luxury stylesheet
│   ├── app.js              # POS controller & guest check cart engine
│   └── images/
│       ├── palace.jpg      # The Leela Palace inspired architectural lobby
│       └── martini.jpg     # Lemon and Olive inspired velvet cocktail still life
├── run.py                  # Universal cross-platform launcher (Python 3)
├── run.sh                  # POSIX launcher script (Linux, macOS, BSD, WSL)
├── run.bat                 # Windows CMD batch launcher
├── run.ps1                 # Windows PowerShell launcher
├── .gitattributes          # Cross-platform line ending rules
├── .gitignore              # OS & Python cache ignore rules
└── README.md               # Complete operational documentation
```
