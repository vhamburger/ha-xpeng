# 🚗 XPENG Vehicles Integration for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://home-assistant.io)

Community integration to connect **XPENG Electric Vehicles** (e.g. **XPENG X9**, G9, G6, P7) to Home Assistant.

Designed for daily telemetry tracking and charging data matching with your smart home and the **Home Assistant Energy Dashboard**!

---

## ✨ Features

* **⚡ Energy Dashboard Ready (`total_increasing` in `kWh`):**
  * `sensor.<vehicle_name>_energy_charged` tracks cumulative charged energy and can be selected directly under *Energy Dashboard → Individual Devices*.
* **🏠 Intelligent Home Wallbox Detection:**
  * `sensor.<vehicle_name>_home_energy_charged` classifies charging sessions at your private wallbox using configurable night-time hours and power thresholds (e.g. 8–12 kW for 11 kW AC wallboxes).
* **📊 Comprehensive Vehicle Telemetry:**
  * **Battery State of Charge (SoC %):** `sensor.<vehicle_name>_battery_level`
  * **Remaining Range (km):** `sensor.<vehicle_name>_range`
  * **Odometer (km):** `sensor.<vehicle_name>_odometer` (`total_increasing` for daily and monthly mileage tracking)
  * **Tire Pressures (bar):** Individual sensors for all 4 wheels (Front Left, Front Right, Rear Left, Rear Right)
  * **Battery Temperature (°C):** Maximum and minimum temperature of the high-voltage pack
  * **Battery Voltage (V):** High-voltage BMS pack voltage (800V architecture)
  * **Last Charge Energy (kWh):** Energy added during the most recent charging session
* **🔄 Dual-Import Mode:**
  1. **Local File Drop (ready to use):** Simply place downloaded GDPR CSV export files or ZIP archives into a configured directory (e.g. `/config/xpeng/`).
  2. **XPENG Open Platform API:** Automated daily data fetch via the official EU Open Platform API (`/oauth2/queryData`).
* **🧹 Automatic Storage Retention:**
  * High-frequency CAN-bus CSV files can be large (50–60 MB). Once processed and accounted for in the cumulative meters, raw files are automatically removed to protect your Home Assistant storage (can be toggled in options).
* **🔘 Manual Sync Button:**
  * `button.<vehicle_name>_sync_data` lets you trigger an immediate scan/refresh from your dashboard or automations.

---

## 🇪🇺 EU Region & How to Access Your XPENG Data

> [!NOTE]
> This integration is based on the data export mechanisms provided under European Union regulations (**GDPR** and the **EU Data Act**). As a result, this data access is currently tailored to **European XPENG vehicles and EU accounts**.

You can obtain vehicle data in two ways:

### 1. Manual File Download (GDPR Data Export)
* Log in with your XPENG owner account on the official European XPENG website / owner portal.
* Request your vehicle data download (GDPR data export).
* XPENG prepares a ZIP archive containing the 3 high-resolution telemetry CSV files (`driving_power_energy`, `driving_operation`, `driving_status`).
* Place the ZIP or extracted CSV files into your configured Home Assistant directory (default: `/config/xpeng/`). The integration will automatically parse the data and update your sensors!

### 2. Automated API Access (XPENG Open Platform)
* For automatic daily fetching directly from XPENG's servers, you can apply for API access via the official Open Platform.
* Refer to the official [XPENG Open Platform API Integration Guide](https://static-eu.xiaopeng.com/xp-ucenter/api-integration-guide-en-0.0.1.html).
* To request API credentials (`appId` and `appSecret`), send an email to **`glo.open@xpeng.com`** with:
  * Your integrating entity/user name
  * Application name (e.g. `Home Assistant`)
  * Contact email address
* Once approved and authenticated, you will receive `openId` and `accessToken` to enter into the integration's setup dialog.

---

## 📦 Installation via HACS

1. Open **HACS** in your Home Assistant.
2. Click the **three dots** in the top right corner $\rightarrow$ **Custom repositories**.
3. Enter the repository URL: `https://github.com/<your-username>/ha-xpeng`
4. Category: **Integration**.
5. Click **Add**.
6. Search for **XPENG Vehicles**, click **Download**, and restart Home Assistant.

---

## ⚙️ Configuration

1. In Home Assistant, navigate to **Settings** $\rightarrow$ **Devices & Services** $\rightarrow$ **Add Integration**.
2. Search for **XPENG Vehicles**.
3. Choose your vehicle name (e.g. `My XPENG`), vehicle model (Auto-Detect or pick your model from the dropdown), and your preferred import mode:
   * **Local Directory:** Enter the path where you drop CSVs/ZIPs (default: `/config/xpeng`).
   * **XPENG Open Platform API:** Enter your `appId`, `appSecret`, `openId`, and `accessToken`.

### Options & Customization:
Click **Configure** on the integration card at any time to adjust:
* *Delete processed files after import (save storage)*: enabled by default
* *Enable home wallbox detection*: enabled by default
* *Wallbox power range (kW)*: default `8.0` to `12.0` kW
* *Night charging window*: default `20:00` to `07:00`

---

## ⚡ Setup with Home Assistant Energy Dashboard

1. Navigate to **Settings** $\rightarrow$ **Dashboards** $\rightarrow$ **Energy**.
2. Scroll to **Individual Devices**.
3. Click **Add Device** and select:
   * `sensor.<vehicle_name>_energy_charged` (Total energy charged across all sessions) or
   * `sensor.<vehicle_name>_home_energy_charged` (Home wallbox charging only).
4. Home Assistant will automatically calculate and display your vehicle's charging energy consumption!

---

## 📄 License
MIT License
