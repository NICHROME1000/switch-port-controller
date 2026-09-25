#!/usr/bin/env python3
import sys
import re
import ast
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def log_msg(msg: str, is_error: bool = False):
    """Output log message with timestamp in YYYY-MM-DD HH:MM:SS format."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_stream = sys.stderr if is_error else sys.stdout
    print(f"[{now_str}] {msg}", file=target_stream, flush=True)

def parse_ports(port_arg: str):
    """Parse port argument like '[1, 2, 8]' or '8' into a list of unique integers."""
    raw = port_arg.strip()
    try:
        # Check if array format: [1, 2, 8]
        if raw.startswith("[") and raw.endswith("]"):
            parsed = ast.literal_eval(raw)
            if not isinstance(parsed, (list, tuple)):
                raise ValueError()
            ports = [int(p) for p in parsed]
        else:
            # Single integer format
            ports = [int(raw)]
    except Exception:
        raise ValueError(f"Invalid format: '{port_arg}'")

    if not ports:
        raise ValueError("Port list cannot be empty.")

    # Validate range
    for p in ports:
        if not (1 <= p <= 8):
            raise ValueError(f"Port {p} is out of range. Supported ports are 1 to 8 (Port 9 SFP is not supported).")

    return sorted(list(set(ports)))

def configure_ports(switch_ip, username, password, target_ports, enable_state):
    base_url = f"http://{switch_ip}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            context.set_default_timeout(15000)
            context.set_default_navigation_timeout(15000)
            page = context.new_page()

            log_msg(f"[*] Accessing switch login page ({switch_ip})...")
            page.goto(f"{base_url}/", timeout=15000)

            # 1. Login process
            log_msg("[*] Submitting login credentials...")
            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)
            page.click('input#loginsub')

            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeoutError:
                log_msg("[!] Networkidle timeout reached, continuing execution.")

            # 2. Check login result
            error_tip = page.locator('label#tip')
            if error_tip.is_visible():
                error_text = error_tip.inner_text().strip()
                log_msg(f"[!] Login failed: Incorrect username or password ({error_text}).", is_error=True)
                sys.exit(1)

            menu_frame = page.frame_locator("xpath=/html/frameset/frame[2]")
            try:
                menu_frame.locator('a[href="port.cgi"]').wait_for(state="attached", timeout=5000)
            except PlaywrightTimeoutError:
                log_msg("[!] Login failed: Target menu frame not found.", is_error=True)
                sys.exit(1)

            log_msg("[+] Login successful. Navigating to Port Setting...")

            # 3. Open Port Setting
            menu_frame.locator('a[href="port.cgi"]').evaluate("el => el.click()")

            # 4. Wait for main frame and form loading
            main_frame = page.frame_locator('frame[name="main-frame"]')
            log_msg("[*] Waiting for Port Setting form to load...")
            form = main_frame.locator('form[name="portcfg"]')
            form.wait_for(state="attached", timeout=15000)

            # 5. Modify port configurations (SODOLA supports checking multiple boxes simultaneously)
            log_msg(f"[*] Selecting Ports {target_ports}...")
            for port_num in target_ports:
                chk_id = f"port{port_num - 1}"
                form.locator(f"input#{chk_id}").evaluate("""el => {
                    el.checked = true;
                    if (typeof chkClick === 'function') chkClick(el);
                }""")

            state_val = "1" if enable_state else "0"
            form.locator('select[name="state"]').select_option(value=state_val)

            log_msg("[*] Applying port settings...")
            form.evaluate("""form => {
                if (typeof btnPortCfgClick === 'function') {
                    btnPortCfgClick();
                } else {
                    form.submit();
                }
            }""")

            page.wait_for_timeout(3000)
            action_str = "Enabled" if enable_state else "Disabled"
            log_msg(f"[+] Successfully {action_str} Port(s) {target_ports}.")

        except Exception as e:
            log_msg(f"[!] An error occurred: {e}", is_error=True)
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 6:
        log_msg(f"Usage: {sys.argv[0]} <ip_address> <username> <password> <'[1, 2, 8]'> <enable|disable>", is_error=True)
        log_msg(f"Example: {sys.argv[0]} 192.168.100.204 admin 'password' '[1, 2, 8]' disable", is_error=True)
        sys.exit(1)

    ip = sys.argv[1]
    user = sys.argv[2]
    pwd = sys.argv[3]

    # Parse and validate ports
    try:
        ports = parse_ports(sys.argv[4])
    except ValueError as e:
        log_msg(f"[!] Invalid port specification: {e}", is_error=True)
        sys.exit(1)

    # Validate action argument
    action_arg = sys.argv[5].lower()
    if action_arg not in ("enable", "disable"):
        log_msg(f"[!] Invalid action '{sys.argv[5]}'. Action must be 'enable' or 'disable'.", is_error=True)
        sys.exit(1)

    is_enable = (action_arg == "enable")

    configure_ports(ip, user, pwd, ports, is_enable)
