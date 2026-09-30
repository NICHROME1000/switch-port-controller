# switch-port-controller

Playwright-based automation scripts to enable or disable network switch ports via Web GUI. Supports multi-port batch operations and is optimized for low-memory headless servers running scheduled cron jobs.

---

## English

### Overview
This repository provides Python automation scripts to manage port states (Enable/Disable) on managed switching hubs that only offer a Web GUI interface. By leveraging Playwright in headless mode, these scripts interact directly with complex web frames and JavaScript-driven UI components. Both single-port and multi-port batch configurations are supported.

### Verified Hardware & Firmware
| Manufacturer | Model | Firmware Version |
| :--- | :--- | :--- |
| **SODOLA** | SL902-SWTGW218AS-JP | V200.2.4 |
| **TP-Link** | TL-SG108E | 1.0.0 Build 20230218 Rel.50633 |

> **Note on SODOLA Switch:**  
> Port 9 (SFP) on the SODOLA switch cannot be controlled using this script. Only RJ45 ports (Ports 1–8) are supported.

### Features
- **Multi-Port Batch Control:** Configure multiple ports in a single command using array syntax (e.g., `'[1, 2, 8]'`).
- **Sequential Verification (TP-Link):** Inspects the WebUI table after each port modification to ensure the state has updated before proceeding to subsequent ports, including an explicit cooldown delay.
- **Fail-Fast Authentication:** Detects login failure banners/DOM elements immediately and aborts execution with clean error logs.
- **Strict Validation:** Rejects out-of-range ports (outside 1–8) and invalid actions before browser dispatch.
- **Resource & Memory Optimization:** Tuned with lightweight browser flags (`--no-sandbox`, `--disable-dev-shm-usage`, `--disable-gpu`, `--single-process`) to operate safely even on 1GB RAM instances.
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

### Robustness & Low-Memory Server Best Practices

To prevent system crashes (OOM freezes) and lingering zombie processes on resource-constrained servers:

1. **Chromium Memory Minimization:**
Scripts launch Chromium with `--disable-dev-shm-usage` (uses disk temp instead of `/dev/shm`), `--no-sandbox`, `--disable-gpu`, and `--single-process` to eliminate unnecessary multi-process overhead.
2. **Two-Layer Timeout Architecture:**
* **Internal (Playwright):** 15s operation/navigation timeout and a 10s network-idle cap with guaranteed `browser.close()` inside `try...finally`.
* **External (Wrapper Shell):** Enforces a hard execution barrier using `/usr/bin/timeout -s KILL 60s`.


3. **Swap Requirement:**
For servers with 1GB RAM or less, configuring at least a 2GB swap file (`/swapfile`) is strongly recommended to absorb brief browser launch spikes and prevent kernel lockups.

### Automation via cron (Best Practice)

When automating with `cron`, invoke these scripts using wrapper shell scripts and stagger schedule timings by 1–2 minutes:

* **Avoid Special Character Issues:** Passwords containing `%` will be broken by cron's interpreter unless wrapped in a shell script.
* **Prevent Browser Collisions:** Stagger execution times by 1–2 minutes to avoid concurrent headless Chromium profile locks.
* **Wrapper Execution Example:**
```bash
/usr/bin/timeout -s KILL 60s /usr/bin/python3 /usr/local/bin/switch_gui_ctrl_sodola.py 192.168.100.204 admin 'your_password' '[1, 2, 8]' disable >> /var/log/switch_ctrl_sodola.log 2>&1

```



---

## 日本語

### 概要

Web GUI のみ提供されているマネージドスイッチングハブのポート状態（有効/無効）を自動で切り替えるための Python スクリプトです。Playwright のヘッドレスブラウザ機能を活用し、フレームセットや JavaScript で制御された WebUI を直接操作します。単一ポートの指定だけでなく、複数ポートの一括制御に対応し、低メモリ環境（RAM 1GB 程度）でも安定して稼働するよう設計されています。

### 動作確認済み機器・ファームウェア

| メーカー | モデル名 | ファームウェアバージョン |
| --- | --- | --- |
| **SODOLA** | SL902-SWTGW218AS-JP | V200.2.4 |
| **TP-Link** | TL-SG108E | 1.0.0 Build 20230218 Rel.50633 |

> **SODOLA スイッチに関する注意点:**
> SODOLA スイッチの 9番ポート（SFP）は本スクリプトでは制御できません（制御対象は 1〜8番ポートのみとなります）。

### 主な機能

* **複数ポートの一括制御:** 配列形式（例: `'[1, 2, 8]'`）による複数ポートの同時指定に対応。
* **反映確認とウェイト処理（TP-Link）:** プルダウン選択式の TP-Link において、1ポート変更ごとに画面内テーブルのステータス変化を監視・確認し、待機時間を挟みながら確実に次のポートを設定。
* **省メモリ設計:** `--no-sandbox`、`--disable-dev-shm-usage`、`--disable-gpu`、`--single-process` を指定し、RAM 1GB 以下のサーバーでも安全に動作。
* **ログイン失敗の即時検知:** 認証エラー表示を検知して即座に終了ステータスで中断。
* **厳密な引数バリデーション:** 指定ポート番号の範囲（1〜8）やアクション文字の正当性を事前チェック。
* **プロセスのゾンビ化防止:** スクリプト内部のタイムアウト処理とシェル側の強制キルによる2重の防護設計。

### 必要要件

* Python 3.10 以上
* [Playwright](https://playwright.dev/python/)

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

### 安定性・低メモリ環境での運用指針

機器のWebUI応答遅延や、小規模サーバー（RAM 1GB 程度）でのメモリ枯渇（OOM フリーズ）を防ぐため、以下の対策を適用しています。

1. **Chromium の省メモリ最適化:**
`/dev/shm` 枯渇を防ぐ `--disable-dev-shm-usage` や、マルチプロセス起動を抑制する `--single-process` フラグを適用済みです。
2. **2重のタイムアウト保護:**
* **Python 層:** 画面遷移・操作のタイムアウト（15秒）と `try...finally` によるブラウザプロセスの確実な解放。
* **OS 層（ラッパー）:** `timeout -s KILL 60s` により、万が一のフリーズ時にもプロセスを強制終了。


3. **スワップ領域（Swap）の確保（推奨）:**
RAM 1GB 以下のサーバーでは、OSの定期メンテナンス（apt更新メトリクス収集等）との競合によるハングアップを防ぐため、**最低 2GB のスワップファイル（`/swapfile`）の配備を推奨**します。

### cron による自動実行時の注意点

cron から実行する場合、以下のトラブルを防ぐために**シェルスクリプト（ラッパー）経由での呼び出し**および**実行時刻を1〜2分ずらしたスケジュール設定**を推奨します。

* **特殊文字のエスケープ回避:** パスワードに含まれる `%` 記号は cron では改行として扱われるため、シェルスクリプトに引数を隠蔽することで構文エラーを防ぎます。
* **ブラウザ競合の防止:** ヘッドレス Chromium のプロファイル衝突や高負荷を防ぐため、同時刻ではなく1〜2分間隔を空けて実行します。
* **実行コマンド例（ラッパー内）:**
```bash
/usr/bin/timeout -s KILL 60s /usr/bin/python3 /usr/local/bin/switch_gui_ctrl_sodola.py 192.168.100.204 admin 'your_password' '[1, 2, 8]' disable >> /var/log/switch_ctrl_sodola.log 2>&1

```
