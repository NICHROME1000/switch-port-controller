#!/usr/bin/env python3
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def log_msg(msg: str, is_error: bool = False):
    """Output log message with timestamp in YYYY-MM-DD HH:MM:SS format."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_stream = sys.stderr if is_error else sys.stdout
    print(f"[{now_str}] {msg}", file=target_stream, flush=True)

def configure_port_tlsg108e(switch_ip, username, password, port_num, enable_state):
    base_url = f"http://{switch_ip}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            # Set default operation and navigation timeouts to 15 seconds
            context.set_default_timeout(15000)
            context.set_default_navigation_timeout(15000)
            page = context.new_page()

            log_msg(f"[*] Accessing switch login page ({switch_ip})...")
            page.goto(f"{base_url}/", timeout=15000)

            # 1. Login process
            log_msg("[*] Submitting login credentials...")
            page.fill('input#username', username)
            page.fill('input#password', password)
            page.click('input#logon')

            # Cap networkidle wait time to 10 seconds
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeoutError:
                log_msg("[!] Networkidle timeout reached, continuing execution.")

            # 2. Check login result
            ret_info = page.locator('div#ret_info')
            if ret_info.is_visible():
                error_text = ret_info.inner_text().strip()
                if error_text:
                    log_msg(f"[!] Login failed: {error_text}", is_error=True)
                    sys.exit(1)

            # Confirm target main frame is loaded
            try:
                page.wait_for_selector('frame[name="mainFrame"], frame[src*="Rpm.htm"]', state="attached", timeout=5000)
            except PlaywrightTimeoutError:
                # Re-check ret_info in case of slow rendering
                if ret_info.is_visible():
                    error_text = ret_info.inner_text().strip()
                    log_msg(f"[!] Login failed: {error_text}", is_error=True)
                else:
                    log_msg("[!] Login failed: Main frame not found.", is_error=True)
                sys.exit(1)

            log_msg("[+] Login successful. Navigating to Port Setting...")

            # 3. Locate main frame and navigate to Port Setting
            main_frame = page.frame_locator('frame[name="mainFrame"]')
            page.evaluate("""() => {
                var f = document.getElementsByName('mainFrame')[0] || document.getElementsByTagName('frame')[1];
                if (f) {
                    f.src = 'PortSettingRpm.htm';
                }
            }""")

            # 4. Wait for Port Setting form elements
            log_msg("[*] Waiting for Port Setting form to load...")
            form = main_frame.locator('form[name="port_setting"]')
            form.wait_for(state="attached", timeout=15000)

            # 5. Modify port configuration
            log_msg(f"[*] Configuring Port {port_num}...")
            port_sel = form.locator('select#portSel')
            port_sel.select_option(value=str(port_num))

            state_val = "1" if enable_state else "0"
            form.locator('select[name="state"]').select_option(value=state_val)

            # 6. Apply settings
            log_msg("[*] Applying port settings...")
            form.locator('input[name="apply"]').evaluate("el => el.click()")

            # Wait for settings to apply and page to stabilize
            page.wait_for_timeout(3000)
            action_str = "Enabled" if enable_state else "Disabled"
            log_msg(f"[+] Successfully {action_str} Port {port_num}.")

        except Exception as e:
            log_msg(f"[!] An error occurred: {e}", is_error=True)
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 6:
        log_msg(f"Usage: {sys.argv[0]} <ip_address> <username> <password> <port(1-8)> <enable|disable>", is_error=True)
        log_msg(f"Example: {sys.argv[0]} 192.168.100.205 admin 'password' 8 disable", is_error=True)
        sys.exit(1)

    ip = sys.argv[1]
    user = sys.argv[2]
    pwd = sys.argv[3]

    # Validate port number (must be integer 1 to 8)
    try:
        port = int(sys.argv[4])
        if not (1 <= port <= 8):
            raise ValueError()
    except ValueError:
        log_msg(f"[!] Invalid port number '{sys.argv[4]}'. Port must be an integer between 1 and 8.", is_error=True)
        sys.exit(1)

    # Validate action argument
    state = sys.argv[5].lower()
    if state not in ("enable", "disable"):
        log_msg(f"[!] Invalid action '{sys.argv[5]}'. Action must be 'enable' or 'disable'.", is_error=True)
        sys.exit(1)

    is_enable = (state == "enable")
    configure_port_tlsg108e(ip, user, pwd, port, is_enable)
