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
  let issuer = null;
  let hypothetical = null;
  let opened = null;
  let generation = 0;

  function message(text) { $("history-message").textContent = text; }
  function saveMessage(text) { $("decision-message").textContent = text; }
  function enableSaving() {
    $("decision-save").disabled = !enabled || !issuer;
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
    $("history-status").textContent = enabled ? "Local private store enabled" : "Saving disabled";
    $("decision-save-panel").hidden = !enabled;
    $("decision-list-panel").hidden = !enabled;
    enableSaving();
    if (enabled) {
      refreshHistory();
    } else {
      message("History is disabled. Restart with --research-dir to opt in.");
    }
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
      detailRow("Quote retained", "No"),
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
    if (!enabled) return;
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
  $("history-refresh").addEventListener("click", refreshHistory);

})();
