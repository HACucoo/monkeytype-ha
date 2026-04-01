class MonkeytypeCard extends HTMLElement {
  set hass(hass) {
    if (!this._config) return;

    const wpmEntity  = hass.states[this._config.wpm_entity];
    const rankEntity = hass.states[this._config.rank_entity];

    const wpm  = wpmEntity  ? parseFloat(wpmEntity.state)  : null;
    const rank = rankEntity ? parseInt(rankEntity.state, 10) : null;

    const fmtWpm  = (!wpmEntity  || isNaN(wpm))  ? "–" : wpm.toFixed(1);
    const fmtRank = (!rankEntity || isNaN(rank))  ? "–" : `#${rank.toLocaleString()}`;

    this.shadowRoot.querySelector("#wpm-value").textContent  = fmtWpm;
    this.shadowRoot.querySelector("#rank-value").textContent = fmtRank;
  }

  setConfig(config) {
    if (!config.wpm_entity || !config.rank_entity) {
      throw new Error("monkeytype-card: wpm_entity und rank_entity sind Pflichtfelder");
    }
    this._config = config;

    if (!this.shadowRoot) {
      this.attachShadow({ mode: "open" });
    }

    const label = config.label ?? "Monkeytype";

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: var(--primary-font-family, sans-serif);
        }
        .card {
          background: var(--ha-card-background, var(--card-background-color, #fff));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,.15));
          padding: 14px 16px 12px;
          display: flex;
          align-items: center;
          gap: 14px;
          overflow: hidden;
        }
        .icon {
          font-size: 28px;
          line-height: 1;
          flex-shrink: 0;
          color: var(--primary-color, #03a9f4);
          display: flex;
          align-items: center;
        }
        .icon svg {
          width: 32px;
          height: 32px;
          fill: currentColor;
        }
        .body {
          flex: 1;
          min-width: 0;
        }
        .title {
          font-size: 0.72rem;
          font-weight: 600;
          letter-spacing: .04em;
          text-transform: uppercase;
          color: var(--secondary-text-color, #727272);
          margin-bottom: 4px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .stats {
          display: flex;
          align-items: baseline;
          gap: 14px;
          flex-wrap: wrap;
        }
        .stat {
          display: flex;
          align-items: baseline;
          gap: 3px;
          white-space: nowrap;
        }
        .value {
          font-size: 1.6rem;
          font-weight: 700;
          line-height: 1;
          color: var(--primary-text-color, #212121);
        }
        .unit {
          font-size: 0.75rem;
          font-weight: 500;
          color: var(--secondary-text-color, #727272);
        }
        .divider {
          width: 1px;
          height: 1.4rem;
          background: var(--divider-color, #e0e0e0);
          align-self: center;
        }
      </style>
      <div class="card">
        <div class="icon">
          <!-- keyboard SVG (MDI) -->
          <svg viewBox="0 0 24 24">
            <path d="M19,10H17V8H19M19,13H17V11H19M16,10H14V8H16M16,13H14V11H16M16,17H8V15H16M7,10H5V8H7M7,13H5V11H7M20,5H4C2.9,5 2,5.9 2,7V17C2,18.1 2.9,19 4,19H20C21.1,19 22,18.1 22,17V7C22,5.9 21.1,5 20,5M10,10H8V8H10M10,13H8V11H10M13,10H11V8H13M13,13H11V11H13Z"/>
          </svg>
        </div>
        <div class="body">
          <div class="title">${label}</div>
          <div class="stats">
            <div class="stat">
              <span class="value" id="wpm-value">–</span>
              <span class="unit">WPM</span>
            </div>
            <div class="divider"></div>
            <div class="stat">
              <span class="value" id="rank-value">–</span>
              <span class="unit">Rang</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  getCardSize() {
    return 1;
  }
}

customElements.define("monkeytype-card", MonkeytypeCard);
