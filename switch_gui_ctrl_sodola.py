#!/usr/bin/env python3
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

def log_msg(msg: str, is_error: bool = False):
    """年月日時分秒付きでログを出力する"""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    target_stream = sys.stderr if is_error else sys.stdout
    print(f"[{now_str}] {msg}", file=target_stream, flush=True)

def configure_port(switch_ip, username, password, port_num, enable_state):
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
            page.fill('input[name="username"]', username)
            page.fill('input[name="password"]', password)
            page.click('input#loginsub')

            # networkidleの無制限待機を防ぐため10秒タイムアウトを指定
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeoutError:
                log_msg("[!] networkidle の待機がタイムアウトしましたが処理を継続します。")

            log_msg("[+] ログイン完了。フレームを探索中...")

            # 2. メニューフレームの取得と「Port Setting」クリック
            menu_frame = page.frame_locator("xpath=/html/frameset/frame[2]")
            log_msg("[*] メニューの 'Port Setting' をクリック中...")
            menu_frame.locator('a[href="port.cgi"]').evaluate("el => el.click()")

            # 3. メインフレームの取得
            main_frame = page.frame_locator('frame[name="main-frame"]')

            # 4. Port Setting 画面の読み込み待機
            log_msg("[*] Port Setting 画面の読み込みを待機中...")
            main_frame.locator('form[name="portcfg"]').wait_for(state="attached", timeout=15000)

            # 5. ポート設定の変更
            log_msg(f"[*] Port {port_num} の設定を変更中...")
            chk_id = f"port{port_num - 1}"

            form = main_frame.locator('form[name="portcfg"]')
            form.locator(f"input#{chk_id}").evaluate("""el => {
                el.checked = true;
                if (typeof chkClick === 'function') chkClick(el);
            }""")

            state_val = "1" if enable_state else "0"
            form.locator('select[name="state"]').select_option(value=state_val)

            log_msg("[*] 設定を適用 (Apply) しています...")
            form.evaluate("""form => {
                if (typeof btnPortCfgClick === 'function') {
                    btnPortCfgClick();
                } else {
                    form.submit();
                }
            }""")

            # 設定反映後の待機
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
    target_port = int(sys.argv[4])
    is_enable = sys.argv[5].lower() == "enable"

    if not 1 <= target_port <= 8:
        log_msg("[!] ポート番号は 1 〜 8 の範囲で指定してください（Port 9 は非対応）。", is_error=True)
        sys.exit(1)

    configure_port(ip, user, pwd, target_port, is_enable)
