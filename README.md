# 📊 Crypto Session Bar

A lightweight native macOS application that tracks global trading sessions directly in your **Menu Bar**. Keep market information at your fingertips without cluttering your screen.

---

## ✨ Features

* **Minimalist UI:** Displays only in the top menu bar (Status Bar)
* **Smart Tracking:** Automatically detects the current trading session (Hong Kong, Frankfurt/XETRA, London, NYSE pre/main, CME)
* **CME Gap Alert:** Indicates volatility risks when markets open (weekends and Monday pre-open)
* **BTC/ETH Premium:** Spot prices from Coinbase and premium vs Binance in the menu
* **Low Resource Usage:** Built with Python using native macOS libraries (PyObjC)

---

## 🌍 Time Zone Handling

The application uses the `zoneinfo` library (Python 3.9+ standard) for correct handling of daylight saving time transitions. This is critical for trading, as exchange opening times relative to UTC change twice a year.

**Main tracked sessions** (editable in `data/sessions.json`; CME uses `"venue": "cme"`):

* **HKEX (Hong Kong)** — Asia/Hong_Kong
* **XETRA (Frankfurt)** — Europe/Berlin
* **LSE (London)** — Europe/London
* **NYSE (New York)** — pre-market and main session, America/New_York
* **CME (Chicago)** — futures session, America/Chicago (with weekend wrap logic)

> **Note:** The application automatically matches your Mac's system time with the configured exchange time zones, ensuring accurate display.

### Simplified hours (not an official calendar)

Opening times in `data/sessions.json` are **approximate regular hours** for the menu bar. They do **not** include exchange holidays, early closes, auction-only days, or venue-specific exceptions. Treat this as an at-a-glance guide, not compliance-grade market data.

The **CME gap risk** banner uses your **Mac’s local clock** (weekend plus Monday morning through 10:00 local). It is a rough reminder, not tied to the exact Chicago reopen minute in your time zone.

---

## 🛠 Development & Running from Source

### Requirements

* macOS (Intel or Apple Silicon)
* Python 3.12 (recommended version for stable builds)

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/trading-bar.git
cd trading-bar

# Create a virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# Optional: tests and build
pip install -r requirements-dev.txt
```

---

## 📦 Building Your Own .app File

To create a standalone application, PyInstaller is used as it most correctly packages dependencies in newer macOS versions (including Sonoma and Sequoia).

### 1. Prepare Access Permissions

If you encounter an "Operation not permitted" error during build, you need to grant Terminal full disk access:

> **System Settings → Privacy & Security → Full Disk Access → Enable Terminal**

### 2. Build Command

Execute the following command in the project root:

```bash
pip install pyinstaller
pyinstaller --noconsole --windowed --onefile --hidden-import=zoneinfo --name "TradingBar" main.py
```

#### Build Options Explained

* `--noconsole` and `--windowed`: The application won't open an extra terminal window
* `--onefile`: All dependencies are packaged into a single executable file
* `--hidden-import=zoneinfo`: Forces inclusion of the timezone database

### 3. Installation

After the build process completes:

1. Navigate to the `dist/` folder
2. Drag `TradingBar.app` to your `Applications` folder

---

## ⚙️ Auto-Start Configuration

To make the application launch automatically at system startup:

1. Go to **System Settings → General → Login Items**
2. In the "Open at Login" section, click the **+** button
3. Select `TradingBar.app` from your Applications folder

---

## 📝 License

MIT License. Use for any purpose. Happy trading!
