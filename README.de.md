# Monkeytype für Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-0.7.2-blue)
![HA](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-brightgreen)
&nbsp;&nbsp;[🇬🇧 English version](README.md)

Bringt deine [Monkeytype](https://monkeytype.com)-Stats direkt ins Home Assistant Dashboard –
als native Sensoren und als kompakte Lovelace-Karte.

---

## Features

- **Sensor: Today Best WPM** – höchste WPM des heutigen Tages, gefiltert auf Modus und Sprache
- **Sensor: Leaderboard Rank** – aktueller globaler Rang auf der Monkeytype-Bestenliste
- **Lovelace Card** – platzsparende Karte mit Tastatur-Icon und Fließtext
- Polling alle 5 Minuten (innerhalb des API-Rate-Limits)
- Passt sich automatisch dem HA-Theme (Hell/Dunkel) an

---

## Voraussetzungen

- Home Assistant 2024.1 oder neuer
- Ein Monkeytype-Account mit generiertem **ApeKey**

### ApeKey erstellen

1. Auf [monkeytype.com](https://monkeytype.com) einloggen
2. **Account → Ape Keys → Generate New**
3. Scopes aktivieren: `results`, `leaderboards`
4. Key kopieren und sicher aufbewahren

---

## Installation via HACS

1. HACS öffnen → **Integrationen**
2. Oben rechts auf **⋮ → Benutzerdefinierte Repositories**
3. URL eintragen: `https://github.com/HACucoo/monkeytype-ha`
   Kategorie: **Integration**
4. **Hinzufügen** klicken, danach die Integration in HACS suchen und installieren
5. Home Assistant neu starten

---

## Manuelle Installation

```
config/
└── custom_components/
    └── monkeytype/
        ├── __init__.py
        ├── sensor.py
        ├── const.py
        └── manifest.json
```

Ordner aus dem [neuesten Release](https://github.com/HACucoo/monkeytype-ha/releases) nach `custom_components/monkeytype/` kopieren, dann HA neu starten.

---

## Konfiguration

Die Integration wird vollständig über die Home Assistant UI eingerichtet – keine `configuration.yaml` nötig.

**Einstellungen → Geräte & Dienste → Integration hinzufügen → „Monkeytype"**

Im Dialog folgende Felder ausfüllen:

| Feld | Beschreibung | Standard |
|---|---|---|
| ApeKey | API-Schlüssel aus deinem Monkeytype-Account | – |
| Modus | `time`, `words`, `quote`, `custom`, `zen` | `time` |
| Modus-Detail | z. B. `60`, `15`, `100` | `60` |
| Sprache | z. B. `english`, `german` | `english` |

Der ApeKey wird beim Speichern direkt gegen die API geprüft.

**Mehrere Modi** (z. B. 15s und 60s) lassen sich durch erneutes Hinzufügen der Integration mit anderen Werten einrichten.

### Erzeugte Sensoren

Die Entity-ID setzt sich aus den konfigurierten Werten zusammen:

```
sensor.monkeytype_today_best_wpm_{mode}{mode2}_{language}
sensor.monkeytype_rank_{mode}{mode2}_{language}
```

Mit den Standardwerten (`time`, `60`, `english`) ergibt das:

| Entity | Beschreibung |
|---|---|
| `sensor.monkeytype_today_best_wpm_time60_english` | Heutige Höchst-WPM |
| `sensor.monkeytype_rank_time60_english` | Leaderboard-Rang (`unknown` wenn nicht platziert) |

Bei `Modus-Detail: 15` wären es entsprechend `..._time15_english` usw.

---

## Lovelace Card

### Ressource registrieren

Die Karte ist im Integration-Paket enthalten und wird automatisch bereitgestellt.
Einmalig unter **Einstellungen → Dashboards → ⋮ → Ressourcen** eintragen:

| URL | Typ |
|---|---|
| `/monkeytype/monkeytype-card.js` | JavaScript-Modul |

Kein manuelles Kopieren nötig – HACS erledigt das.

### Karte einbinden

Im Dashboard-Editor → **Karte hinzufügen → Manuell:**

```yaml
type: custom:monkeytype-card
wpm_entity: sensor.monkeytype_today_best_wpm_time60_english
rank_entity: sensor.monkeytype_rank_time60_english
label: Monkeytype   # optional
```

Die Karte belegt genau eine Zeile und sieht so aus:

```
⌨  MONKEYTYPE
   89.5 WPM  │  #1.234 Rang
```

---

## Changelog

### 0.7.2
- Fix: `UpdateFailed` chained Rate-Limit-Exception sauber (B904)
- Chore: ruff Lint-Config hinzugefügt, modernere `datetime.UTC` und `Callable` Imports

### 0.7.1
- Refactor: Coordinator und Sensoren entdoppelt (gemeinsamer `_request` Helper, `SensorEntityDescription`)
- Feat: 401 löst HA-Reauth-UI automatisch aus
- Feat: Reauth-Flow – ApeKey rotieren ohne Integration zu löschen
- Verbesserung: `/results` mit `onOrAfterTimestamp` Filter – kleineres Payload
- Verbesserung: 471 (ApeKey inaktiv) zur Laufzeit mit klarer Meldung

### 0.7.0
- Feat: Daily Leaderboard Rang-Sensor (`/daily/rank`)
- Feat: Lovelace Card visueller Editor mit Schriftgröße/Icon-Größe
- Feat: smartes Rate-Limit-Backoff via `x-ratelimit-reset` Header
- Fix: 479 beim Setup blockiert Einrichtung nicht mehr
- Fix: Rate Limit behält letzte Sensorwerte statt "Unbekannt"
- Fix: nicht-blockierender Startup mit 30s Verzögerung

### 0.6.0
- Fix: korrekter API-Endpoint (`/results`)
- Fix: `X-Client-Version` Header ergänzt
- Fix: 471 (ApeKey inaktiv) mit klarer Fehlermeldung
- Fix: 479 (Rate Limit) behält letzte bekannte Sensorwerte
- Fix: Absicherung gegen null-API-Responses
- Fix: HA-managed aiohttp-Session
- Fix: nicht-blockierender HA-Startup
- Feat: Lovelace Card im Component-Verzeichnis gebündelt

### 0.5.0
- Initiales Release
- Sensoren: Today Best WPM, Leaderboard Rank
- Lovelace Card: `monkeytype-card`
