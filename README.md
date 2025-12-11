# Snow_Autoupdate
A lightweight ServiceNow incident monitor using headless Selenium to detect and process new or reopened tickets. Includes real-time logging (console, file, in-memory) and a mobile-friendly live log viewer. All sensitive values are replaced with placeholders for safe configuration via environment variables.Below is the **same README**, fully rewritten to match **your actual file structure** from the screenshot:

```
SNOW_AUTOUPDATE/
 ├─ Logs/
 │   ├─ Live.txt
 │   ├─ Log.txt
 │   └─ Reopen.txt
 ├─ Output Files/
 │   ├─ CLI Output.png
 │   └─ Live Logger.png
 ├─ Headless.py
 ├─ Snowhead.py
 ├─ LICENSE
 └─ README.md
```

Everything now references **Headless.py**, **Snowhead.py**, and the actual log file names.

---

# **ServiceNow Incident Monitor (Headless Selenium + Live Log Viewer)**

A lightweight automation tool that continuously monitors ServiceNow for **new, reopened, or unassigned incidents**, processes them using defined rules, and provides a **real-time mobile-friendly log viewer**.

Runs using a **headless Chrome Selenium scraper** with a **thread-safe logging system**.
The **Live Log Viewer** auto-refreshes and resets its in-memory buffer every ~60 seconds to maintain speed and prevent excessive payloads.

---

## ⭐ **Features**

✔️ **Headless Selenium scraping** (no visible browser)
✔️ Detects **new incidents**, **high-reopen incidents**, and **unassigned tickets**
✔️ Smart auto-actions: **WIP**, **Pending Vendor**, **Pending Tasks**, **Skip Logic**
✔️ **L2 Fast-Processing Memory** for repeated incidents
✔️ **Thread-safe logging** to three outputs
✔️ **Live Log Viewer** accessible on your local network
✔️ **Live.txt buffer auto-clears every 60 seconds**
✔️ No credentials in code — uses environment variables or safe placeholders

---

## 📁 **Project Structure**

```
SNOW_AUTOUPDATE/
 ├─ Logs/
 │   ├─ Live.txt        # Live viewer buffer (auto-clears)
 │   ├─ Log.txt         # Full persistent log
 │   └─ Reopen.txt      # High reopen incidents archive
 ├─ Output Files/
 │   ├─ CLI Output.png  # Example CLI output screenshot
 │   └─ Live Logger.png # Example mobile log viewer screenshot
 ├─ Headless.py         # Main runner (monitor + logging + viewer)
 ├─ Snowhead.py         # Ticket processing logic + L2 memory
 ├─ LICENSE
 └─ README.md
```

---

## ⚙️ **Installation**

### 1️⃣ Install Python

Requires **Python 3.10+**

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Install Chrome + ChromeDriver

* Chrome must be installed
* ChromeDriver version must match your Chrome
* Add ChromeDriver to PATH or configure via environment variable:

```
CHROME_DRIVER_PATH=<path-to-chromedriver>
```

---

## 🔐 **Configuration (Environment Variables)**

Create a `.env` file or export:

```
SNOW_USERNAME=your_username
SNOW_PASSWORD=your_password
SNOW_URL=https://your-instance.service-now.com
DOWNLOAD_PATH=C:/Users/<User>/Downloads
CHROME_DRIVER_PATH=C:/Tools/chromedriver.exe
LIVE_LOG_PORT=8000
LIVE_LOG_CLEAR_INTERVAL=60
```

**Never hard-code credentials.**

---

## 🚀 **How to Run**

Run the main script:

```bash
python Headless.py
```

What happens:

* Headless Chrome launches in background
* Monitor loop begins
* Logs are written to:

  * `Logs/Log.txt`
  * `Logs/Live.txt` (UI buffer)
  * `Logs/Reopen.txt` (high reopen incidents)
* Mobile-friendly live log viewer starts automatically

---

## 📱 **Live Log Viewer**

Accessible via your system’s local network:

```
http://<your-local-ip>:8000
```

### Viewer Behavior

* Displays **real-time log events**
* Automatically scrolls like a terminal
* **Live.txt** buffer resets every **60 seconds**:

  * Clears only **in-memory buffer**
  * Does **NOT** delete `Log.txt`
  * Prevents UI lag, keeps updates lightweight

**Important:**

> Live.txt is a *rotating* buffer. Log.txt is the permanent log.

---

## 🧠 **Ticket Processing Logic (Snowhead.py)**

| Condition            | Action                        |
| -------------------- | ----------------------------- |
| Assigned To is empty | Prompt/skip based on rules    |
| Reopen count high    | Save to Reopen.txt + escalate |
| Known repeat ticket  | Apply L2 memory (auto-action) |
| Ticket closed        | Skip                          |
| UI timeout           | Skip                          |

You can tune thresholds and timings inside **Snowhead.py**.

---

## 📝 **L2 Fast-Processing Memory**

If a ticket matches stored patterns:

* Auto-applies: **Pending Vendor**, **Pending Tasks**, **WIP**, etc.
* Greatly speeds up recurrence handling
* Extend memory by editing your JSON/store inside `Snowhead.py`

---

## 📦 **Typical Requirements**

```
selenium
flask
python-dotenv
webdriver-manager
```

(Add your own if additional modules exist.)

---

## ♻️ **Log Management**

### 1. `Logs/Log.txt`

Permanent log, append-only.

### 2. `Logs/Live.txt`

Lightweight buffer for the web UI.
Clears every **60 seconds** to prevent UI overload.

### 3. `Logs/Reopen.txt`

Archive of incidents with high reopen counts.

---

## 🔄 **Auto-Restart Behavior**

If application restarts:

* Viewer restarts
* Log.txt continues growing
* Live buffer restarts empty
* Monitoring loop resumes without losing state

---

## 📌 **Usage Notes**

* Mobile + PC must be on the **same WiFi**
* Don’t commit `.env`
* Run on a stable network for best Selenium performance

---

## 🛡️ **Security**

* Credentials never logged
* Sensitive text sanitized
* Runs in isolated headless browser session
* Log trimming prevents sensitive overflow

---

## 🧩 **Future Enhancements**

* Push notifications
* Webhook alerts
* Stats dashboard
* Multi-user log viewer modes

---

## 🙌 **Contributions**

PRs welcome!
Please avoid committing real credentials or internal data.

---

If you want, I can also generate:

✅ Requirements.txt
✅ Sample `.env.example`
✅ Auto-start script (Windows `.bat`, Linux `systemd`)
✅ Screenshots section for README
✅ GitHub badges

Just tell me!

