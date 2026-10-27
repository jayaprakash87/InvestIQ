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
  let quoteConfigured = false;
  let modelConfigured = false;
  let aiGeneration = 0;
  let scenarioGeneration = 0;
  let questionHistory = [];
  let selectionVersion = 0;
  let evidenceVersion = 0;
  let searchVersion = 0;
  const node = (tag, cls, value) => {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (value !== undefined && value !== null) el.textContent = String(value);
    return el;
  };

  function status(id, value) { $(id).textContent = value; }
  function setConfigured(value, quotes = false) {
    configured = Boolean(value);
    quoteConfigured = Boolean(quotes);
    // Rotate selection version when credentials/entitlements are changed.
    selectionVersion += 1;
    evidenceVersion += 1;
    searchVersion += 1;
    selected = null;
    document.dispatchEvent(new Event("investiq:issuer-cleared"));
    $("research-select").hidden = true;
    $("connected-output").hidden = true;
    $("filing-evidence-panel").hidden = true;
    $("filing-result").hidden = true;
    $("company-results").replaceChildren();
    $("search-button").disabled = !configured;
    $("research-button").disabled = !quoteConfigured;
    $("ai-run-button").disabled = !configured || !modelConfigured;
    $("provider-status").textContent = configured ? "Session configured" : "Not configured";
    $("nav-connection-state").textContent = configured ? "Configured" : "Not configured";
    if (!configured) setModelConfigured(false);
    aiGeneration += 1;
    $("ai-result").hidden = true;
    resetInteractions();
  }

  function setModelConfigured(value, model) {
    modelConfigured = Boolean(value);
    $("nav-model-state").textContent = modelConfigured ? "Configured" : "Not configured";
    $("ai-run-button").disabled = !modelConfigured || !configured;
    if (model) $("model-select").value = model;
    aiGeneration += 1;
    $("ai-result").hidden = true;
    resetQuestionHistory();
  }

  function resetQuestionHistory() {
    questionHistory = [];
    $("ai-question-list").replaceChildren();
    $("ai-question-history").hidden = true;
    $("ai-followup-suggestions").replaceChildren();
  }

  function resetInteractions() {
    scenarioGeneration += 1;
    $("scenario-workbench").hidden = true;
    $("scenario-results").hidden = true;
    resetQuestionHistory();
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
    $("filing-evidence-panel").hidden = true;
    $("filing-result").hidden = true;
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
        evidenceVersion += 1;
        selected = company;
        document.dispatchEvent(new CustomEvent("investiq:issuer-selected", {
          detail: { symbol: company.symbol, venue: company.venue,
            cik: company.cik, currency: company.currency_candidate, company: company.company }
        }));
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
        $("research-button").disabled = !quoteConfigured;
        $("filing-evidence-panel").hidden = false;
        $("filing-result").hidden = true;
        status("filing-message", "Confirm the listing and USD currency, then choose a topic.");
        $("connected-output").hidden = true;
        aiGeneration += 1;
        $("ai-result").hidden = true;
        resetInteractions();
        $("scenario-workbench").hidden = false;
        status("scenario-message", "Enter manually verified hypothetical EPS and price; no live data is used.");
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
      setConfigured(session.configured, session.quote_configured);
      setModelConfigured(session.model_configured, session.model_name);
      document.dispatchEvent(new CustomEvent("investiq:session-ready", {
        detail: { csrf, privateHistoryEnabled: session.private_history_enabled === true }
      }));
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
      setConfigured(result.configured, result.quote_configured);
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
      setConfigured(false, false);
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
    evidenceVersion += 1;
    aiGeneration += 1;
    $("ai-result").hidden = true;
    resetInteractions();
    selected = null;
    document.dispatchEvent(new Event("investiq:issuer-cleared"));
    $("confirm-listing").checked = false;
    $("confirm-currency").checked = false;
    $("research-select").hidden = true;
    $("connected-output").hidden = true;
    $("filing-evidence-panel").hidden = true;
    $("filing-result").hidden = true;
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
    if (!selected || !configured || !quoteConfigured) {
      status("research-message", "An authorized Twelve Data key is required for quotes.");
      return;
    }
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
  function showFiling(result) {
    const filing = result.document;
    const source = $("filing-source");
    source.replaceChildren();
    source.append(node("p", "filing-metadata",
      "SEC Form " + filing.form + " · Filed " + filing.filed_on +
      " · Accession " + filing.accession +
      " · Extracted-text digest " + filing.document_sha256.slice(0, 16) + "…"));
    if (typeof filing.source_url === "string" &&
        /^https:\/\/www\.sec\.gov\/Archives\/edgar\/data\/[0-9]+\/[0-9]+\/[A-Za-z0-9_.-]+$/.test(filing.source_url)) {
      const link = node("a", "secondary-link", "Open primary filing on SEC.gov");
      link.href = filing.source_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      source.append(link);
    }
    const excerpts = $("filing-excerpts");
    excerpts.replaceChildren();
    if (!result.passages.length) excerpts.append(node("p", "empty-state",
      "No sufficiently long keyword-matching passages were extracted. " +
      "This does not mean the filing lacks this information."));
    for (const p of result.passages) {
      const article = node("article", "filing-excerpt");
      article.append(
        node("p", "filing-excerpt-text", p.excerpt),
        node("p", "filing-excerpt-ref", "Extracted-text offsets " +
          p.extracted_start + "–" + p.extracted_end),
        node("code", "reference-chip", p.evidence_id));
      excerpts.append(article);
    }
    const limitations = $("filing-limitations");
    limitations.replaceChildren();
    for (const warning of result.limitations) limitations.append(node("li", "", warning));
    $("filing-result").hidden = false;
  }

  for (const button of document.querySelectorAll(".filing-topic")) {
    button.addEventListener("click", async () => {
      if (!configured || !selected) return;
      if (!$("confirm-listing").checked || !$("confirm-currency").checked) {
        status("filing-message", "Confirm the listing and USD currency first.");
        return;
      }
      const candidate = selected;
      const generation = selectionVersion;
      const topicRequest = ++evidenceVersion;
      button.disabled = true;
      $("filing-result").hidden = true;
      status("filing-message", "Retrieving the selected SEC filing and excerpts…");
      try {
        const result = await post("/api/v1/research/filing-evidence", {
          symbol: candidate.symbol, venue: candidate.venue, cik: candidate.cik,
          currency: candidate.currency_candidate,
          confirm_current_listing: $("confirm-listing").checked,
          confirm_currency: $("confirm-currency").checked,
          topic: button.dataset.topic
        });
        if (generation !== selectionVersion || topicRequest !== evidenceVersion ||
            selected !== candidate || !configured ||
            !$("confirm-listing").checked || !$("confirm-currency").checked) {
          status("filing-message", "Selection changed; previous excerpts discarded.");
          return;
        }
        showFiling(result);
        status("filing-message", "Retrieved source excerpts; no AI analysis was performed.");
      } catch (error) {
        if (generation === selectionVersion && topicRequest === evidenceVersion &&
            selected === candidate && configured) {
          status("filing-message", error.message || "Filing evidence unavailable.");
        }
      } finally {
        button.disabled = false;
      }
    });
  }

  function validatedSecLink(url) {
    if (typeof url !== "string") return null;
    if (!/^https:\/\/(www|data)\.sec\.gov\/(Archives\/edgar\/data\/|api\/xbrl\/companyfacts\/)/.test(url)) {
      return null;
    }
    return url;
  }

  function citedClaim(claim, records, className) {
    const result = node("article", className);
    result.append(node("p", "ai-claim-text", claim.claim));
    const citations = node("div", "ai-citations");
    for (const id of claim.evidence_ids) {
      const ref = records[id];
      if (!ref) continue;
      const box = node("div", "ai-source");
      box.append(node("code", "reference-chip", id));
      if (ref.type === "filing_passage") {
        box.append(node("p", "ai-source-detail", ref.excerpt));
      } else {
        box.append(node("p", "ai-source-detail",
          ref.metric + ": " + ref.value + " " + ref.currency +
          " · fiscal end " + ref.fiscal_end));
      }
      const url = validatedSecLink(ref.source_url);
      if (url) {
        const link = node("a", "secondary-link", "Inspect SEC source");
        link.href = url;
        link.rel = "noopener noreferrer";
        link.target = "_blank";
        box.append(link);
      }
      citations.append(box);
    }
    if (!claim.evidence_ids.length) {
      citations.append(node("span", "unattributed",
        "Counter-thesis hypothesis; no directly supporting supplied source."));
    }
    result.append(citations);
    return result;
  }

  function showAiResearch(payload) {
    if (payload.mode !== "ai_assisted_sec_limited_not_verified" ||
        payload.model_executed !== true || !payload.analysis ||
        !payload.source_records) {
      throw new Error("Unsupported AI research response");
    }
    $("ai-overview").textContent = payload.analysis.overview;
    const findings = $("ai-findings");
    findings.replaceChildren();
    for (const finding of payload.analysis.findings) {
      findings.append(citedClaim(finding, payload.source_records, "ai-claim"));
    }
    $("ai-bear").replaceChildren(
      citedClaim(payload.analysis.bear_case, payload.source_records, "ai-claim")
    );
    $("ai-questions").replaceChildren();
    for (const q of payload.analysis.open_questions) {
      $("ai-questions").append(node("li", "", q));
    }
    $("ai-disclosures").replaceChildren();
    for (const limitation of payload.disclosures) {
      $("ai-disclosures").append(node("li", "", limitation));
    }
    const hints = $("ai-followup-suggestions");
    hints.replaceChildren();
    for (const q of payload.analysis.open_questions) {
      const button = node("button", "secondary-button followup-question", q);
      button.type = "button";
      button.addEventListener("click", () => {
        $("ai-question").value = q.slice(0, 360);
        $("ai-consent").checked = false;
        aiGeneration += 1;
        $("ai-question").focus();
        status("ai-message", "Question filled. Review it and authorize another independent request.");
      });
      hints.append(button);
    }
    $("ai-result").hidden = false;
  }

  $("model-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = $("model-setup-button");
    button.disabled = true;
    status("model-message", "Validating model key locally; no provider call…");
    const payload = {
      model_api_key: $("model-key").value,
      model: $("model-select").value
    };
    try {
      const result = await post("/api/v1/model/configure", payload);
      setModelConfigured(result.model_configured, result.model_name);
      $("model-key").value = "";
      status("model-message", "Model key configured in local session memory. It has not been tested.");
    } catch (error) {
      status("model-message", error.message || "Model configuration rejected.");
    } finally {
      payload.model_api_key = "";
      button.disabled = false;
    }
  });

  $("model-clear-button").addEventListener("click", async () => {
    try {
      await post("/api/v1/model/clear", {});
      setModelConfigured(false);
      $("model-key").value = "";
      status("model-message", "Model credential cleared from the local session.");
    } catch (error) {
      status("model-message", error.message || "Could not clear model session.");
    }
  });

  $("ai-research-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!selected || !configured || !modelConfigured) {
      status("ai-message", "Configure SEC discovery and a model, then select a company.");
      return;
    }
    if (!$("confirm-listing").checked || !$("confirm-currency").checked ||
        !$("ai-consent").checked) {
      status("ai-message", "Confirm the issuer, currency and external model consent.");
      return;
    }
    const candidate = selected;
    const selection = selectionVersion;
    const generation = ++aiGeneration;
    const submittedQuestion = $("ai-question").value;
    const submit = $("ai-run-button");
    submit.disabled = true;
    $("ai-result").hidden = true;
    status("ai-message", "Reading SEC evidence; one permitted model call follows…");
    try {
      const response = await post("/api/v1/research/ai", {
        symbol: candidate.symbol, venue: candidate.venue, cik: candidate.cik,
        currency: candidate.currency_candidate,
        confirm_current_listing: $("confirm-listing").checked,
        confirm_currency: $("confirm-currency").checked,
        consent_external_sec_data: $("ai-consent").checked,
        question: submittedQuestion
      });
      if (generation !== aiGeneration || selection !== selectionVersion ||
          selected !== candidate || !modelConfigured ||
          !$("confirm-listing").checked || !$("confirm-currency").checked ||
          !$("ai-consent").checked) {
        status("ai-message", "Company, consent or model changed; discarded previous analysis.");
        return;
      }
      showAiResearch(response);
      questionHistory.push(submittedQuestion);
      questionHistory = questionHistory.slice(-5);
      $("ai-question-list").replaceChildren(
        ...questionHistory.map(q => node("li", "", q))
      );
      $("ai-question-history").hidden = false;
      status("ai-message",
        "Model response complete. Every citation identifies an input source, not verified truth.");
    } catch (error) {
      if (generation === aiGeneration && selection === selectionVersion) {
        status("ai-message", error.message || "AI research failed.");
      }
    } finally {
      // Consent is per request, not an ongoing or blanket authorization.
      $("ai-consent").checked = false;
      submit.disabled = !modelConfigured || !configured;
    }
  });

  // A changed confirmation invalidates visible, previously qualified outputs.
  for (const id of ["confirm-listing", "confirm-currency"]) {
    $(id).addEventListener("change", () => {
      scenarioGeneration += 1;
      aiGeneration += 1;
      evidenceVersion += 1;
      $("scenario-results").hidden = true;
      $("ai-result").hidden = true;
      $("filing-result").hidden = true;
      status("scenario-message", "Listing/currency confirmation changed; recalculate if appropriate.");
    });
  }
  $("ai-question").addEventListener("input", () => {
    aiGeneration += 1;
    $("ai-result").hidden = true;
  });
  $("ai-consent").addEventListener("change", () => {
    if (!$("ai-consent").checked) {
      aiGeneration += 1;
      $("ai-result").hidden = true;
    }
  });

  // The scenario workbench has no LLM or licensed provider dependency.
  // An edit invalidates the previously displayed scenario and pending response.
  $("scenario-form").addEventListener("input", () => {
    scenarioGeneration += 1;
    $("scenario-results").hidden = true;
    document.dispatchEvent(new Event("investiq:scenario-invalidated"));
    status("scenario-message", "Assumptions changed. Recalculate to view new outcomes.");
  });

  function assumption(name, field) {
    const value = Number($("scenario-" + name + "-" + field).value);
    if (!Number.isFinite(value)) throw new Error("Enter finite scenario assumptions.");
    return value;
  }

  function inputNumber(id) {
    const field = $(id);
    if (!field.value.trim() || !field.checkValidity()) {
      throw new Error("Complete each input using the supported numeric range.");
    }
    const value = Number(field.value);
    if (!Number.isFinite(value)) throw new Error("Use a finite numeric input.");
    return value;
  }

  function manualScenarioInputs() {
    return {
      start_eps: inputNumber("scenario-eps"),
      initial_price: inputNumber("scenario-price"),
      years: inputNumber("scenario-years"),
      scenarios: ["bear", "base", "bull"].map(name => ({
        name,
        annual_growth_percent: assumption(name, "growth"),
        terminal_pe: assumption(name, "pe"),
        weight_percent: assumption(name, "weight")
      }))
    };
  }

  function percentage(value) {
    return Number(value).toLocaleString("en-US", { maximumFractionDigits: 2 }) + "%";
  }

  function amount(value) {
    return Number(value).toLocaleString("en-US", {
      minimumFractionDigits: 2, maximumFractionDigits: 2
    }) + " USD";
  }

  function renderHypothetical(data) {
    if (data.mode !== "manual_hypothetical_no_provider_data" ||
        !Array.isArray(data.outcomes) || data.outcomes.length !== 3) {
      throw new Error("The scenario response did not match the supported contract.");
    }
    const summary = $("scenario-result-summary");
    summary.replaceChildren(
      row("Weighted terminal price (subjective)", amount(data.weighted_terminal_price)),
      row("Price-only cumulative return", percentage(data.weighted_price_return_percent)),
      row("Annualized return on weighted price", percentage(data.annualized_return_on_weighted_price_percent))
    );
    const results = $("scenario-result-cases");
    results.replaceChildren();
    for (const outcome of data.outcomes) {
      const card = node("article", "scenario-case");
      card.append(
        node("strong", "scenario-case-title", outcome.name.toUpperCase()),
        row("Subjective weight", percentage(outcome.weight_percent)),
        row("Hypothetical terminal price", amount(outcome.terminal_price)),
        row("Total price return", percentage(outcome.total_price_return_percent)),
        row("Annualized price return", percentage(outcome.annualized_price_return_percent))
      );
      results.append(card);
    }
    $("scenario-input-hash").textContent =
      "Deterministic input fingerprint: " + data.input_sha256 +
      " · Not stored. An input fingerprint is not historical replay.";
    const limitations = $("scenario-disclosures");
    limitations.replaceChildren();
    for (const warning of data.disclosures) {
      limitations.append(node("li", "", warning));
    }
    $("scenario-results").hidden = false;
  }

  $("scenario-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!selected || !configured ||
        !$("confirm-listing").checked || !$("confirm-currency").checked) {
      status("scenario-message", "Select a company and confirm its listing and currency first.");
      return;
    }
    const candidate = selected;
    const selection = selectionVersion;
    const generation = ++scenarioGeneration;
    const button = $("scenario-run");
    button.disabled = true;
    $("scenario-results").hidden = true;
    try {
      const inputs = manualScenarioInputs();
      const weightTotal = inputs.scenarios.reduce((sum, x) => sum + x.weight_percent, 0);
      if (Math.abs(weightTotal - 100) > 1e-9) {
        throw new Error("Subjective bear/base/bull weights must total 100%.");
      }
      status("scenario-message", "Calculating using the deterministic Python core…");
      const result = await post("/api/v1/research/scenarios", {
        symbol: candidate.symbol, venue: candidate.venue, cik: candidate.cik,
        currency: candidate.currency_candidate,
        confirm_current_listing: $("confirm-listing").checked,
        confirm_currency: $("confirm-currency").checked,
        hypothetical: inputs
      });
      if (generation !== scenarioGeneration || selection !== selectionVersion ||
          selected !== candidate || !configured ||
          !$("confirm-listing").checked || !$("confirm-currency").checked) {
        status("scenario-message", "Inputs or company changed; outdated calculation discarded.");
        return;
      }
      renderHypothetical(result);
      document.dispatchEvent(new CustomEvent("investiq:scenario-calculated", {
        detail: { inputs: result.inputs }
      }));
      status("scenario-message", "Hypothetical outcomes recalculated; no data was saved.");
    } catch (error) {
      if (generation === scenarioGeneration && selection === selectionVersion) {
        status("scenario-message", error.message || "Invalid hypothetical scenario.");
      }
    } finally {
      button.disabled = false;
    }
  });

  initialize();
})();
