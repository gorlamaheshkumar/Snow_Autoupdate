import os
import sys
import time
import threading
import msvcrt
import socket
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from collections import deque
from playsound import playsound  # pip install playsound==1.2.2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException


# ===================================================================
# --- ✍️ CONFIGURATION (PLACEHOLDERS — REPLACE BEFORE USE) ---
# ===================================================================

# Credentials (replace with secure retrieval in production)
USER = "USER_USERNAME"
PASSWORD = "USER_PASSWORD"

# --- ServiceNow URLs ---
BASE_URL = "SNOW_BASE_URL"  # e.g. "https://yourinstance.service-now.com"
LOGIN_URL = f"{BASE_URL}/nav_to.do?uri=%2F$pa_dashboard.do"
URL_NEW_STATE_LIST = "SNOW_URL_NEW_STATE_LIST"  # e.g. "https://yourinstance.service-now.com/incident_list.do?sysparm_query=state%3D1%5Eassignment_group.name%3DYour%20Group"

# --- File Paths (PLACEHOLDERS - Set to valid paths before running) ---
SOUND_PATH = r"PATH_TO_NOTIFICATION_SOUND"          # e.g. r"C:\path\to\sound.mp3"
REOPEN_FILE_PATH = r"PATH_TO_REOPEN_FILE"          # e.g. r"C:\path\to\Reopen.txt"

# Default paths (will be overwritten by user choice in runtime)
LOG_FILE_PATH = r"PATH_TO_LOG_FILE"                # e.g. r"C:\path\to\Log.txt"
LIVE_FILE_PATH = r"PATH_TO_LIVE_FILE"              # e.g. r"C:\path\to\Live.txt"

# --- Settings ---
POLL_INTERVAL = 5
# Visual Formatting Settings
LINE_LENGTH = 92  # Width of the divider lines
LOG_BUFFER_SIZE = 100  # Number of recent logs to keep in memory
WEB_SERVER_PORT = 8000  # Port for mobile log viewer


# ===================================================================
# --- LIVE LOG MANAGER (APPEND MODE) ---
# ===================================================================
class LiveLogManager:
    """
    1. Mobile Buffer: RAM (Fastest) for the Web Server.
    2. Log.txt: Append Mode (Historical History).
    3. Live.txt: Append Mode (Secondary Log).
    """
    def __init__(self, log_file, live_file, buffer_size=100):
        self.log_file = log_file
        self.live_file = live_file

        # Buffers
        self.buffer = deque(maxlen=buffer_size) # For Mobile Web
        self.lock = threading.Lock()

    def update_paths(self, new_log_path, new_live_path):
        """Updates paths dynamically based on user input"""
        self.log_file = new_log_path
        self.live_file = new_live_path

    def add(self, message):
        current_time = time.time()
        time_str = time.strftime("[%Y-%m-%d %H:%M:%S]")
        full_line = f"{time_str} {message}"

        with self.lock:
            # --- 1. Update Mobile Web Buffer ---
            self.buffer.append(message)

        # --- 2. Write to HISTORICAL Log (Append) ---
        try:
            log_dir = os.path.dirname(self.log_file)
            if log_dir and not os.path.exists(log_dir): os.makedirs(log_dir)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(full_line + "\n")
        except: pass

        # --- 3. Write to LIVE Log (Append) ---
        try:
            log_dir = os.path.dirname(self.live_file)
            if log_dir and not os.path.exists(log_dir): os.makedirs(log_dir)
            with open(self.live_file, "a", encoding="utf-8") as f:
                f.write(full_line + "\n")
        except: pass

    def get_all(self):
        """Get all logs for mobile viewer."""
        with self.lock:
            return "\n".join(self.buffer)

# Global log manager (Initialized with defaults, updated in Main)
log_manager = LiveLogManager(LOG_FILE_PATH, LIVE_FILE_PATH, LOG_BUFFER_SIZE)

def log(message):
    """Prints to console (clean, no timestamp) and saves to file with timestamp."""
    print(message)
    log_manager.add(message)


