# 🚗 XPENG Vehicles Integration for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg)](https://home-assistant.io)

Offizielle Community-Integration zur Einbindung von **XPENG-Elektrofahrzeugen** (z. B. **XPENG X9**, G9, G6, P7) in Home Assistant.

Entwickelt für den täglichen Telemetrie- und Ladedaten-Abgleich mit deinem Smarthome und dem **Home Assistant Energy Dashboard**!

---

## ✨ Features

* **⚡ Energy Dashboard Zähler (`total_increasing` in `kWh`):**
  * `sensor.<name>_energy_charged` erfasst die kumulierte Ladeenergie und kann direkt im HA Energy Dashboard unter *Individual Devices* ausgewählt werden.
* **🏠 Intelligente Erkennung von Wallbox-Ladungen zu Hause:**
  * `sensor.<name>_home_energy_charged` filtert Ladevorgänge an deiner privaten Wallbox anhand deines individuellen Nachtzeitfensters und Ladeleistungsbereichs (z. B. 8–12 kW).
* **📊 Vollständige Fahrzeug-Telemetrie:**
  * **Akkustand (SoC %):** `sensor.<name>_battery_level`
  * **Restreichweite (km):** `sensor.<name>_range`
  * **Kilometerstand (km):** `sensor.<name>_odometer` (`total_increasing` für Tages- und Monatserfassung)
  * **Reifendrücke (bar):** 4 Einzelsensoren für alle Reifen (FL, FR, RL, RR)
  * **Batterietemperatur (°C):** Maximal- und Minimaltemperatur des Akkupacks
  * **Batteriespannung (V):** Hochvolt-BMS-Spannung (800V-Architektur)
  * **Letzte Ladung (kWh):** Energiemenge des letzten Ladezyklus
* **🔄 Dual-Import-Modus:**
  1. **Lokaler Datei-Drop (sofort nutzbar):** Lege die heruntergeladenen CSVs oder das ZIP-Archiv in einem Ordner (z. B. `/config/xpeng/`) ab.
  2. **XPENG Open Platform API:** Vollautomatischer täglicher Datenabruf über die offizielle EU Open Platform API (`/oauth2/queryData`).
* **🧹 Automatische Speicher-Retention:**
  * Verhindert das Zumüllen deiner Home Assistant Festplatte: Große CSV-Dumps werden nach erfolgreicher Verarbeitung automatisch gelöscht (einstellbar in den Optionen).
* **🔘 Manueller Sync-Button:**
  * Über `button.<name>_sync_data` kann der Datenimport jederzeit sofort per Knopfdruck oder Automation ausgelöst werden.

---

## 📦 Installation via HACS

1. Öffne **HACS** in deinem Home Assistant.
2. Klicke oben rechts auf das Drei-Punkte-Menü $\rightarrow$ **Benutzerdefinierte Repositories**.
3. Füge die URL dieses Repositories ein und wähle die Kategorie **Integration**.
4. Klicke auf **Herunterladen**.
5. Starte Home Assistant neu.

---

## ⚙️ Konfiguration

1. Gehe in Home Assistant auf **Einstellungen** $\rightarrow$ **Geräte & Dienste** $\rightarrow$ **Integration hinzufügen**.
2. Suche nach **XPENG Vehicles**.
3. Wähle den Fahrzeugnamen (z. B. `Lexi`) und deinen bevorzugten Modus:
   * **Lokaler Ordner:** Gib den Pfad an, in dem du CSVs/ZIPs ablegst (Standard: `/config/xpeng`).
   * **XPENG Open Platform API:** Gib deine `appId`, `appSecret`, `openId` und `accessToken` ein.

### Optionen anpassen:
Über **Konfigurieren** an der Integration kannst du jederzeit folgende Parameter anpassen:
* *Dateien nach Import automatisch löschen (Speicherschutz)*
* *Wallbox-Erkennung aktivieren / deaktivieren*
* *Leistungsbereich für Wallbox (Standard: 8,0 bis 12,0 kW)*
* *Nachtladefenster Start & Ende (Standard: 20:00 Uhr bis 07:00 Uhr)*

---

## ⚡ Energy Dashboard einrichten

1. Öffne **Einstellungen** $\rightarrow$ **Dashboards** $\rightarrow$ **Energie**.
2. Scrolle zu **Einzelne Geräte** (Individual Devices).
3. Klicke auf **Gerät hinzufügen** und wähle deinen Sensor:
   * `sensor.lexi_energy_charged` (Gesamte Ladeenergie) oder
   * `sensor.lexi_home_energy_charged` (nur Zuhause geladene Energie).
4. Home Assistant berechnet nun automatisch den täglichen Ladeenergieverbrauch deines XPENG!

---

## 📄 Lizenz
MIT License
