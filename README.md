# switch-port-controller

Playwright-based automation scripts to enable or disable network switch ports via Web GUI. Supports multi-port batch operations and is designed for robust, scheduled execution using cron.

---

## English

### Overview

This repository provides Python automation scripts to manage port states (Enable/Disable) on managed switching hubs that only offer a Web GUI interface. By leveraging Playwright in headless mode, these scripts interact directly with complex web frames and JavaScript-driven UI components. Both single-port and multi-port batch configurations are supported.

### Verified Hardware & Firmware

| Manufacturer | Model               | Firmware Version |
|:------------ |:------------------- |:---------------- |
| **SODOLA**   | SL902-SWTGW218AS-JP | V200.2.4         |
| **TP-Link** | TL-SG108E | 1.0.0 Build 20230218 Rel.50633 |

> **Note on SODOLA Switch:**  
> Port 9 (SFP) on the SODOLA switch cannot be controlled using this script. Only RJ45 ports (Ports 1–8) are supported.

### Features

- **Multi-Port Batch Control:** Configure multiple ports in a single command using array syntax (e.g., `'[1, 2, 8]'`).
- **Sequential Verification (TP-Link):** Inspects the WebUI table after each port modification to ensure the state has updated before proceeding to subsequent ports, including an explicit cooldown delay.
- **Fail-Fast Authentication:** Detects login failure banners/DOM elements immediately and aborts execution with clean error logs.
- **Strict Validation:** Rejects out-of-range ports (outside 1–8) and invalid actions before browser dispatch.
- **Process Guarding:** Strict internal timeouts combined with shell-level execution caps prevent hanging Chromium instances.

### Requirements

