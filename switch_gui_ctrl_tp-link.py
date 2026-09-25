#!/usr/bin/env python3
import sys
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
        if raw.startswith("[") and raw.endswith("]"):
            parsed = ast.literal_eval(raw)
            if not isinstance(parsed, (list, tuple)):
                raise ValueError()
            ports = [int(p) for p in parsed]
        else:
            ports = [int(raw)]
    except Exception:
        raise ValueError(f"Invalid format: '{port_arg}'")

    if not ports:
        raise ValueError("Port list cannot be empty.")

    for p in ports:
        if not (1 <= p <= 8):
            raise ValueError(f"Port {p} is out of range. Supported ports are 1 to 8.")

    return sorted(list(set(ports)))

def configure_ports_tlsg108e(switch_ip, username, password, target_ports, enable_state):
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
            page.fill('input#username', username)
            page.fill('input#password', password)
            page.click('input#logon')

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

            try:
                page.wait_for_selector('frame[name="mainFrame"], frame[src*="Rpm.htm"]', state="attached", timeout=5000)
            except PlaywrightTimeoutError:
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

            state_val = "1" if enable_state else "0"
            expected_text = "Enabled" if enable_state else "Disabled"

            # 5. Loop through target ports with verification
            for port_num in target_ports:
                log_msg(f"[*] Configuring Port {port_num} to '{expected_text}'...")
                port_sel = form.locator('select#portSel')
                port_sel.select_option(value=str(port_num))
                form.locator('select[name="state"]').select_option(value=state_val)

                # Submit form via Apply button
                form.locator('input[name="apply"]').evaluate("el => el.click()")

                # 6. Verify status update on the table
                # TL-SG108E displays port list in table rows where column 1 is Port Number and column 2 is State
                row_locator = main_frame.locator(f"tr:has-text('Port {port_num}'), tr:has(td:text-is('{port_num}'))")
                try:
                    # Wait up to 5 seconds for the state cell to reflect the expected text
                    row_locator.locator(f"text={expected_text}").first.wait_for(state="visible", timeout=5000)
                    log_msg(f"[+] Port {port_num} verified: successfully switched to '{expected_text}'.")
                except PlaywrightTimeoutError:
                    log_msg(f"[!] Warning: Timed out waiting for table verification on Port {port_num}. Proceeding.", is_error=True)

                # 1-second delay before moving to the next port
                page.wait_for_timeout(1000)

            log_msg(f"[+] All requested ports {target_ports} successfully processed.")

        except Exception as e:
            log_msg(f"[!] An error occurred: {e}", is_error=True)
            sys.exit(1)
        finally:
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 6:
        log_msg(f"Usage: {sys.argv[0]} <ip_address> <username> <password> <'[1, 2, 8]'> <enable|disable>", is_error=True)
        log_msg(f"Example: {sys.argv[0]} 192.168.100.205 admin 'password' '[1, 2, 8]' disable", is_error=True)
        sys.exit(1)

    ip = sys.argv[1]
    user = sys.argv[2]
    pwd = sys.argv[3]

    try:
        ports = parse_ports(sys.argv[4])
    except ValueError as e:
        log_msg(f"[!] Invalid port specification: {e}", is_error=True)
        sys.exit(1)

    state = sys.argv[5].lower()
    if state not in ("enable", "disable"):
        log_msg(f"[!] Invalid action '{sys.argv[5]}'. Action must be 'enable' or 'disable'.", is_error=True)
        sys.exit(1)

    is_enable = (state == "enable")
    configure_ports_tlsg108e(ip, user, pwd, ports, is_enable)
