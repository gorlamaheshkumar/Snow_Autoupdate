# SNOW_Autoupdate

A lightweight ServiceNow incident monitor using headless Selenium to detect and process new or reopened tickets. Includes real-time logging (console, file, in-memory) and a mobile-friendly live log viewer. All sensitive values are replaced with placeholders for safe configuration.

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
 ├─ LICENSE
 └─ README.md
```

---

## ServiceNow Incident Monitor (Headless Selenium + Live Log Viewer)

A lightweight automation tool that continuously monitors ServiceNow for **new, reopened, or unassigned incidents**, processes them using defined rules, and provides a **real-time mobile-friendly log viewer**.

Runs using a **headless Chrome Selenium scraper** with a **thread-safe logging system**. The **Live Log Viewer** auto-refreshes and rotates its buffer every ~3 minutes to maintain speed and prevent excessive payloads.

---

## ⭐ Features

✔️ **Headless Selenium scraping** (no visible browser)

✔️ Detects **new incidents**, **high-reopen incidents**, and **unassigned tickets**

✔️ Smart auto-actions: **WIP**, **Pending Vendor**, **Pending Tasks**, **Skip Logic**

✔️ **Level-2 (L2) Fast-Processing Memory** for repeated incidents

✔️ **Thread-safe logging** to three outputs (Console, Log.txt, Live.txt)

✔️ **Live Log Viewer** accessible on your local network

✔️ **Live.txt buffer auto-rotates every 3 minutes**

✔️ No credentials in code — uses safe placeholders

---

## 📁 Project Structure

```
SNOW_AUTOUPDATE/
 ├─ Logs/
 │   ├─ Live.txt        # Live viewer buffer (auto-rotates every 3 mins)
 │   ├─ Log.txt         # Full persistent log (append-only)
 │   └─ Reopen.txt      # High reopen incidents archive
 ├─ Output Files/
 │   ├─ CLI Output.png  # Example CLI output screenshot
 │   └─ Live Logger.png # Example mobile log viewer screenshot
 ├─ Headless.py         # Main runner (monitor + logging + viewer)
 ├─ LICENSE
 └─ README.md
