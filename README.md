# Monkeytype for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-0.5.0-blue)
![HA](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-brightgreen)

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

In `configuration.yaml`:

```yaml
monkeytype:
  api_key: DEIN_APE_KEY
  mode: time        # optional – default: time
  mode2: "60"       # optional – default: "60"
  language: english # optional – default: english
```

**Mehrere Modi gleichzeitig** (z. B. 15s und 60s):

```yaml
monkeytype:
  - api_key: DEIN_APE_KEY
    mode2: "60"
  - api_key: DEIN_APE_KEY
    mode2: "15"
```

Nach dem Neustart tauchen die Sensoren automatisch auf:

| Entity | Beschreibung |
|---|---|
| `sensor.monkeytype_today_best_wpm_time60_english` | Heutige Höchst-WPM |
| `sensor.monkeytype_rank_time60_english` | Leaderboard-Rang (`unknown` wenn nicht platziert) |

---

## Lovelace Card

### Ressource registrieren

`www/monkeytype-card.js` nach `config/www/` kopieren, dann unter
**Einstellungen → Dashboards → ⋮ → Ressourcen** eintragen:

| URL | Typ |
|---|---|
| `/local/monkeytype-card.js` | JavaScript-Modul |

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

### 0.5.0
- Initiales Release
- Sensoren: Today Best WPM, Leaderboard Rank
- Lovelace Card: `monkeytype-card`