- Python 3.10+
- [Playwright](https://playwright.dev/python/)

### Installation

1. Install Playwright and required browser binaries:
	```bash
	pip3 install playwright
	playwright install chromium
	playwright install-deps chromium
	```
2. Make the scripts executable:
	```bash
	chmod +x switch_gui_ctrl_sodola.py switch_gui_ctrl_tp-link.py
	```

### Usage

#### SODOLA Switch (`switch_gui_ctrl_sodola.py`)

```bash
./switch_gui_ctrl_sodola.py <switch_ip> <username> <password> <port|'[port, ...]' (1-8)> <enable|disable>

# Multi-port batch configuration (Disable Ports 1, 2, and 8)
./switch_gui_ctrl_sodola.py 192.168.100.204 admin 'your_password' '[1, 2, 8]' disable

# Single-port configuration (Enable Port 8)
./switch_gui_ctrl_sodola.py 192.168.100.204 admin 'your_password' 8 enable
```

#### TP-Link Switch (`switch_gui_ctrl_tp-link.py`)

```bash
./switch_gui_ctrl_tp-link.py <switch_ip> <username> <password> <port|'[port, ...]' (1-8)> <enable|disable>

# Multi-port batch configuration (Disable Ports 1, 2, and 8)
./switch_gui_ctrl_tp-link.py 192.168.100.205 admin 'your_password' '[1, 2, 8]' disable

# Single-port configuration (Enable Port 8)
./switch_gui_ctrl_tp-link.py 192.168.100.205 admin 'your_password' 8 enable
```

> **Note on Shell Quoting:**
> Always enclose array arguments in quotes (e.g., `'[1, 2, 8]'`) to avoid parameter expansion or word splitting by your shell.

### Robustness & Timeout Handling

To prevent server memory exhaustion and zombie processes caused by unresponsive switches or hanging Web UIs, the scripts incorporate a two-layer safety mechanism:

1. **Python Script Layer:**
	- Operation and navigation timeouts are constrained to 15 seconds (`context.set_default_timeout(15000)`).
	- Network idle wait states (`networkidle`) are capped at 10 seconds.
	- Guaranteed resource cleanup via `try...finally` blocks to ensure `browser.close()` is always executed even on exceptions.
2. **OS / Process Layer (Wrapper Script):**
	- Wrapper shell scripts enforce hard execution limits using `timeout -s KILL 60s` to prevent background process accumulation.

### Automation via cron (Best Practice)

When automating with `cron`, invoke these scripts using wrapper shell scripts and stagger schedule timings by 1–2 minutes:

- **Avoid Special Character Issues:** Passwords containing `%` will be broken by cron's interpreter unless wrapped in a shell script.
- **Prevent Browser Collisions:** Stagger execution times by 1–2 minutes to avoid concurrent headless Chromium profile locks.
- **Process Guard Example:**
	```bash
	/usr/bin/timeout -s KILL 60s /usr/bin/python3 /usr/local/bin/switch_gui_ctrl_sodola.py 192.168.100.204 admin 'your_password' '[1, 2, 8]' disable >> /var/log/switch_ctrl_sodola.log 2>&1
	```

---

## 日本語

### 概要

Web GUI のみ提供されているマネージドスイッチングハブのポート状態（有効/無効）を自動で切り替えるための Python スクリプトです。Playwright のヘッドレスブラウザ機能を活用し、フレームセットや JavaScript で制御された WebUI を直接操作します。単一ポートの指定だけでなく、複数ポートの一括制御に対応しています。

### 動作確認済み機器・ファームウェア

| メーカー    | モデル名            | ファームウェアバージョン       |
| ----------- | ------------------- | ------------------------------ |
| **SODOLA**  | SL902-SWTGW218AS-JP | V200.2.4                       |
| **TP-Link** | TL-SG108E           | 1.0.0 Build 20230218 Rel.50633 |

> **SODOLA スイッチに関する注意点:**
> SODOLA スイッチの 9番ポート（SFP）は本スクリプトでは制御できません（制御対象は 1〜8番ポートのみとなります）。

### 主な機能

- **複数ポートの一括制御:** 配列形式（例: `'[1, 2, 8]'`）による複数ポートの同時指定に対応。
- **反映確認とウェイト処理（TP-Link）:** プルダウン選択式の TP-Link において、1ポート変更ごとに画面内テーブルのステータス変化を監視・確認し、待機時間を挟みながら確実に次のポートを設定。
- **ログイン失敗の即時検知:** ユーザー名・パスワードの不一致やエラー表示を判定し、無駄なリトライを行わず即時中断。
- **厳密な引数バリデーション:** 指定ポート番号の範囲（1〜8）やアクション文字の正当性を事前チェック。
- **プロセスのゾンビ化防止:** スクリプト内部のタイムアウト処理とシェル側の強制キルによる2重の防護設計。

### 必要要件

- Python 3.10 以上
- [Playwright](https://playwright.dev/python/?utm_source=gemini)

### インストール手順

1. Playwright および依存ブラウザ（Chromium）のインストール:
	```bash
	pip3 install playwright
	playwright install chromium
	playwright install-deps chromium
	```
2. スクリプトに実行権限を付与:
	```bash
	chmod +x switch_gui_ctrl_sodola.py switch_gui_ctrl_tp-link.py
	```

### 使用方法

#### SODOLA スイッチ用 (`switch_gui_ctrl_sodola.py`)

```bash
./switch_gui_ctrl_sodola.py <スイッチIP> <ユーザー名> <パスワード> <ポート番号|'[ポート, ...]' (1-8)> <enable|disable>

# 複数ポートの一括指定例 (1番、2番、8番ポートを無効化)
./switch_gui_ctrl_sodola.py 192.168.100.204 admin 'your_password' '[1, 2, 8]' disable

# 単一ポートの指定例 (8番ポートを有効化)
./switch_gui_ctrl_sodola.py 192.168.100.204 admin 'your_password' 8 enable
```

#### TP-Link スイッチ用 (`switch_gui_ctrl_tp-link.py`)

```bash
./switch_gui_ctrl_tp-link.py <スイッチIP> <ユーザー名> <パスワード> <ポート番号|'[ポート, ...]' (1-8)> <enable|disable>

# 複数ポートの一括指定例 (1番、2番、8番ポートを無効化)
./switch_gui_ctrl_tp-link.py 192.168.100.205 admin 'your_password' '[1, 2, 8]' disable

# 単一ポートの指定例 (8番ポートを有効化)
./switch_gui_ctrl_tp-link.py 192.168.100.205 admin 'your_password' 8 enable
```

> **シェルのエスケープについて:**
> 配列形式でポートを指定する際は、シェルによるブラケット展開やスペースの分割を防ぐため、必ず引数をクォーテーションで囲んでください（例: `'[1, 2, 8]'`）。

### 安定性・タイムアウト対策

機器のWebUI応答遅延や通信切断によるプロセスのゾンビ化、メモリ枯渇によるサーバーフリーズを防ぐため、**2重のタイムアウト保護設計**を採用しています。

1. **Python スクリプト層の保護:**
	- 画面遷移および各操作のデフォルトタイムアウトを 15 秒に設定。
	- `networkidle` の無限待機を防ぐため 10 秒の上限を設定。
	- `try...finally` 構文により、例外発生時や途中停止時でも確実に `browser.close()` を実行して Chromium プロセスを解放。
2. **OS / プロセス層の保護（ラッパースクリプト）:**
	- シェルスクリプト側で `timeout -s KILL 60s` を付与し、不測のフリーズ時にも最大60秒でプロセスを強制終了。

### cron による自動実行時の注意点

cron から実行する場合、以下のトラブルを防ぐために**シェルスクリプト（ラッパー）経由での呼び出し**および**実行時刻を1〜2分ずらしたスケジュール設定**を推奨します。

- **特殊文字のエスケープ回避:** パスワードに含まれる `%` 記号は cron では改行として扱われるため、シェルスクリプトに引数を隠蔽することで構文エラーを防ぎます。
- **ブラウザ競合の防止:** ヘッドレス Chromium のプロファイル衝突や高負荷を防ぐため、同時刻ではなく1〜2分間隔を空けて実行します。
- **実行コマンド例（ラッパー内）:**
	```bash
	/usr/bin/timeout -s KILL 60s /usr/bin/python3 /usr/local/bin/switch_gui_ctrl_sodola.py 192.168.100.204 admin 'your_password' '[1, 2, 8]' disable >> /var/log/switch_ctrl_sodola.log 2>&1
	```
