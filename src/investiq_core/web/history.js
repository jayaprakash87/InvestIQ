"use strict";

/* Explicit, opt-in, private research history UI.
 * Uses only authored content and safely validated hypothetical assumptions.
 * Never reads live quotes, SEC documents or model answer DOM.
 */
(() => {
  const $ = id => document.getElementById(id);
  const make = (tag, className, text) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined && text !== null) el.textContent = String(text);
    return el;
  };
  let csrf = null;
  let enabled = false;
  let unlocked = false;
  let issuer = null;
  let hypothetical = null;
  let opened = null;
  let generation = 0;

  function message(text) { $("history-message").textContent = text; }
  function saveMessage(text) { $("decision-message").textContent = text; }
  function enableSaving() {
    $("decision-save").disabled = !enabled || !unlocked || !issuer;
    $("decision-selected-issuer").textContent = issuer
      ? "Selected " + issuer.company + " · " + issuer.symbol + " / " + issuer.venue +
        ". Confirm the current listing and currency before saving."
      : "Select and confirm an issuer to create or revise a decision.";
  }
  async function post(path, data) {
    if (!csrf) throw new Error("Local browser session is unavailable.");
    const response = await fetch(path, {
      method: "POST", credentials: "same-origin", cache: "no-store",
      headers: { "Content-Type": "application/json", "X-InvestIQ-CSRF": csrf },
      body: JSON.stringify(data)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Private history request rejected.");
    return result;
  }

  document.addEventListener("investiq:session-ready", event => {
    csrf = event.detail.csrf;
    enabled = event.detail.privateHistoryEnabled === true;
    unlocked = event.detail.privateHistoryUnlocked === true;
    $("history-status").textContent = !enabled ? "Saving disabled"
      : unlocked ? "History unlocked" : "History locked";
    $("history-unlock-form").hidden = !enabled || unlocked;
    $("decision-save-panel").hidden = !unlocked;
    $("decision-list-panel").hidden = !unlocked;
    enableSaving();
    if (enabled && unlocked) {
      refreshHistory();
    } else if (enabled) {
      message("Private history requires the one-time code printed in your launch terminal.");
    } else {
      message("History is disabled. Restart with --research-dir to opt in.");
    }
  });
  document.addEventListener("investiq:session-disconnected", () => {
    // The server revokes access on disconnect; also hide any opened local text.
    unlocked = false;
    opened = null;
    generation += 1;
    $("history-list").replaceChildren();
    $("history-open-details").replaceChildren();
    $("history-warnings").replaceChildren();
    $("history-open").hidden = true;
    $("decision-save-panel").hidden = true;
    $("decision-list-panel").hidden = true;
    $("history-unlock-form").hidden = !enabled;
    $("history-unlock-code").value = "";
    $("history-status").textContent = enabled ? "History locked" : "Saving disabled";
    message("Private history locked after disconnect. Enter the launch code again.");
    enableSaving();
  });
  document.addEventListener("investiq:issuer-selected", event => {
    issuer = event.detail;
    hypothetical = null;
    $("decision-include-scenarios").checked = false;
    enableSaving();
  });
  document.addEventListener("investiq:issuer-cleared", () => {
    issuer = null;
    hypothetical = null;
    $("decision-include-scenarios").checked = false;
    enableSaving();
  });
  document.addEventListener("investiq:scenario-calculated", event => {
    hypothetical = event.detail.inputs;
  });
  document.addEventListener("investiq:scenario-invalidated", () => {
    hypothetical = null;
    $("decision-include-scenarios").checked = false;
  });

  function lines(id) {
    return $(id).value.split("\n").map(x => x.trim()).filter(Boolean);
  }
  function detailRow(label, value) {
    const row = make("div", "connected-detail");
    row.append(make("span", "", label), make("strong", "", value));
    return row;
  }

  function renderOpen(record) {
    const area = $("history-open-details");
    area.replaceChildren(
      detailRow("Thesis / revision", record.thesis_id + " · " + record.revision),
      detailRow("Instrument", record.symbol + " / " + record.venue + " / " + record.currency),
      detailRow("SEC issuer", record.issuer_cik),
      detailRow("Stage", record.stage),
      detailRow("Recorded", record.saved_at),
      detailRow("Snapshot SHA-256", record.digest_sha256),
      detailRow("Previous thesis SHA-256", record.parent_digest || "First revision"),
      detailRow("AI response retained", "No"),
      detailRow("Quote retained", record.quote_retained ? "Yes — qualified prior snapshot" : "No"),
      detailRow("Annual SEC facts retained", String(record.annual_facts_retained)),
      detailRow("Offline numeric replay eligible", record.replay_numerical_price_analysis ? "Yes" : "No"),
      detailRow("Hypothetical parameters retained",
        record.scenario_assumptions_retained ? "Growth, P/E, weights, years only" : "No")
    );
    for (const [title, text] of [
      ["Author's thesis", record.statement],
      ["Why this revision", record.reason],
      ["Risks", record.risks.join("; ") || "Not entered"],
      ["Invalidation triggers", record.invalidation_triggers.join("; ") || "Not entered"]
    ]) {
      const block = make("div", "history-note");
      block.append(make("strong", "", title), make("p", "", text));
      area.append(block);
    }
    $("history-warnings").replaceChildren(
      ...(record.replay_warnings || []).map(x => make("li", "", x))
    );
    $("history-open-title").textContent =
      record.thesis_id + " · Revision " + record.revision;
    $("history-open").hidden = false;
  }

  async function openRevision(thesisId, revision) {
    const version = ++generation;
    $("history-open").hidden = true;
    message("Reading saved decision offline…");
    try {
      const record = await post("/api/v1/decisions/open", {
        thesis_id: thesisId, revision
      });
      if (version !== generation) return;
      opened = record;
      renderOpen(record);
      message("Immutable decision reopened and replayed offline. No provider requests.");
    } catch (error) {
      if (version === generation) message(error.message);
    }
  }

  async function refreshHistory() {
    if (!enabled || !unlocked) return;
    const version = ++generation;
    message("Reading existing private decision revisions…");
    try {
      const response = await post("/api/v1/decisions/list", {});
      if (version !== generation) return;
      const list = $("history-list");
      list.replaceChildren();
      for (const item of response.snapshots) {
        const button = make("button", "candidate history-entry");
        button.type = "button";
        button.append(
          make("strong", "", item.symbol + " · " + item.thesis_id),
          make("span", "candidate-secondary",
            "Revision " + item.revision + " · " + item.stage + " · " + item.saved_at)
        );
        button.addEventListener("click", () => openRevision(item.thesis_id, item.revision));
        list.append(button);
      }
      if (!response.snapshots.length) {
        list.append(make("p", "empty-state", "No saved decisions yet."));
      }
      message(response.snapshots.length + " private revision(s) listed without provider calls.");
    } catch (error) {
      if (version === generation) message(error.message);
    }
  }
  $("history-unlock-form").addEventListener("submit", async event => {
    event.preventDefault();
    if (!enabled || unlocked) return;
    const field = $("history-unlock-code");
    const code = field.value;
    field.value = "";
    $("history-unlock-message").textContent = "Checking the one-time access code…";
    try {
      const result = await post("/api/v1/decisions/unlock", { code });
      if (result.private_history_unlocked !== true) {
        throw new Error("Private history authorization was rejected.");
      }
      unlocked = true;
      $("history-status").textContent = "History unlocked";
      $("history-unlock-form").hidden = true;
      $("decision-save-panel").hidden = false;
      $("decision-list-panel").hidden = false;
      enableSaving();
      await refreshHistory();
      $("history-unlock-message").textContent = "Private history unlocked for this session.";
    } catch (error) {
      $("history-unlock-message").textContent =
        error.message || "Private history unlock failed.";
    }
  });

  $("history-refresh").addEventListener("click", refreshHistory);

  $("decision-form").addEventListener("submit", async event => {
    event.preventDefault();
    if (!enabled || !unlocked || !issuer || !$("confirm-listing").checked ||
        !$("confirm-currency").checked || !$("decision-consent").checked) {
      saveMessage("Select and confirm the issuer, then explicitly authorize local saving.");
      return;
    }
    if ($("decision-include-scenarios").checked && !hypothetical) {
      saveMessage("First recalculate valid hypothetical inputs in the scenario workbench.");
      return;
    }
    const selected = issuer;
    const button = $("decision-save");
    button.disabled = true;
    saveMessage("Recording a new, immutable local revision…");
    try {
      const record = await post("/api/v1/decisions/save", {
        symbol: selected.symbol, venue: selected.venue, cik: selected.cik,
        currency: selected.currency,
        confirm_current_listing: $("confirm-listing").checked,
        confirm_currency: $("confirm-currency").checked,
        approve_private_save: $("decision-consent").checked,
        decision: {
          thesis_id: $("decision-id").value.trim(),
          statement: $("decision-statement").value,
          reason: $("decision-reason").value,
          stage: $("decision-stage").value,
          risks: lines("decision-risks"),
          invalidation_triggers: lines("decision-triggers"),
          hypothetical: $("decision-include-scenarios").checked ? hypothetical : null
        }
      });
      saveMessage("Revision " + record.revision +
        " saved locally. No licensed quote, AI output or EPS amount stored.");
      await refreshHistory();
    } catch (error) {
      saveMessage(error.message || "Unable to record a private decision.");
    } finally {
      $("decision-consent").checked = false;
      enableSaving();
    }
  });

  $("history-revise").addEventListener("click", () => {
    if (!opened) return;
    $("decision-id").value = opened.thesis_id;
    $("decision-statement").value = opened.statement;
    $("decision-stage").value = opened.stage;
    $("decision-reason").value = "";
    $("decision-risks").value = opened.risks.join("\n");
    $("decision-triggers").value = opened.invalidation_triggers.join("\n");
    $("decision-include-scenarios").checked = false;
    $("decision-consent").checked = false;
    saveMessage("Draft prepared from revision " + opened.revision +
      ". Reconfirm the SAME issuer and write a fresh reason before saving.");
    $("decision-reason").focus();
  });

  async function exportPrivate(format) {
    if (!opened || !enabled || !unlocked) return;
    try {
      const result = await post("/api/v1/decisions/export", {
        thesis_id: opened.thesis_id, revision: opened.revision, format
      });
      const mime = format === "json" ? "application/json" : "text/markdown";
      const blob = new Blob([result.content], { type: mime + ";charset=utf-8" });
      const temporaryUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = temporaryUrl;
      anchor.download = result.filename;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(temporaryUrl), 1000);
      message("Private file exported. Review its content before sharing.");
    } catch (error) {
      message(error.message || "Private export failed.");
    }
  }
  $("history-export-json").addEventListener("click", () => exportPrivate("json"));
  $("history-export-md").addEventListener("click", () => exportPrivate("markdown"));

})();
