# switch-port-controller

Playwright-based automation scripts to enable or disable network switch ports via Web GUI. Designed for scheduled network operations using cron.

---

## English

### Overview

This repository provides Python automation scripts to manage port states (Enable/Disable) on managed switching hubs that only offer a Web GUI interface. By leveraging Playwright in headless mode, these scripts interact directly with complex web frames and JavaScript-driven UI components without requiring manual browser interaction.

### Verified Hardware & Firmware

| Manufacturer | Model               | Firmware Version               |
|:------------ |:------------------- |:------------------------------ |
| **SODOLA**   | SL902-SWTGW218AS-JP | V200.2.4                       |
| **TP-Link**  | TL-SG108E           | 1.0.0 Build 20230218 Rel.50633 |

> **Note on SODOLA Switch:**  
> Port 9 (SFP) on the SODOLA switch cannot be controlled using this script. Only RJ45 ports (Ports 1–8) are supported.

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
./switch_gui_ctrl_sodola.py <switch_ip> <username> <password> <port(1-8)> <enable|disable>

# Example: Disable Port 8
./switch_gui_ctrl_sodola.py 192.168.100.4 swuser 'your_password' 8 disable

# Example: Enable Port 8
./switch_gui_ctrl_sodola.py 192.168.100.4 swuser 'your_password' 8 enable
```

#### TP-Link Switch (`switch_gui_ctrl_tp-link.py`)

```bash
./switch_gui_ctrl_tp-link.py <switch_ip> <username> <password> <port(1-8)> <enable|disable>

# Example: Disable Port 8
./switch_gui_ctrl_tp-link.py 192.168.100.5 swuser 'your_password' 8 disable

# Example: Enable Port 8
./switch_gui_ctrl_tp-link.py 192.168.100.5 swuser 'your_password' 8 enable
```

### Automation via cron (Recommendation)

If you automate execution via `cron`, it is recommended to invoke these scripts via wrapper shell scripts to prevent password parsing issues (e.g., `%` interpreted as a newline by cron) and stagger execution times by a few minutes to prevent headless browser collisions.

---

## 日本語

### 概要

Web GUI のみ提供されているマネージドスイッチングハブのポート状態（有効/無効）を自動で切り替えるための Python スクリプトです。Playwright のヘッドレスブラウザ機能を活用し、フレームセットや JavaScript で制御された WebUI を直接操作することで、スケジュールされたポート制御（cron 等）を実現します。

### 動作確認済み機器・ファームウェア

| メーカー    | モデル名            | ファームウェアバージョン       |
| ----------- | ------------------- | ------------------------------ |
| **SODOLA**  | SL902-SWTGW218AS-JP | V200.2.4                       |
| **TP-Link** | TL-SG108E           | 1.0.0 Build 20230218 Rel.50633 |

> **SODOLA スイッチに関する注意点:**
> SODOLA スイッチの 9番ポート（SFP）は本スクリプトでは制御できません（制御対象は 1〜8番ポートのみとなります）。

### 必要要件

* Python 3.10 以上
* [Playwright](https://playwright.dev/python/?utm_source=gemini)

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
./switch_gui_ctrl_sodola.py <スイッチIP> <ユーザー名> <パスワード> <ポート番号(1-8)> <enable|disable>

# 実行例: 8番ポートを無効化
./switch_gui_ctrl_sodola.py 192.168.100.204 swuser 'your_password' 8 disable

# 実行例: 8番ポートを有効化
./switch_gui_ctrl_sodola.py 192.168.100.204 swuser 'your_password' 8 enable
```

#### TP-Link スイッチ用 (`switch_gui_ctrl_tp-link.py`)

```bash
./switch_gui_ctrl_tp-link.py <スイッチIP> <ユーザー名> <パスワード> <ポート番号(1-8)> <enable|disable>

# 実行例: 8番ポートを無効化
./switch_gui_ctrl_tp-link.py 192.168.100.205 swuser 'your_password' 8 disable

# 実行例: 8番ポートを有効化
./switch_gui_ctrl_tp-link.py 192.168.100.205 swuser 'your_password' 8 enable
```

### cron による自動実行時の注意点

cron から実行する場合、パスワードに含まれる `%` 記号が改行として誤認される問題や、複数インスタンスの Chromium が同一秒に起動した際の衝突を防ぐため、**シェルスクリプト（ラッパー）経由での呼び出し**および**実行時刻を1〜2分ずらしたスケジュール設定**を推奨します。