# ===================================================================
# --- WEB SERVER FOR MOBILE ---
# ===================================================================
class MobileLogHandler(SimpleHTTPRequestHandler):
    """HTTP handler to serve logs to mobile devices."""
    def do_GET(self):
        if self.path == '/' or self.path == '':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()

            html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Live Script Monitor</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body {
                        font-family: 'Courier New', monospace;
                        background: #0a0e27;
                        color: #00ff88;
                        padding: 15px;
                        height: 100vh;
                        overflow: hidden;
                        display: flex;
                        flex-direction: column;
                    }
                    .header {
                        text-align: center;
                        margin-bottom: 15px;
                        font-weight: bold;
                        font-size: 16px;
                        color: #ff6b6b;
                        border-bottom: 2px solid #00ff88;
                        padding-bottom: 10px;
                    }
                    .status {
                        font-size: 12px;
                        color: #00ccff;
                        margin-bottom: 10px;
                        text-align: center;
                    }
                    .logs-container {
                        flex: 1;
                        overflow-y: auto;
                        border: 2px solid #00ff88;
                        background: #0d1117;
                        padding: 12px;
                        border-radius: 5px;
                        font-size: 12px;
                        line-height: 1.6;
                    }
                    .log-line {
                        margin: 3px 0;
                        white-space: pre-wrap;
                        word-break: break-word;
                    }
                    .error { color: #ff4444; }
                    .success { color: #44ff44; }
                    .warning { color: #ffaa00; }
                    .info { color: #4488ff; }
                    .action { color: #ff88ff; }

                    .logs-container::-webkit-scrollbar {
                        width: 8px;
                    }
                    .logs-container::-webkit-scrollbar-track {
                        background: #0d1117;
                    }
                    .logs-container::-webkit-scrollbar-thumb {
                        background: #00ff88;
                        border-radius: 4px;
                    }
                </style>
            </head>
            <body>
                <div class="header">🔴 LIVE SCRIPT MONITOR 🔴</div>
                <div class="status">Status: <span id="status">Connecting...</span></div>
                <div class="logs-container" id="logs">Loading logs...</div>

                <script>
                    let lastLength = 0;

                    function colorize(text) {
                        if (text.includes('❌') || text.includes('Error') || text.includes('Failed')) {
                            return `<span class="error">${escapeHtml(text)}</span>`;
                        }
                        if (text.includes('✅') || text.includes('Successful')) {
                            return `<span class="success">${escapeHtml(text)}</span>`;
                        }
                        if (text.includes('⚠️') || text.includes('Warning')) {
                            return `<span class="warning">${escapeHtml(text)}</span>`;
                        }
                        if (text.includes('🚨') || text.includes('ACTION REQUIRED')) {
                            return `<span class="action">${escapeHtml(text)}</span>`;
                        }
                        return `<span class="info">${escapeHtml(text)}</span>`;
                    }

                    function escapeHtml(text) {
                        const div = document.createElement('div');
                        div.textContent = text;
                        return div.innerHTML;
                    }

                    function fetchLogs() {
                        fetch('/api/logs?t=' + Date.now())
                            .then(r => r.json())
                            .then(data => {
                                document.getElementById('status').innerText = '✅ Connected';
                                document.getElementById('status').style.color = '#00ff88';

                                const container = document.getElementById('logs');
                                const lines = data.logs.split('\\n').filter(l => l.trim());

                                if (lines.length > lastLength) {
                                    container.innerHTML = lines.map((line) => {
                                        return `<div class="log-line">${colorize(line)}</div>`;
                                    }).join('');
                                    lastLength = lines.length;

                                    setTimeout(() => {
                                        container.scrollTop = container.scrollHeight;
                                    }, 10);
                                }
                            })
                            .catch(err => {
                                document.getElementById('status').innerText = '❌ Disconnected';
                                document.getElementById('status').style.color = '#ff4444';
                            });
                    }

                    fetchLogs();
                    setInterval(fetchLogs, 1000);
                </script>
            </body>
            </html>
            '''
            self.wfile.write(html.encode('utf-8'))

        elif self.path.startswith('/api/logs'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()

            logs_content = log_manager.get_all()
            response = json.dumps({"logs": logs_content})
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress server logs

def get_local_ip():
    """Get your laptop's local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def start_web_server():
    """Start web server for mobile log viewing in background thread."""
    def run_server():
        server = HTTPServer(('0.0.0.0', WEB_SERVER_PORT), MobileLogHandler)
        ip = get_local_ip()

        # Also log to file for mobile viewer
        log_manager.add("")
        log_manager.add("=" * LINE_LENGTH)
        log_manager.add("📱 WEB SERVER STARTED - MOBILE LOG VIEWER")
        log_manager.add("=" * LINE_LENGTH)
        log_manager.add(f"   👉 Local Network: http://{ip}:{WEB_SERVER_PORT}")
        log_manager.add(f"   💡 Ensure mobile & laptop are on SAME WiFi")
        log_manager.add("=" * LINE_LENGTH)
        log_manager.add("")

        server.serve_forever()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

# ===================================================================
# --- HELPERS ---
# ===================================================================
def print_centered_header(text, char="-"):
    """Prints a centered header starting at the beginning of the line."""
    border = char * LINE_LENGTH

    # Calculate padding to center text within the line length
    padding = (LINE_LENGTH - len(text)) // 2
    centered_text = (" " * padding) + text

    log(border)
    log(centered_text)
    log(border)

def load_l2_from_file():
    """Loads previous L2 memory from file."""
    memory = {}
    if os.path.exists(REOPEN_FILE_PATH):
        try:
            with open(REOPEN_FILE_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split('|')
                    if len(parts) >= 3:
                        ticket = parts[0].strip()
                        name = parts[1].strip()
                        val = parts[2].strip()
                        memory[ticket] = {'value': val, 'name': name}
        except: pass
    return memory

def save_l2_item_to_file(ticket, val, name, short_desc):
    """Appends a new processed ticket to the file."""
    try:
        log_dir = os.path.dirname(REOPEN_FILE_PATH)
        if log_dir and not os.path.exists(log_dir): os.makedirs(log_dir)
        clean_desc = short_desc.replace("|", "-").replace("\n", " ")
        with open(REOPEN_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(f"{ticket}|{name}|{val}|{clean_desc}\n")
    except Exception as e:
        log(f"      ⚠️ Error saving to file: {e}")

def play_notification():
    """Plays sound for exactly 3 seconds."""
    clean_path = os.path.abspath(SOUND_PATH.strip())

    def _play():
        try:
            if os.path.exists(clean_path):
                playsound(clean_path)
            else:
                print("\a")
        except Exception as e:
            log(f"   ⚠️ Sound playback error: {e}")

    t = threading.Thread(target=_play)
    t.daemon = True
    t.start()
    time.sleep(3)

def get_shift_users():
    """Asks user for shift members at startup."""
    users = ["Default User"]
    print_centered_header("👥 SHIFT CONFIGURATION 👥", char="-")
    print(f"\n    1. {users[0]} (Default)")

    try:
        count_str = input("    👉 How many additional employees? (0 for none): ").strip()
        count = int(count_str) if count_str.isdigit() else 0
        for i in range(count):
            name = input(f"    👉 Enter Name for Employee {i+2}: ").strip()
            if name: users.append(name)
    except: pass
    log(f"    ✅ Active Shift Users: {users}\n")
    return users

def get_input_with_timeout(prompt, timeout=60):
    """Waits for input with a countdown timer on the same line."""
    start_time = time.time()
    input_chars = []

    while msvcrt.kbhit(): msvcrt.getch() # Clear buffer

    print("") # New line
    while True:
        elapsed = time.time() - start_time
        remaining = int(timeout - elapsed)
        current_str = "".join(input_chars)

        sys.stdout.write(f"\r    Clock: [{remaining:02d}s] {prompt} {current_str}")
        sys.stdout.flush()

        if remaining <= 0:
            log(f"    ⌛ Timeout! Skipping ticket.")
            return "S"

        if msvcrt.kbhit():
            char = msvcrt.getwch()
            if char in ('\r', '\n'):
                print("")
                return current_str
            elif char == '\b':
                if input_chars:
                    input_chars.pop()
                    sys.stdout.write(f"\r    {' ' * 100}")
            else:
                input_chars.append(char)
        time.sleep(0.05)

# ===================================================================
# --- BROWSER INITIALIZATION (HEADED) ---
# ===================================================================
def initialize_driver():
    log("🚀 Launching Chrome (Headed Mode - visible browser window)")
    opts = Options()
    # NOTE: we intentionally do NOT add a headless argument so Chrome opens in headed mode.
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--silent")
    opts.add_argument("--log-level=3")
    opts.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

    old_stderr = sys.stderr
    try:
        with open(os.devnull, 'w') as f:
            sys.stderr = f
            driver = webdriver.Chrome(options=opts)
    finally:
        sys.stderr = old_stderr

    wait = WebDriverWait(driver, 20)

    log("🔐 Logging in (Background)")
    driver.get(LOGIN_URL)

    try:
        try:
            wait.until(EC.element_to_be_clickable((By.ID, "btnSetPopup"))).click()
            time.sleep(2)
        except:
            pass

        time.sleep(2)
        #log("⏳ Waiting for login form to load...")

        wait.until(EC.element_to_be_clickable((By.ID, "corporateOpener"))).click()
        time.sleep(2)

        wait.until(EC.element_to_be_clickable((By.ID, "UsernameInputTxtCorporate"))).send_keys(USER)
        time.sleep(1)

        driver.find_element(By.ID, "PasswordInputCorporate").send_keys(PASSWORD)
        time.sleep(1)

        driver.find_element(By.ID, "btnLoginCorporate").click()
        time.sleep(2)

        wait.until(EC.url_contains("$pa_dashboard.do"))
        log("✅ Logged in successfully.")

    except Exception as e:
        log(f"❌ Login Failed. Error: {e}")
        try: driver.quit()
        except: pass
        exit()

    return driver, wait

# ===================================================================
# --- TAB 1: SCRAPER ---
# ===================================================================
def scrape_l1_incidents_detailed(driver, wait):
    driver.switch_to.window(driver.window_handles[0])
    driver.get(URL_NEW_STATE_LIST)

    scraped_tickets = []
    try:
        try: wait.until(EC.presence_of_element_located((By.CLASS_NAME, "list2_body")))
        except: return []

        headers = driver.find_elements(By.XPATH, "//table//thead//th")
        col_map = {"Number": -1, "Short description": -1, "Reopen count": -1, "Assigned to": -1}

        for i, h in enumerate(headers):
            txt = h.text.strip().lower()
            if "number" in txt: col_map["Number"] = i
            elif "short description" in txt: col_map["Short description"] = i
            elif "reopen count" in txt: col_map["Reopen count"] = i
            elif "assigned to" in txt: col_map["Assigned to"] = i

        if col_map["Number"] == -1: return []

        rows = driver.find_elements(By.CSS_SELECTOR, ".list2_body tr")
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                t_num = cells[col_map["Number"]].text.strip() if len(cells) > col_map["Number"] else ""

                if not t_num.startswith("INC"): continue

                short_desc = "No Description"
                if col_map["Short description"] != -1 and len(cells) > col_map["Short description"]:
                    short_desc = cells[col_map["Short description"]].text.strip()

                assigned_to = ""
                if col_map["Assigned to"] != -1 and len(cells) > col_map["Assigned to"]:
                    assigned_to = cells[col_map["Assigned to"]].text.strip()

                reopen_count = 0
                if col_map["Reopen count"] != -1 and len(cells) > col_map["Reopen count"]:
                    try: reopen_count = int(cells[col_map["Reopen count"]].text.strip())
                    except: reopen_count = 0

                scraped_tickets.append({
                    "ticket": t_num, "desc": short_desc,
                    "assigned": assigned_to, "reopen": reopen_count
                })
            except: pass

    except Exception as e:
        if "stale element" not in str(e).lower():
            log(f"      ⚠️ Error scraping L1: {e}")

    seen = set()
    unique = []
    for item in scraped_tickets:
        if item['ticket'] not in seen:
            unique.append(item)
            seen.add(item['ticket'])
    return unique

# ===================================================================
# --- TAB 2: PROCESSOR ---
# ===================================================================
def process_ticket_in_tab2(driver, wait, ticket_data, l2_memory, shift_users):
    ticket = ticket_data['ticket']
    short_desc = ticket_data['desc']
    assigned_to_val = ticket_data['assigned']
    reopen_count = ticket_data['reopen']

    # Define the custom dividers (Full Width, No Indent)
    DIVIDER_STR = "-" * LINE_LENGTH
    EQUAL_STR   = "=" * LINE_LENGTH

    # --- 1. FAST CHECKS ---
    if ticket in l2_memory:
        mem = l2_memory[ticket]
        log(DIVIDER_STR)
        log(f"    🔄 Fast-Processing: {ticket} - {short_desc}")
        log(f"    🧠 Found in L2 Memory! Opening to auto-update: {mem['name']}")
        open_and_update(driver, wait, ticket, mem['value'], mem['name'], assignee=None)
        log(DIVIDER_STR + "\n")
        return None

    # --- 2. LOGIC CHECK ---
    needs_attention = False
    reason = ""

    if not assigned_to_val or "(empty)" in assigned_to_val:
        needs_attention = True; reason = "Assigned To is Empty"
    elif reopen_count > 0:
        needs_attention = True; reason = f"Reopen Count is {reopen_count}"

    if not needs_attention:
        return None

    # --- 3. OPEN PAGE (Background) ---
    if len(driver.window_handles) < 2: driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])

    url = f"{BASE_URL}/incident.do?sysparm_query=number={ticket}"
    driver.get(url)

    try:
        try: wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "gsft_main")))
        except: pass
        wait.until(EC.presence_of_element_located((By.ID, "sys_readonly.incident.number")))

        if short_desc == "No Description" or not short_desc:
            try: short_desc = driver.find_element(By.ID, "incident.short_description").get_attribute("value")
            except: pass

        # --- ALERT USER (Pretty Output) ---
        log("\n" + EQUAL_STR)
        log(f"    🚨 ACTION REQUIRED: {ticket}")
        log(f"    📄 Desc: {short_desc}")
        log(f"    ⚠️  Reason: {reason}")
        log(EQUAL_STR)

        state_el = driver.find_element(By.ID, "incident.state")
        current_state = state_el.get_attribute("value")
        if current_state in ['6', '7', '8']:
            log("    ⏭️  Ticket Closed. Skipping.")
            return None

        play_notification()

        # --- 4. CONSOLE INTERACTION (WITH TIMER) ---
        selected_assignee = None
        if not assigned_to_val or "(empty)" in assigned_to_val:
            print("\n    👤 Need Assignee:")
            for idx, user in enumerate(shift_users): print(f"    [{idx+1}] {user}")
            print("    [S] Skip")

            while True:
                u_choice_str = get_input_with_timeout(f"👉 Select User (1-{len(shift_users)}), or [S]kip: ", timeout=60)

                if u_choice_str is None or u_choice_str.strip().upper() == 'S':
                    log("    ⏭️  Skipped assignment. Skipping ticket.")
                    return None

                try:
                    u_choice = int(u_choice_str.strip())
                    if 1 <= u_choice <= len(shift_users):
                        selected_assignee = shift_users[u_choice-1]
                        break
                except: pass

        print(f"    Select State for {ticket}:")
        print("    [1] Work in Progress (4)")
        print("    [2] Pending Tasks (22)")
        print("    [3] Pending Vendor (21)")
        print("    [S] Skip")

        while True:
            choice = get_input_with_timeout("👉 Choice: ", timeout=60)
            if choice is None: choice = 'S'
            choice = choice.strip().upper()
            if choice in ['1', '2', '3', 'S']: break

        if choice == 'S':
            log("    ⏭️  Skipped.")
            return None

        val_map = {'1': '4', '2': '22', '3': '21'}
        name_map = {'1': 'WIP', '2': 'Pending Tasks', '3': 'Pending Vendor'}
        target_val = val_map[choice]
        state_name = name_map[choice]

        update_logic(driver, state_el, target_val, state_name, assignee=selected_assignee)
        return {'value': target_val, 'name': state_name, 'assignee': selected_assignee}

    except Exception as e:
        log(f"    ❌ Error processing ticket: {e}")
        return None

def open_and_update(driver, wait, ticket, value, name, assignee):
    if len(driver.window_handles) < 2: driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[1])
    driver.get(f"{BASE_URL}/incident.do?sysparm_query=number={ticket}")
    try:
        try: wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "gsft_main")))
        except: pass
        wait.until(EC.presence_of_element_located((By.ID, "sys_readonly.incident.number")))
        state_el = driver.find_element(By.ID, "incident.state")
        update_logic(driver, state_el, value, name, assignee)
    except: pass

def update_logic(driver, state_el, value, name, assignee):
    try:
        driver.execute_script(f"arguments[0].value = '{value}';", state_el)
        if assignee:
            try:
                assign_input = driver.find_element(By.ID, "sys_display.incident.assigned_to")
                assign_input.clear()
                time.sleep(0.5)
                assign_input.send_keys(assignee)
                time.sleep(1)
                assign_input.send_keys("\t")
            except: pass

        log(f"    💾 Saving {name}")
        driver.execute_script("gsftSubmit(document.getElementById('sysverb_update_and_stay'));")
        time.sleep(3)
        log("    ✅ Update Successful.")
    except Exception as e:
        log(f"    ❌ Update Failed: {e}")

# ===================================================================
# --- MAIN LOOP ---
# ===================================================================
if __name__ == "__main__":
    # STEP 1: Ask to Enable Web Server
    print("")
    print("=" * LINE_LENGTH)
    print("                    📱 WEB SERVER STARTED - MOBILE LOG VIEWER  📱")
    print("=" * LINE_LENGTH)
    print(f"   👉 Local Network: http://{get_local_ip()}:{WEB_SERVER_PORT}")
    print(f"   💡 Ensure mobile & laptop are on SAME WiFi")
    print("=" * LINE_LENGTH)
    print("")

    while True:
        enable_choice = input("📱 WEB SERVER Live Log Monitor - Need to Enable or Not (Y/N): ").strip().upper()
        if enable_choice in ['Y', 'N']:
            break
        print("    ❌ Invalid input. Please enter Y or N")

    if enable_choice == 'Y':
        log("📱 WEB SERVER: Enabled ✅")
        start_web_server()
        time.sleep(3)  # Give server time to start
    else:
        log("📱 WEB SERVER: Disabled ❌")

    print("")

    # STEP 2: Ask about OneDrive Usage
    print_centered_header("ONEDRIVE USAGE")
    while True:
        drive_choice = input("    👉 Company Onedrive Using (Y/N): ").strip().upper()
        if drive_choice in ['Y', 'N']:
            break
        print("    ❌ Invalid input. Please enter Y or N")

    # Set Dynamic Paths based on Choice (placeholders remain)
    if drive_choice == 'Y':
        final_log_path = r"PATH_TO_ONEDRIVE_LOG_FILE"   # e.g. r"C:\Users\<User>\OneDrive - Org\Documents\Snow\Log.txt"
        final_live_path = r"PATH_TO_ONEDRIVE_LIVE_FILE" # e.g. r"C:\Users\<User>\OneDrive - Org\Documents\Snow\Live.txt"
        log(f"    📂 Using OneDrive Paths: {final_log_path}")
    else:
        final_log_path = r"PATH_TO_LOCAL_LOG_FILE"      # e.g. r"C:\Users\<User>\Downloads\Log.txt"
        final_live_path = r"PATH_TO_LOCAL_LIVE_FILE"    # e.g. r"C:\Users\<User>\Downloads\Live.txt"
        log(f"    📂 Using Local Downloads Paths: {final_log_path}")

    # Update the global log manager with the selected paths
    log_manager.update_paths(final_log_path, final_live_path)

    print("")

    # STEP 3: Ask for shift configuration
    shift_users = get_shift_users()

    if not USER or not PASSWORD:
        log("❌ Error: Credentials missing in Configuration section.")
        exit()
        1

    driver = None
    l2_memory = load_l2_from_file()

    while True:
        try:
            if driver is None:
                driver, wait = initialize_driver()
                driver.execute_script("window.open('about:blank', 'tab2');")

            while True:
                print_centered_header("♻️   Checking for New Tickets (Cycle) ♻️", char="-")

                l1_data_list = scrape_l1_incidents_detailed(driver, wait)
                time_now = time.strftime("%H:%M:%S")

                if l1_data_list:
                    log(f"    🎯 Active Tickets Found: {len(l1_data_list)} - {time_now}")
                    for ticket_obj in l1_data_list:
                        result = process_ticket_in_tab2(driver, wait, ticket_obj, l2_memory, shift_users)
                        if result:
                            ticket_num = ticket_obj['ticket']
                            l2_memory[ticket_num] = result
                            save_l2_item_to_file(ticket_num, result['value'], result['name'], ticket_obj['desc'])
                else:
                    log(f"    (No tickets found) - {time_now}")

                time.sleep(POLL_INTERVAL)

        except WebDriverException as e:
            log(f"\n⚠️ Browser Connection Lost: {e}")
            log("🔄 Restarting session")
            try: driver.quit()
            except: pass
            driver = None
            time.sleep(5)

        except KeyboardInterrupt:
            log("\n🛑 Stopped by User.")
            break

        except Exception as e:
            log(f"\n❌ Unexpected Error: {e}")
            time.sleep(5)

    if driver: driver.quit()
