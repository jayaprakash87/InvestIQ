"use strict";

// Render all backend-origin text with textContent, never HTML interpolation.
// Only the existing Python financial core computes scenario valuations.
(function () {
  const byId = (id) => document.getElementById(id);
  const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
  const percent = new Intl.NumberFormat("en-US", {
    style: "percent",
    maximumFractionDigits: 1
  });

  function node(tag, className, value) {
    const result = document.createElement(tag);
    if (className) result.className = className;
    if (value !== undefined && value !== null) result.textContent = String(value);
    return result;
  }

  function dateLabel(value) {
    if (!value) return "Date unavailable";
    const d = new Date(value);
    return Number.isNaN(d.getTime())
      ? "Unverified timestamp"
      : d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric", timeZone: "UTC" });
  }

  function labeledValue(label, value) {
    const row = node("div", "detail-row");
    row.append(node("span", "detail-label", label), node("strong", "detail-value", value));
    return row;
  }

  function renderFindings(report) {
    const container = byId("finding-list");
    container.replaceChildren();
    for (const [i, finding] of report.findings.entries()) {
      const item = node("article", "finding");
      const head = node("div", "finding-head");
      head.append(node("span", "finding-number", String(i + 1).padStart(2, "0")));
      const pill = node("span", "finding-kind kind-" + finding.kind, finding.kind.replaceAll("_", " "));
      head.append(pill);
      item.append(head, node("p", "finding-text", finding.text));
      const references = (finding.evidence_ids || []).concat(finding.assumption_ids || []);
      if (references.length) {
        item.append(node("div", "reference-label", "LINKED INPUTS"));
        for (const reference of references) {
          const ref = node("code", "reference-chip", reference);
          item.append(ref);
        }
      } else {
        item.append(node("span", "unattributed", "No numeric evidence asserted"));
      }
      container.append(item);
    }
    if (report.questions.length) {
      byId("followup").replaceChildren(
        node("strong", "", "Open research question"),
        node("p", "", report.questions.join(" "))
      );
      byId("followup").hidden = false;
    }
    byId("findings-empty").hidden = true;
    container.hidden = false;
  }

  function renderScenarios(payload) {
    const result = payload.validation.scenario_analysis;
    const container = byId("scenario-list");
    container.replaceChildren();
    const years = payload.bundle.valuation.years;
    const initialPrice = payload.bundle.valuation.hypothetical_entry_price;
    const header = node("div", "scenario-parameters");
    header.append(
      labeledValue("Fictional entry price", number.format(initialPrice) + " USD"),
      labeledValue("Assumed holding period", years + " years")
    );
    container.append(header);
    const maxPrice = Math.max(...result.outcomes.map((x) => x.terminal_price), 0.01);
    for (const outcome of result.outcomes) {
      const item = node("div", "scenario");
      const head = node("div", "scenario-head");
      head.append(node("strong", "scenario-name", outcome.name));
      head.append(node("span", "scenario-price", number.format(outcome.terminal_price) + " USD"));
      const barBg = node("div", "bar-bg");
      const bar = node("div", "bar-fill " + outcome.name.toLowerCase().replace(/[^a-z]/g, ""));
      bar.style.width = Math.min(100, Math.max(0, outcome.terminal_price / maxPrice * 100)) + "%";
      barBg.append(bar);
      const detail = node("div", "scenario-detail");
      detail.append(
        node("span", "", "Subjective weight: " + percent.format(outcome.probability)),
        node("span", outcome.annualized_price_return < 0 ? "negative-return" : "positive-return",
          percent.format(outcome.annualized_price_return) + " annualized*")
      );
      item.append(head, barBg, detail);
      container.append(item);
    }
    const total = node("div", "expected-total");
    total.append(
      node("span", "", "Weighted terminal value"),
      node("strong", "", number.format(result.expected_terminal_price) + " USD")
    );
    container.append(total);
    byId("scenario-note").textContent = "* " + payload.validation.disclaimer;
    byId("scenario-note").hidden = false;
    byId("scenarios-empty").hidden = true;
    container.hidden = false;
  }

  function renderEvidence(evidence) {
    const container = byId("evidence-list");
    container.replaceChildren();
    for (const item of evidence) {
      const card = node("article", "evidence-item");
      const metric = node("div", "evidence-head");
      metric.append(
        node("strong", "evidence-name", item.metric.replaceAll("_", " ")),
        node("span", "source-badge", item.kind)
      );
      card.append(metric);
      card.append(node("div", "evidence-value", number.format(Number(item.value)) +
        (item.currency ? " " + item.currency : "")));
      card.append(labeledValue("Value unit", item.unit.replaceAll("_", " ")));
      card.append(labeledValue("Economic period", dateLabel(item.effective_at)));
      card.append(labeledValue("Publisher", item.source.publisher));
      card.append(labeledValue("Published (fictional)", dateLabel(item.source.published_at)));
      card.append(node("code", "source-id", item.observation_id));
      container.append(card);
    }
    byId("evidence-empty").hidden = true;
    container.hidden = false;
  }

  function renderThesis(history) {
    const container = byId("thesis-list");
    container.replaceChildren();
    for (const thesis of history) {
      const article = node("article", "thesis-item");
      const bubble = node("div", "revision-bubble", thesis.revision);
      const body = node("div", "thesis-body");
      const meta = node("div", "thesis-meta");
      meta.append(
        node("span", "thesis-stage", thesis.stage.replaceAll("_", " ")),
        node("span", "thesis-date", dateLabel(thesis.as_of))
      );
      body.append(meta, node("p", "thesis-statement", thesis.statement));
      body.append(node("div", "thesis-reason", thesis.revision_reason));
      if (thesis.risks.length) {
        body.append(node("div", "reference-label", "RECORDED RISKS"));
        const list = node("ul", "risk-list");
        for (const risk of thesis.risks) list.append(node("li", "", risk));
        body.append(list);
      }
      article.append(bubble, body);
      container.append(article);
    }
    byId("thesis-empty").hidden = true;
    container.hidden = false;
  }

  function renderResponse(payload) {
    if (payload.mode !== "synthetic" || payload.connected !== false ||
        payload.model_executed !== false || !payload.bundle.synthetic ||
        payload.validation.validation !== "structural_only") {
      throw new Error("Unexpected demo contract; data was not displayed.");
    }
    byId("metric-findings").textContent = number.format(payload.validation.finding_count);
    byId("metric-evidence").textContent = number.format(payload.validation.evidence_count);
    byId("metric-scenarios").textContent =
      number.format(payload.validation.scenario_analysis.outcomes.length);
    byId("metric-thesis").textContent = number.format(payload.validation.thesis_revision_count);
    renderFindings(payload.bundle.report);
    renderScenarios(payload);
    renderEvidence(payload.bundle.evidence);
    renderThesis(payload.bundle.thesis_history);
  }

  async function runDemo() {
    const button = byId("run-demo");
    const state = byId("run-state");
    button.disabled = true;
    state.textContent = "Validating the fictional research bundle…";
    try {
      const response = await fetch("/api/v1/demo", { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) throw new Error("Preview service returned HTTP " + response.status);
      const payload = await response.json();
      renderResponse(payload);
      state.textContent = "Synthetic research loaded and structurally validated. No model or provider was called.";
      button.textContent = "Run synthetic research again";
    } catch (error) {
      state.textContent = "Could not load the demonstration. " + (error instanceof Error ? error.message : "Unknown error");
    } finally {
      button.disabled = false;
    }
  }

  byId("run-demo").addEventListener("click", runDemo);
  for (const link of document.querySelectorAll(".nav-link")) {
    link.addEventListener("click", () => {
      for (const nav of document.querySelectorAll(".nav-link")) {
        nav.classList.remove("active");
        nav.removeAttribute("aria-current");
      }
      link.classList.add("active");
      link.setAttribute("aria-current", "page");
    });
  }
})();
