"use strict";

/* Connected-only controls. Credentials are sent to the same-origin local
 * backend explicitly, never placed in URLs, DOM results or browser storage.
 * User-facing financial arithmetic is computed in the Python core.
 */
(() => {
  const $ = (id) => document.getElementById(id);
  let csrf = null;
  let selected = null;
  let configured = false;
  let selectionVersion = 0;
  let searchVersion = 0;
  const node = (tag, cls, value) => {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (value !== undefined && value !== null) el.textContent = String(value);
    return el;
  };

  function status(id, value) { $(id).textContent = value; }
  function setConfigured(value) {
    configured = Boolean(value);
    // Rotate selection version when credentials/entitlements are changed.
    selectionVersion += 1;
    searchVersion += 1;
    selected = null;
    $("research-select").hidden = true;
    $("connected-output").hidden = true;
    $("company-results").replaceChildren();
    $("search-button").disabled = !configured;
    $("provider-status").textContent = configured ? "Session configured" : "Not configured";
    $("nav-connection-state").textContent = configured ? "Configured" : "Not configured";
    if (!configured) {
    }
  }

  async function post(path, payload) {
    if (!csrf) throw new Error("Local session unavailable. Refresh this page.");
    const response = await fetch(path, {
      method: "POST",
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        "X-InvestIQ-CSRF": csrf
      },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (!response.ok) {
      const code = data && typeof data.code === "string" ? " (" + data.code + ")" : "";
      throw new Error((data.error || "Connected request failed") + code);
    }
    return data;
  }

  function row(label, value) {
    const el = node("div", "connected-detail");
    el.append(node("span", "", label), node("strong", "", value === null ? "Unavailable" : value));
    return el;
  }

  function displayCandidates(data) {
    const container = $("company-results");
    container.replaceChildren();
    selected = null;
    $("research-select").hidden = true;
    $("connected-output").hidden = true;
    const companies = data.companies || [];
    if (!companies.length) {
      status("search-message", "No matching supported candidates. Search another name or ticker.");
      return;
    }
    status("search-message", companies.length + " candidate" + (companies.length === 1 ? "" : "s") +
      " found. Select one, then verify its current listing.");
    for (const company of companies) {
      const button = node("button", "candidate", "");
      button.type = "button";
      button.setAttribute("role", "listitem");
      const primary = node("span", "candidate-primary", company.company);
      const secondary = node("span", "candidate-secondary",
        company.symbol + " · " + company.venue + " · SEC CIK " + company.cik);
      button.append(primary, secondary);
      button.addEventListener("click", () => {
        selectionVersion += 1;
        selected = company;
        for (const choice of container.querySelectorAll("button")) {
          choice.classList.remove("candidate-selected");
        }
        button.classList.add("candidate-selected");
        $("chosen-company").replaceChildren(
          row("Issuer", company.company),
          row("Instrument", company.symbol + " · " + company.venue),
          row("SEC issuer ID", company.cik),
          row("Proposed trading currency", company.currency_candidate),
          row("Directory observation", company.observed_at)
        );
        $("confirm-listing").checked = false;
        $("confirm-currency").checked = false;
        $("research-select").hidden = false;
        $("connected-output").hidden = true;
      });
      container.append(button);
    }
  }

  function displayResearch(data) {
    const container = $("connected-summary");
    container.replaceChildren();
    const quote = data.quote;
    container.append(
      row("Issuer", data.issuer),
      row("Selected instrument", data.symbol + " · " + data.venue),
      row("Candle close price", quote.price + " " + data.currency),
      row("Market event time", quote.market_event_at),
      row("Market session", quote.market_session),
      row("Provider timeliness", quote.timeliness + " (NOT independently verified live)"),
      row("Freshness against selected age policy", quote.freshness),
      row("Price adjustment basis", quote.adjustment),
      row("Quote source", quote.source),
      row("Quote retention permission", quote.snapshot_right),
      row("Annual reported EPS P/E proxy", data.reported_annual_pe_proxy)
    );
    const facts = $("connected-facts");
    facts.replaceChildren();
    for (const fact of data.annual_facts || []) {
      const card = node("article", "connected-fact");
      card.append(
        node("strong", "", fact.metric.replaceAll("_", " ")),
        node("span", "", fact.value + (fact.currency ? " " + fact.currency : "") +
          " · " + fact.unit.replaceAll("_", " ")),
        node("small", "", "Fiscal end " + fact.fiscal_end +
          " · filed " + fact.filing_date + " · SEC accession " + fact.accession),
        node("code", "", fact.source_reference)
      );
      facts.append(card);
    }
    if (!facts.children.length) facts.append(node("p", "", "No supported annual facts were available."));
    const warnings = $("connected-warnings");
    warnings.replaceChildren();
    for (const warning of data.warnings || []) warnings.append(node("li", "", warning));
    $("connected-output").hidden = false;
  }

  async function initialize() {
    try {
      const response = await fetch("/api/v1/session", {
        credentials: "same-origin", cache: "no-store",
        headers: { "X-InvestIQ-Init": "1" }
      });
      if (!response.ok) throw new Error("Could not initialize local session.");
      const session = await response.json();
      csrf = session.csrf;
      setConfigured(session.configured);
      status("setup-message", session.configured ?
        "Provider credentials are configured in server memory." :
        "Configure your own provider credentials to begin connected research.");
    } catch (error) {
      status("setup-message", error.message || "Session initialization failed.");
    }
  }

  $("connection-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = $("setup-button");
    button.disabled = true;
    status("setup-message", "Validating local session configuration…");
    const values = {
      sec_contact: $("sec-contact").value,
      twelve_data_api_key: $("quote-key").value
    };
    try {
      const result = await post("/api/v1/session/configure", values);
      $("quote-key").value = "";
      $("sec-contact").value = "";
      setConfigured(result.configured);
      status("setup-message", "Configured for this server session only. No credentials were persisted.");
    } catch (error) {
      status("setup-message", error.message || "Unable to configure session.");
    } finally {
      values.twelve_data_api_key = "";
      button.disabled = false;
    }
  });

  $("clear-session").addEventListener("click", async () => {
    try {
      await post("/api/v1/session/clear", {});
      setConfigured(false);
      $("quote-key").value = "";
      $("sec-contact").value = "";
      status("setup-message", "Disconnected; session credentials and directory cleared.");
      status("search-message", "Configure a provider session first.");
      status("research-message", "");
    } catch (error) {
      status("setup-message", error.message || "Failed to clear local session.");
    }
  });

  $("search-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!configured) return;
    const button = $("search-button");
    const submittedSearch = ++searchVersion;
    // A search initiated during a prior research call invalidates that result.
    selectionVersion += 1;
    selected = null;
    $("research-select").hidden = true;
    $("connected-output").hidden = true;
    button.disabled = true;
    status("search-message", "Retrieving issuer candidates from SEC (first search may take time)…");
    try {
      const result = await post("/api/v1/companies/search", {
        query: $("company-search").value.trim()
      });
      if (submittedSearch === searchVersion && configured) displayCandidates(result);
    } catch (error) {
      if (submittedSearch === searchVersion) {
        status("search-message", error.message || "Company search failed.");
      }
    } finally {
      button.disabled = !configured;
    }
  });

  $("connected-research-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!selected || !configured) return;
    const button = $("research-button");
    const submittedCandidate = selected;
    const submittedVersion = selectionVersion;
    button.disabled = true;
    $("connected-output").hidden = true;
    status("research-message", "Retrieving SEC annual facts and permitted quote…");
    try {
      const result = await post("/api/v1/research/connected", {
        symbol: submittedCandidate.symbol,
        venue: submittedCandidate.venue,
        cik: submittedCandidate.cik,
        currency: submittedCandidate.currency_candidate,
        confirm_current_listing: $("confirm-listing").checked,
        confirm_currency: $("confirm-currency").checked,
        max_quote_age_minutes: Number($("quote-age").value)
      });
      if (submittedVersion !== selectionVersion || selected !== submittedCandidate || !configured) {
        status("research-message", "Selection changed; the previous research result was discarded.");
        return;
      }
      displayResearch(result);
      status("research-message", "Current sourced results loaded. No data saved and no AI model executed.");
    } catch (error) {
      if (submittedVersion === selectionVersion && selected === submittedCandidate) {
        status("research-message", error.message || "Connected research failed.");
      }
    } finally {
      button.disabled = false;
    }
  });
  initialize();
})();