```

---

## ⚙️ Installation

### 1️⃣ Install Python

Requires **Python 3.10+**

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Install Chrome + ChromeDriver

- Chrome must be installed
- ChromeDriver version must match your Chrome version
- Add ChromeDriver to PATH or configure the path in code

---

## 🔐 Configuration (Placeholders)

Before running, replace these placeholders in `Headless.py`:

```python
USER = "USER_USERNAME"                          # Your ServiceNow username
PASSWORD = "USER_PASSWORD"                      # Your ServiceNow password
BASE_URL = "SNOW_BASE_URL"                      # e.g., https://yourinstance.service-now.com
LOGIN_URL = f"{BASE_URL}/nav_to.do?uri=..."    # ServiceNow login endpoint
URL_NEW_STATE_LIST = "SNOW_URL_NEW_STATE_LIST"  # Your incident list URL
SOUND_PATH = r"PATH_TO_NOTIFICATION_SOUND"      # e.g., C:\path\to\sound.mp3
REOPEN_FILE_PATH = r"PATH_TO_REOPEN_FILE"       # e.g., C:\path\to\Reopen.txt
LOG_FILE_PATH = r"PATH_TO_LOG_FILE"             # e.g., C:\path\to\Log.txt
LIVE_FILE_PATH = r"PATH_TO_LIVE_FILE"           # e.g., C:\path\to\Live.txt
```

**Never hard-code real credentials in production.**

---

## 🚀 How to Run

Run the main script:

```bash
python Headless.py
```

### What Happens

1. Headless Chrome launches in background
2. Prompts you to enable the Web Server (for mobile viewer)
3. Asks about OneDrive usage (for log file locations)
4. Requests shift configuration (list of team members)
5. Monitor loop begins
6. Logs are written to:
   - `Logs/Log.txt` — Full persistent history
   - `Logs/Live.txt` — Rotating buffer (resets every 3 mins)
   - `Logs/Reopen.txt` — High reopen incidents
7. Mobile-friendly live log viewer starts automatically

---

## 📱 Live Log Viewer

Accessible via your system's local network:

```
http://<your-local-ip>:8000
```

### Viewer Features

✔️ Displays **real-time log events** with color-coding

✔️ Automatically scrolls like a terminal

✔️ Responsive **mobile-friendly interface**

✔️ Live.txt buffer resets every **3 minutes**:
  - Clears only the in-memory buffer
  - Does **NOT** delete Log.txt
  - Prevents UI lag, keeps updates lightweight

### Important Notes

- **Live.txt** is a rotating buffer for UI performance
- **Log.txt** is the permanent append-only log
- Both files persist across script restarts

---

## 🧠 Ticket Processing Logic

| Condition | Action |
|-----------|--------|
| Assigned To is empty | Prompt user for assignee or skip |
| Reopen count > 0 | Log and process based on rules |
| Known repeat ticket | Apply L2 memory (auto-action) |
| Ticket closed (State 6,7,8) | Skip processing |
| Console timeout (60 sec) | Auto-skip |

You can tune thresholds and timings inside `Headless.py`.

---

## 🧠 Level-2 (L2) Fast-Processing Memory

If a ticket matches stored patterns from `Reopen.txt`:

- **Auto-applies** previous state (Pending Vendor, Pending Tasks, WIP, etc.)
- Greatly speeds up recurrence handling
- Reduces manual intervention for repeated issues
- Memory persists across script restarts

---

## 📦 Requirements

```
selenium==4.x
playsound==1.2.2
python-dotenv
```

---

## ♻️ Log Management

### 1. Logs/Log.txt

- **Purpose**: Permanent log, append-only
- **Behavior**: Grows indefinitely (archive periodically)
- **Access**: Full historical record

### 2. Logs/Live.txt

- **Purpose**: Lightweight buffer for the web UI
- **Behavior**: Clears every 3 minutes to prevent UI overload
- **Access**: Recent events only (last 3 minutes)

### 3. Logs/Reopen.txt

- **Purpose**: Archive of incidents with high reopen counts
- **Behavior**: Append-only, stores ticket | state | description
- **Access**: Quick reference for escalated tickets

---

## 📌 Usage Notes

- Mobile and laptop must be on the **same WiFi network**
- Run on a stable network for best Selenium performance
- Script will prompt for shift member configuration on startup
- Each incident is processed only once per cycle
- Console input supports both manual entry and timeout-based skip

---

## 🛡️ Security

- Credentials stored as placeholders (user fills them in)
- Sensitive data never logged to files
- Runs in isolated headless browser session
- All file paths are configurable for flexibility
- No external API calls or cloud storage

---

## 🔄 Auto-Restart Behavior

If the application restarts:

- Web Server restarts automatically
- Log.txt continues growing
- Live.txt buffer restarts empty
- Monitoring loop resumes without losing L2 memory
- Reopen.txt state is preserved

---

## 🎯 Typical Workflow

1. Script starts → Configure shift members
2. Browser logs into ServiceNow
3. Continuous loop:
   - Scrapes incident list (State = New)
   - Checks against L2 memory
   - Processes new/reopened tickets
   - Applies auto-actions or prompts user
   - Logs all activity
4. Mobile viewer shows live updates in real-time
5. Press Ctrl+C to stop script gracefully

---

## 🔮 Future Enhancements

- 🎮 **Mobile CLI Control** — Control tickets remotely from mobile UI (Select assignee, state, add work notes without console input)
- ⏰ **Periodic Alarm System** — Set recurring alarms (every 10/15/20 mins) to play notification sound
- 🧹 **Queue Monitoring** — Scrape and display ticket counts for multiple queues (INC/RITM across different teams)
- 📊 **Live Statistics Dashboard** — Display cycle counts, restart counter, skipped tickets, and updated tickets history
- 📝 **Notes Scraping** — Auto-scrape ticket history to identify previous states and auto-apply them for reopened tickets
- 🎵 **Queue Sound Alerts** — Play distinct sound when queue counts increase across monitored queues
- 🔋 **Auto-Restart Mechanism** — Automatically restart browser session after N cycles to prevent lag buildup
- 📱 **Enhanced Mobile Interface** — Sliding panels for queues, history, and CLI actions with real-time updates
- 🚀 **Advanced Auto-Actions** — Smarter skip counts with auto-assignment and auto-acknowledgement thresholds
- 🔄 **Batch/Multi-Mode Processing** — Update multiple tickets at once with bulk assignee assignment, state changes, and work notes addition (e.g., assign 5 tickets to same team member, add common resolution notes, change state for entire queue in one action)

---


## 🙌 **Contributions**



PRs welcome!

Please avoid committing real credentials or internal data.



---