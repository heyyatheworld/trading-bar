# 📊 Crypto Session Bar

A lightweight native macOS application that tracks global trading sessions directly in your **Menu Bar**. Keep market information at your fingertips without cluttering your screen.

---

## ✨ Features

* **Minimalist UI:** Displays only in the top menu bar (Status Bar)
* **Smart Tracking:** Automatically detects the current trading session (London, New York, Tokyo, and more)
* **CME Gap Alert:** Indicates volatility risks when markets open
* **Low Resource Usage:** Built with Python using native macOS libraries (PyObjC)

---

## 🌍 Time Zone Handling

The application uses the `zoneinfo` library (Python 3.9+ standard) for correct handling of daylight saving time transitions. This is critical for trading, as exchange opening times relative to UTC change twice a year.

**Main tracked sessions:**

* **Asia (Tokyo):** 00:00 — 09:00 UTC
* **Europe (London):** 08:00 — 17:00 UTC
* **America (New York):** 13:00 — 22:00 UTC

> **Note:** The application automatically matches your Mac's system time with the configured exchange time zones, ensuring accurate display.

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
pip install pyobjc requests
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
