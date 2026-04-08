# Monkeytype for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-0.6.0-blue)
![HA](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-brightgreen)
&nbsp;&nbsp;[🇩🇪 Deutsche Version](README.de.md)

Brings your [Monkeytype](https://monkeytype.com) stats directly into your Home Assistant dashboard –
as native sensors and a compact Lovelace card.

---

## Features

- **Sensor: Today Best WPM** – highest WPM of the current day, filtered by mode and language
- **Sensor: Leaderboard Rank** – your current global rank on the Monkeytype leaderboard
- **Lovelace Card** – compact card with keyboard icon and inline values
- Polls every 5 minutes (well within the API rate limit)
- Automatically adapts to the HA theme (light/dark)

---

## Prerequisites

- Home Assistant 2024.1 or newer
- A Monkeytype account with a generated **ApeKey**

### Creating an ApeKey

1. Log in at [monkeytype.com](https://monkeytype.com)
2. Go to **Account → Ape Keys → Generate New**
3. Enable scopes: `results`, `leaderboards`
4. Copy the key and store it safely

---

## Installation via HACS

1. Open HACS → **Integrations**
2. Click **⋮ → Custom Repositories** (top right)
3. Enter URL: `https://github.com/HACucoo/monkeytype-ha`
   Category: **Integration**
4. Click **Add**, then search for the integration in HACS and install it
5. Restart Home Assistant

---

## Manual Installation

```
config/
└── custom_components/
    └── monkeytype/
        ├── __init__.py
        ├── sensor.py
        ├── const.py
        └── manifest.json
```

Copy the folder from the [latest release](https://github.com/HACucoo/monkeytype-ha/releases) into `custom_components/monkeytype/`, then restart HA.

---

## Configuration

The integration is configured entirely through the Home Assistant UI – no `configuration.yaml` needed.

**Settings → Devices & Services → Add Integration → "Monkeytype"**

Fill in the following fields:

| Field | Description | Default |
|---|---|---|
| ApeKey | API key from your Monkeytype account | – |
| Mode | `time`, `words`, `quote`, `custom`, `zen` | `time` |
| Mode detail | e.g. `60`, `15`, `100` | `60` |
| Language | e.g. `english`, `german` | `english` |

The ApeKey is validated against the API immediately on save.

**Multiple modes** (e.g. 15s and 60s) can be set up by adding the integration again with different values.

### Generated sensors

The entity ID is composed from the configured values:

```
sensor.monkeytype_today_best_wpm_{mode}{mode2}_{language}
sensor.monkeytype_rank_{mode}{mode2}_{language}
```

With the default values (`time`, `60`, `english`) this results in:

| Entity | Description |
|---|---|
| `sensor.monkeytype_today_best_wpm_time60_english` | Today's highest WPM |
| `sensor.monkeytype_rank_time60_english` | Leaderboard rank (`unknown` if not ranked) |

With `Mode detail: 15` it would be `..._time15_english` and so on.

---

## Lovelace Card

### Register resource

The card is bundled with the integration and served automatically.
Add it once under **Settings → Dashboards → ⋮ → Resources**:

| URL | Type |
|---|---|
| `/monkeytype/monkeytype-card.js` | JavaScript module |

No manual file copying needed – HACS handles it.

### Add the card

In the dashboard editor → **Add card → Manual:**

```yaml
type: custom:monkeytype-card
wpm_entity: sensor.monkeytype_today_best_wpm_time60_english
rank_entity: sensor.monkeytype_rank_time60_english
label: Monkeytype   # optional
```

The card takes up exactly one row and looks like this:

```
⌨  MONKEYTYPE
   89.5 WPM  │  #1,234 Rank
```

---

## Changelog

### 0.6.0
- Fix: correct API endpoint (`/results`)
- Fix: `X-Client-Version` header added
- Fix: 471 (ApeKey inactive) shows clear error message
- Fix: 479 (rate limit) raises UpdateFailed – last known values are preserved
- Fix: guard against null API responses
- Fix: use HA-managed aiohttp session
- Fix: non-blocking HA startup
- Feat: Lovelace card bundled inside component directory (no manual file copy needed)

### 0.5.0
- Initial release
- Sensors: Today Best WPM, Leaderboard Rank
- Lovelace Card: `monkeytype-card`
