#!/usr/bin/env python3
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def log_msg(msg: str, is_error: bool = False):
    """年月日時分秒付きでログを出力する"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_stream = sys.stderr if is_error else sys.stdout
    print(f"[{now_str}] {msg}", file=target_stream, flush=True)

def configure_port_tlsg108e(switch_ip, username, password, port_num, enable_state):
    base_url = f"http://{switch_ip}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            context = browser.new_context()
            # 各操作・ナビゲーションのタイムアウトを15秒に設定
            context.set_default_timeout(15000)
            context.set_default_navigation_timeout(15000)
            page = context.new_page()

            log_msg(f"[*] スイッチ ({switch_ip}) のログインページにアクセス中...")
            page.goto(f"{base_url}/", timeout=15000)

            # 1. ログイン処理
            log_msg("[*] ログイン情報を入力中...")
            page.fill('input#username', username)
            page.fill('input#password', password)
            page.click('input#logon')

            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeoutError:
                log_msg("[!] networkidle の待機がタイムアウトしましたが処理を継続します。")

            log_msg("[+] ログイン完了。フレームを探索中...")

            # 2. メインフレームの取得と画面遷移
            main_frame = page.frame_locator('frame[name="mainFrame"]')
            log_msg("[*] Port Setting 画面へ遷移中...")
            page.evaluate("""() => {
                var f = document.getElementsByName('mainFrame')[0] || document.getElementsByTagName('frame')[1];
                if (f) {
                    f.src = 'PortSettingRpm.htm';
                }
            }""")

            # 3. Port Setting 画面のフォーム要素を待機
            log_msg("[*] Port Setting 画面の読み込みを待機中...")
            form = main_frame.locator('form[name="port_setting"]')
            form.wait_for(state="attached", timeout=15000)

            # 4. ポート設定の変更
            log_msg(f"[*] Port {port_num} の設定を変更中...")
            port_sel = form.locator('select#portSel')
            port_sel.select_option(value=str(port_num))

            state_val = "1" if enable_state else "0"
            form.locator('select[name="state"]').select_option(value=state_val)

            # 5. 設定の適用 (Apply)
            log_msg("[*] 設定を適用 (Apply) しています...")
            form.locator('input[name="apply"]').evaluate("el => el.click()")

            # 設定反映・リロード完了を待機
            page.wait_for_timeout(3000)
            action_str = "有効化 (Enable)" if enable_state else "無効化 (Disable)"
            log_msg(f"[+] Port {port_num} の {action_str} が完了しました。")

        except Exception as e:
            log_msg(f"[!] エラーが発生しました: {e}", is_error=True)
            sys.exit(1)
        finally:
            # 異常終了時も必ずブラウザを閉じてプロセス残留を防ぐ
            browser.close()

if __name__ == "__main__":
    if len(sys.argv) < 6:
        log_msg(f"Usage: {sys.argv[0]} <ip_address> <username> <password> <port(1-8)> <enable|disable>", is_error=True)
        sys.exit(1)

    ip = sys.argv[1]
    user = sys.argv[2]
    pwd = sys.argv[3]
    port = int(sys.argv[4])
    state = sys.argv[5].lower()

    if not 1 <= port <= 8:
        log_msg("[!] ポート番号は 1 〜 8 の範囲で指定してください。", is_error=True)
        sys.exit(1)

    if state not in ("enable", "disable"):
        log_msg("[!] 最後の引数は 'enable' または 'disable' を指定してください。", is_error=True)
        sys.exit(1)

    is_enable = (state == "enable")
    configure_port_tlsg108e(ip, user, pwd, port, is_enable)
