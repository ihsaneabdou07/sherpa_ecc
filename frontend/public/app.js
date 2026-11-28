/* Sherpa ECC — interface (front end statique, sans dépendance).
   Données : window.SHERPA_DATA (js/data.js) · Calculs : window.Engine (js/engine.js).
   Assistant : mode autonome par défaut ; backend optionnel via l'URL saisie dans l'onglet Assistant
   (contrat proposé : POST {API}/ask  corps {question, context}  →  réponse {answer}). */
(function () {
  "use strict";
  const D = window.SHERPA_DATA, E = window.Engine;
  const $ = (s, r) => (r || document).querySelector(s);
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = (n, d = 0) => n == null || isNaN(n) ? "—" : Number(n).toLocaleString("fr-FR", { minimumFractionDigits: d, maximumFractionDigits: d });
  const store = { get(k, def) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : def; } catch (e) { return def; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* stockage indisponible */ } } };
  const COL = ["#0f766e", "#b45309", "#2563eb", "#9333ea", "#be123c", "#65a30d", "#0891b2", "#a16207", "#475569", "#db2777", "#4d7c0f", "#7c3aed"];
  const P = Object.assign({}, E.DEFAULTS, store.get("sherpa.params", {}));
  let saved = store.get("sherpa.scenarioA", null);
  const DEC = store.get("sherpa.decision", null) || { w: D.decision.criteres.map(c => c.poids), n: D.decision.criteres.map(c => c.notes.slice()) };
  const persist = () => store.set("sherpa.params", P);
  const prodByName = n => D.produits.find(p => p.nom === n);

  /* ---------- Briques d'interface ---------- */
  function table(cols, rows, opts) {
    opts = opts || {};
    return `<table><thead><tr>${cols.map(c => `<th class="${c.n ? "n" : ""}">${esc(c.label)}</th>`).join("")}</tr></thead><tbody>` +
      rows.map(r => `<tr class="${opts.best && opts.best(r) ? "best" : ""}">${cols.map(c => `<td class="${c.n ? "n" : ""}">${c.html ? c.html(r) : esc(c.fmt ? c.fmt(r[c.k], r) : r[c.k])}</td>`).join("")}</tr>`).join("") + `</tbody></table>`;
  }
  function slider(id, label, min, max, step, val, unit, dec) {
    return `<label for="${id}">${esc(label)} <span class="v" id="${id}_v">${fmt(val, dec || 0)} ${esc(unit || "")}</span></label><input type="range" id="${id}" min="${min}" max="${max}" step="${step}" value="${val}">`;
  }
  function number(id, label, val, step) { return `<label for="${id}">${esc(label)}</label><input type="number" id="${id}" value="${val}" step="${step || "any"}">`; }
  function heat(rowsLbl, colsLbl, matrix, corner, fmtFn, rowFmt) {
    const flat = matrix.flat(), lo = Math.min(...flat), hi = Math.max(...flat);
    const col = v => { const t = hi === lo ? 0 : (v - lo) / (hi - lo); return `hsl(${Math.round(150 - 150 * t)},55%,${34 + 6 * (1 - t)}%)`; };
    return `<table class="heat"><thead><tr><th>${esc(corner)}</th>${colsLbl.map(c => `<th class="n">${esc(fmt(c))}</th>`).join("")}</tr></thead><tbody>` +
      matrix.map((r, i) => `<tr><th>${esc(rowFmt ? rowFmt(rowsLbl[i]) : fmt(rowsLbl[i]))}</th>${r.map(v => `<td style="background:${col(v)};color:#fff">${fmtFn(v)}</td>`).join("")}</tr>`).join("") + `</tbody></table>`;
  }
  function stackBar(parts, total) {
    return `<div class="bar" role="img" aria-label="${esc(parts.map(p => p.l + " " + fmt(p.v)).join(", "))}">${parts.map(p => `<i style="width:${Math.max(0, p.v) / total * 100}%;background:${p.c}" title="${esc(p.l)} : ${fmt(p.v)}"></i>`).join("")}</div>`;
  }
  const legend = items => `<div class="legend">${items.map(i => `<span><s style="background:${i.c}"></s>${esc(i.l)}</span>`).join("")}</div>`;
  function select(id, label, opts, val) { return `<label for="${id}">${esc(label)}</label><select id="${id}">${opts.map(o => `<option value="${esc(o)}"${o === val ? " selected" : ""}>${esc(o)}</option>`).join("")}</select>`; }
  function bindRange(id, key, dec, cb) { const el = $("#" + id); if (!el) return; el.addEventListener("input", () => { P[key] = parseFloat(el.value); $("#" + id + "_v").textContent = fmt(P[key], dec) + " " + (el.dataset.unit || ""); persist(); cb(); }); }
  function bindVal(id, key, cb, num) { const el = $("#" + id); if (!el) return; el.addEventListener("change", () => { P[key] = num === false ? el.value : parseFloat(el.value); persist(); cb(); }); }
  function download(name, text, type) { const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([text], { type: type || "text/csv;charset=utf-8" })); a.download = name; a.click(); setTimeout(() => URL.revokeObjectURL(a.href), 500); }
  const costParts = r => [{ l: "Hydrogène", v: r.h2, c: COL[0] }, { l: "CO2", v: r.co2, c: COL[1] }, { l: "Annuité CAPEX synthèse", v: r.annuity, c: COL[2] }, { l: "Électricité synthèse + N2", v: r.elecSynth, c: COL[3] }];
  const costLegend = legend(costParts({}).map(p => ({ l: p.l, c: p.c })));

  /* ---------- Onglets ---------- */
  const TABS = [["dashboard", "Tableau de bord"], ["sim", "Simulateur de coût"], ["sens", "Sensibilité"], ["capex", "Dimensionnement & CAPEX"], ["decision", "Matrice de décision"], ["hybride", "Hybride PV–éolien"], ["kb", "Base de connaissances"], ["ptx", "Études PtX"], ["assistant", "Assistant"]];
  const rendered = {}, RENDER = {};
  function show(id) {
    TABS.forEach(([t]) => { $("#tab-" + t).hidden = t !== id; const b = $("#btn-" + t); b.setAttribute("aria-selected", t === id); b.tabIndex = t === id ? 0 : -1; });
    RENDER[id](); rendered.cur = id; try { history.replaceState(null, "", "#" + id); } catch (e) { /* ignore */ }
  }
  $("#tabs").innerHTML = TABS.map(([t, l]) => `<button role="tab" id="btn-${t}" aria-controls="tab-${t}" aria-selected="false" type="button">${esc(l)}</button>`).join("");
  $("#tabs").addEventListener("click", e => { const b = e.target.closest("button"); if (b) show(b.id.slice(4)); });
  $("#tabs").addEventListener("keydown", e => { const i = TABS.findIndex(t => t[0] === rendered.cur); if (e.key === "ArrowRight") show(TABS[(i + 1) % TABS.length][0]), $("#btn-" + rendered.cur).focus(); if (e.key === "ArrowLeft") show(TABS[(i + TABS.length - 1) % TABS.length][0]), $("#btn-" + rendered.cur).focus(); });

  /* ---------- Tableau de bord ---------- */
  RENDER.dashboard = function () {
    const a = E.allProducts(D, P), dc = E.decision(D.decision, DEC.w, DEC.n), best = dc.scores.indexOf(Math.max(...dc.scores));
    const cheapest = a.rows.reduce((x, y) => x.total < y.total ? x : y), max = Math.max(...a.rows.map(r => r.total));
    $("#tab-dashboard").innerHTML = `
    <div class="grid g3">
      <div class="card kpi"><b>${fmt(a.L.total, 2)} €/kg</b><span>Coût de l'hydrogène vert (LCOH) · article : 3–6 €/kg</span></div>
      <div class="card kpi"><b>${esc(cheapest.nom)}</b><span>Produit le moins cher : ${fmt(cheapest.total)} €/t (${fmt(cheapest.eurMwh)} €/MWh)</span></div>
      <div class="card kpi"><b>${esc(D.decision.produits[best])}</b><span>1er de la matrice de décision (score ${fmt(dc.scores[best], 1)} / 5)</span></div>
      <div class="card kpi"><b>${fmt(P.price)} €/MWh · ${fmt(P.hours)} h</b><span>Électricité renouvelable et heures de pleine charge (modifiables dans le Simulateur)</span></div>
    </div>
    <div class="grid g2" style="margin-top:1rem">
      <div class="card"><h2>Coût de production par e-fuel (€/t)</h2>${costLegend}
        ${a.rows.map(r => `<div style="margin:.5rem 0"><div class="row" style="justify-content:space-between;margin:0"><b>${esc(r.nom)}</b><span>${fmt(r.total)} €/t · ×${fmt(r.ratioFossil, 1)} le prix fossile</span></div>${stackBar(costParts(r), max)}</div>`).join("")}
        <p class="note">Ne comprend ni stockage, ni transport, ni coûts de financement intercalaires ni EPC détaillé.</p></div>
      <div class="card"><h2>Messages clés de l'article</h2><ul>${D.synthese.slice(0, 9).map(s => `<li><b>${esc(s.theme)}</b> — ${esc(s.message)} ${s.chiffre ? `<em>(${esc(s.chiffre)})</em>` : ""}</li>`).join("")}</ul></div>
    </div>
    <div class="warn">Ce prototype applique les formules des classeurs Sherpa. Les hypothèses marquées [HYP] (prix de l'électricité marocain, heures de charge, WACC, CAPEX Fischer–Tropsch…) sont à valider avant toute décision d'investissement.</div>`;
  };

  /* ---------- Simulateur ---------- */
  RENDER.sim = function () {
    const root = $("#tab-sim");
    if (!root.dataset.ready) {
      root.dataset.ready = 1;
      root.innerHTML = `<div class="side"><div class="card" id="simCtl"><h2>Paramètres</h2>
        ${slider("price", "Prix de l'électricité renouvelable", 10, 90, 1, P.price, "€/MWh")}
        ${slider("hours", "Heures de pleine charge", 2500, 8000, 100, P.hours, "h/an")}
        ${select("tech", "Électrolyse", Object.keys(D.electro), P.tech)}
        ${select("co2src", "Source de CO2", Object.keys(D.co2), P.co2src)}
        ${slider("wacc", "WACC", 0.03, 0.15, 0.005, P.wacc, "", 3)}
        ${slider("life", "Durée de vie", 10, 30, 1, P.life, "ans")}
        <details><summary>Paramètres avancés</summary>
        ${number("fx", "Taux €/USD", P.fx, 0.01)}${number("waterPrice", "Prix de l'eau dessalée (€/m³)", P.waterPrice, 0.1)}
        ${number("util", "Utilisation de la synthèse (0–1)", P.util, 0.01)}${number("opexSynth", "OPEX synthèse (fraction du CAPEX/an)", P.opexSynth, 0.005)}
        ${number("yield", "Rendement matière (0–1)", P.yield, 0.01)}</details>
        <div class="row"><button class="btn" id="saveA" type="button">Mémoriser comme scénario A</button><button class="btn ghost" id="resetP" type="button">Réinitialiser</button><button class="btn ghost" id="csvP" type="button">Exporter CSV</button></div>
        <p class="note">Les valeurs sont enregistrées dans ce navigateur.</p></div>
        <div id="simOut"></div></div>`;
      bindRange("price", "price", 0, calc); bindRange("hours", "hours", 0, calc); bindRange("wacc", "wacc", 3, calc); bindRange("life", "life", 0, calc);
      $("#wacc").dataset.unit = ""; $("#price").dataset.unit = "€/MWh"; $("#hours").dataset.unit = "h/an"; $("#life").dataset.unit = "ans";
      ["tech", "co2src"].forEach(k => bindVal(k, k, calc, false));
      ["fx", "waterPrice", "util", "opexSynth", "yield"].forEach(k => bindVal(k, k, calc));
      $("#saveA").onclick = () => { const a = E.allProducts(D, P); saved = { P: Object.assign({}, P), lcoh: a.L.total, rows: a.rows.map(r => ({ nom: r.nom, total: r.total })) }; store.set("sherpa.scenarioA", saved); calc(); };
      $("#resetP").onclick = () => { Object.assign(P, E.DEFAULTS); persist(); root.dataset.ready = ""; RENDER.sim(); };
      $("#csvP").onclick = () => { const a = E.allProducts(D, P); download("sherpa_resultats.csv", "Produit;Cout_EUR_t;EUR_MWh_PCI;Part_H2;Elec_MWh_t;Efficacite;Eau_m3_t;Ratio_fossile\n" + a.rows.map(r => [r.nom, r.total, r.eurMwh, r.partH2, r.elecMwhT, r.efficiency, r.waterM3, r.ratioFossil].map(v => typeof v === "number" ? v.toFixed(3).replace(".", ",") : v).join(";")).join("\n")); };
    }
    calc();
    function calc() {
      const a = E.allProducts(D, P), L = a.L, min = Math.min(...a.rows.map(r => r.total));
      const delta = (name, v) => { if (!saved) return ""; const s = saved.rows.find(r => r.nom === name); return s ? `<td class="n">${v - s.total >= 0 ? "+" : ""}${fmt(v - s.total)}</td>` : "<td></td>"; };
      $("#simOut").innerHTML = `<div class="card"><h2>Hydrogène vert (LCOH) : ${fmt(L.total, 2)} €/kg</h2>
        ${stackBar([{ l: "Électricité", v: L.elec, c: COL[0] }, { l: "CAPEX + OPEX électrolyseur", v: L.capex, c: COL[1] }, { l: "Eau", v: L.water, c: COL[2] }], L.total)}
        ${legend([{ l: "Électricité " + fmt(L.elec, 2) + " €/kg", c: COL[0] }, { l: "Électrolyseur " + fmt(L.capex, 2) + " €/kg", c: COL[1] }, { l: "Eau " + fmt(L.water, 3) + " €/kg", c: COL[2] }])}
        <p class="note">Consommation système : ${fmt(L.kwhKg, 1)} kWh/kg H2 (article : 45–73) · CAPEX électrolyseur retenu : ${fmt(L.elecCapex)} €/kW · facteur de recouvrement du capital : ${fmt(L.crf, 4)}.
        ${saved ? `<br>Scénario A mémorisé : LCOH ${fmt(saved.lcoh, 2)} €/kg (écart ${fmt(L.total - saved.lcoh, 2)}).` : ""}</p></div>
        <div class="card" style="margin-top:1rem"><h2>Coût de production par produit</h2>${costLegend}
        <table><thead><tr><th>Produit</th><th class="n">Coût (€/t)</th><th class="n">€/MWh PCI</th><th class="n">Part H2</th><th class="n">Élec. (MWh/t)</th><th class="n">Efficacité</th><th class="n">Eau (m³/t)</th><th class="n">× fossile</th><th class="n">Article (€/t)</th>${saved ? '<th class="n">Δ vs A</th>' : ""}</tr></thead><tbody>
        ${a.rows.map(r => { const ar = D.articleCost[r.nom]; return `<tr class="${r.total === min ? "best" : ""}"><td><b>${esc(r.nom)}</b></td><td class="n">${fmt(r.total)}</td><td class="n">${fmt(r.eurMwh)}</td><td class="n">${fmt(r.partH2 * 100)} %</td><td class="n">${fmt(r.elecMwhT, 1)}</td><td class="n">${fmt(r.efficiency * 100)} %</td><td class="n">${fmt(r.waterM3, 1)}</td><td class="n">${fmt(r.ratioFossil, 1)}</td><td class="n">${ar ? (ar[0] === ar[1] ? fmt(ar[0]) : fmt(ar[0]) + "–" + fmt(ar[1])) : "n.d."}</td>${delta(r.nom, r.total)}</tr>`; }).join("")}</tbody></table>
        <p class="note">Efficacité = énergie du carburant / électricité totale (électrolyse + captage + synthèse). Les coûts de l'article proviennent de sources hétérogènes : comparaison indicative.</p></div>`;
    }
  };

  /* ---------- Sensibilité ---------- */
  RENDER.sens = function () {
    const root = $("#tab-sens");
    if (!root.dataset.ready) { root.dataset.ready = 1; root.innerHTML = `<div class="card"><div class="row"><div style="min-width:240px">${select("sensProd", "Produit analysé", D.produits.map(p => p.nom), P.product)}</div></div></div><div id="sensOut"></div>`; $("#sensProd").onchange = e => { P.product = e.target.value; persist(); draw(); }; }
    draw();
    function draw() {
      const prod = prodByName(P.product), prices = [15, 20, 25, 30, 40, 50, 60, 80], hrs = [3000, 4000, 5000, 6000, 7000, 8000], caps = [800, 1200, 1600, 2000, 2500];
      const h1 = E.heatLcoh(D, P, prices, hrs), h2 = E.heatProduct(D, P, prod, prices, caps), tor = E.tornado(D, P, prod);
      const max = Math.max(...tor.map(t => Math.max(Math.abs(t.low), Math.abs(t.high)))) || 1, W = 720, lw = 280, mid = lw + (W - lw) / 2, sc = (W - lw) / 2 / max;
      const svg = `<svg viewBox="0 0 ${W} ${tor.length * 30 + 30}" role="img" aria-label="Diagramme tornado" style="width:100%;max-width:${W}px">` +
        tor.map((t, i) => { const y = 24 + i * 30; return `<text x="${lw - 8}" y="${y + 14}" text-anchor="end" font-size="12">${esc(t.label)}</text><rect x="${mid + Math.min(0, t.low) * sc}" y="${y}" width="${Math.abs(Math.min(0, t.low)) * sc}" height="20" fill="${COL[0]}"><title>${fmt(t.low)} €/t</title></rect><rect x="${mid}" y="${y}" width="${Math.max(0, t.high) * sc}" height="20" fill="${COL[1]}"><title>+${fmt(t.high)} €/t</title></rect><text x="${mid + Math.max(0, t.high) * sc + 4}" y="${y + 14}" font-size="11" class="m">+${fmt(t.high)}</text><text x="${mid + Math.min(0, t.low) * sc - 4}" y="${y + 14}" font-size="11" text-anchor="end" class="m">${fmt(t.low)}</text>`; }).join("") +
        `<line x1="${mid}" x2="${mid}" y1="14" y2="${tor.length * 30 + 20}" stroke="currentColor" opacity=".4"/><text x="${mid}" y="10" text-anchor="middle" font-size="11" class="m">base ${fmt(tor[0].base)} €/t</text></svg>`;
      $("#sensOut").innerHTML = `<div class="grid g2" style="margin-top:1rem">
        <div class="card"><h2>LCOH (€/kg H2) : prix de l'électricité × heures</h2>${heat(prices, hrs, h1, "€/MWh \\ h/an", v => fmt(v, 2))}<p class="note">Technologie ${esc(P.tech)}, WACC ${fmt(P.wacc * 100, 1)} %, durée de vie ${P.life} ans.</p></div>
        <div class="card"><h2>${esc(prod.nom)} (€/t) : prix de l'électricité × CAPEX électrolyseur</h2>${heat(prices, caps, h2, "€/MWh \\ €/kW", v => fmt(v))}<p class="note">Heures de charge : ${fmt(P.hours)} h/an.</p></div></div>
        <div class="card" style="margin-top:1rem"><h2>Tornado : effet de chaque hypothèse sur le coût de ${esc(prod.nom)}</h2>${svg}<p class="note">Vert : baisse du coût ; orange : hausse. Les plages sont celles du registre d'hypothèses Sherpa.</p></div>`;
    }
  };

  /* ---------- Dimensionnement & CAPEX ---------- */
  RENDER.capex = function () {
    const root = $("#tab-capex");
    if (!root.dataset.ready) {
      root.dataset.ready = 1;
      root.innerHTML = `<div class="side"><div class="card"><h2>Projet</h2>
        ${number("tonnage", "Production cible (t/an)", P.tonnage, 1000)}${select("capProd", "Produit détaillé", D.produits.map(p => p.nom), P.product)}
        <label for="horizon">Horizon CAPEX synthèse</label><select id="horizon"><option value="near"${P.horizon === "near" ? " selected" : ""}>Proche terme</option><option value="long"${P.horizon === "long" ? " selected" : ""}>Long terme</option></select>
        ${number("loc", "Facteur de localisation Maroc (1 = niveau article)", P.loc, 0.05)}${number("indirect", "Coûts indirects (fraction du direct)", P.indirect, 0.01)}${number("contingency", "Imprévus (fraction)", P.contingency, 0.01)}
        <details><summary>Énergies renouvelables</summary>${number("pvCapex", "CAPEX PV (€/kW)", P.pvCapex, 10)}${number("windCapex", "CAPEX éolien (€/kW)", P.windCapex, 10)}${number("pvShare", "Part PV (0–1)", P.pvShare, 0.05)}${number("pvCF", "Facteur de charge PV", P.pvCF, 0.01)}${number("windCF", "Facteur de charge éolien", P.windCF, 0.01)}</details>
        <p class="note">Électrolyseur, heures, WACC, CO2 : repris du Simulateur.</p></div><div id="capOut"></div></div>`;
      ["tonnage", "loc", "indirect", "contingency", "pvCapex", "windCapex", "pvShare", "pvCF", "windCF"].forEach(k => bindVal(k, k, draw));
      bindVal("horizon", "horizon", draw, false); $("#capProd").onchange = e => { P.product = e.target.value; persist(); draw(); };
    }
    draw();
    function draw() {
      const rows = D.produits.map(p => E.sizing(D, P, p)), sel = rows.find(r => r.nom === P.product), prod = prodByName(P.product);
      const sizes = [10000, 50000, 100000, 250000, 500000], caps = [500, 800, 1200, 1750, 2200], facs = [0.5, 0.75, 1, 1.25];
      $("#capOut").innerHTML = `<div class="card"><h2>CAPEX pour ${fmt(P.tonnage)} t/an (M€)</h2><table><thead><tr><th>Produit</th><th class="n">Électrolyseur (MW)</th><th class="n">Élec. (GWh/an)</th><th class="n">Eau (m³/an)</th><th class="n">CAPEX électrolyse</th><th class="n">Synthèse</th><th class="n">Captage CO2</th><th class="n">Indirects + imprévus</th><th class="n">TOTAL hors ENR</th><th class="n">par kt/an</th><th class="n">ENR (MW)</th><th class="n">TOTAL + ENR</th><th class="n">Annuité/an</th></tr></thead><tbody>
        ${rows.map(r => `<tr class="${r.nom === P.product ? "best" : ""}"><td><b>${esc(r.nom)}</b></td><td class="n">${fmt(r.mw)}</td><td class="n">${fmt(r.gwh)}</td><td class="n">${fmt(r.water)}</td><td class="n">${fmt(r.cEl)}</td><td class="n">${fmt(r.cSy)}</td><td class="n">${fmt(r.cCo)}</td><td class="n">${fmt(r.ind + r.imp)}</td><td class="n"><b>${fmt(r.total)}</b></td><td class="n">${fmt(r.perKt, 1)}</td><td class="n">${fmt(r.enrMw)}</td><td class="n">${fmt(r.totalEnr)}</td><td class="n">${fmt(r.annuity)}</td></tr>`).join("")}</tbody></table>
        <p class="note">Électricité = électrolyse seule. CAPEX de captage déduit du coût $/t (part capitalistique ${fmt(P.capexShare * 100)} %). CAPEX Fischer–Tropsch [HYP] : non chiffré dans l'article.</p></div>
        <div class="grid g2" style="margin-top:1rem"><div class="card"><h2>Interface pour les autres modules — ${esc(sel.nom)}</h2><table><tbody>
        <tr><td>Hydrogène à produire</td><td class="n">${fmt(sel.h2 / 365, 1)} t/jour</td></tr><tr><td>CO2 à fournir</td><td class="n">${fmt(sel.co2 / 365, 1)} t/jour</td></tr><tr><td>Azote</td><td class="n">${fmt(sel.n2 / 365, 1)} t/jour</td></tr>
        <tr><td>Puissance de l'électrolyseur</td><td class="n">${fmt(sel.mw)} MW</td></tr><tr><td>Charge électrique moyenne</td><td class="n">${fmt(sel.gwh / 8.76, 1)} MW</td></tr><tr><td>Capacité PV + éolien équivalente</td><td class="n">${fmt(sel.enrMw)} MW</td></tr>
        <tr><td>Eau dessalée</td><td class="n">${fmt(sel.water / 365)} m³/jour</td></tr><tr><td>CAPEX total hors / avec ENR</td><td class="n">${fmt(sel.total)} / ${fmt(sel.totalEnr)} M€</td></tr></tbody></table></div>
        <div class="card"><h2>Répartition du CAPEX — ${esc(sel.nom)}</h2>${stackBar([{ l: "Électrolyse", v: sel.cEl, c: COL[0] }, { l: "Synthèse", v: sel.cSy, c: COL[1] }, { l: "Captage CO2", v: sel.cCo, c: COL[2] }, { l: "Indirects", v: sel.ind, c: COL[3] }, { l: "Imprévus", v: sel.imp, c: COL[4] }], sel.total)}
        ${legend([{ l: "Électrolyse " + fmt(sel.cEl), c: COL[0] }, { l: "Synthèse " + fmt(sel.cSy), c: COL[1] }, { l: "Captage CO2 " + fmt(sel.cCo), c: COL[2] }, { l: "Indirects " + fmt(sel.ind), c: COL[3] }, { l: "Imprévus " + fmt(sel.imp), c: COL[4] }])}</div></div>
        <div class="grid g2" style="margin-top:1rem"><div class="card"><h2>CAPEX total (M€) : taille × CAPEX électrolyseur</h2>${heat(sizes, caps, E.gridSizeElec(D, P, prod, sizes, caps), "t/an \\ €/kW", v => fmt(v))}</div>
        <div class="card"><h2>CAPEX total (M€) : taille × facteur de localisation</h2>${heat(sizes, facs, E.gridSizeLoc(D, P, prod, sizes, facs), "t/an \\ facteur", v => fmt(v))}</div></div>`;
    }
  };

  /* ---------- Matrice de décision ---------- */
  RENDER.decision = function () {
    const root = $("#tab-decision"), pr = D.decision.produits;
    root.innerHTML = `<div class="card"><h2>Matrice de décision pondérée (1 défavorable → 5 favorable)</h2><p class="note">Jugement préliminaire Sherpa [HYP] : modifiez les poids et les notes pour un atelier avec les parties prenantes.</p><div id="decTable"></div><div class="row"><button class="btn ghost" id="decReset" type="button">Rétablir les valeurs d'origine</button></div></div><div class="card" style="margin-top:1rem" id="decRes"></div>`;
    const crit = D.decision.criteres;
    $("#decTable").innerHTML = `<table><thead><tr><th>Critère</th><th class="n">Poids</th>${pr.map(p => `<th class="n">${esc(p)}</th>`).join("")}<th>Justification</th></tr></thead><tbody>
      ${crit.map((c, i) => `<tr><td>${esc(c.critere)}</td><td><input type="number" aria-label="Poids ${esc(c.critere)}" data-w="${i}" value="${DEC.w[i]}" step="0.05" min="0" max="1" style="width:5rem"></td>${pr.map((p, j) => `<td><input type="number" aria-label="Note ${esc(p)} ${esc(c.critere)}" data-n="${i},${j}" value="${DEC.n[i][j]}" min="1" max="5" step="1" style="width:4rem"></td>`).join("")}<td class="note">${esc(c.justif)}</td></tr>`).join("")}</tbody></table>`;
    const upd = () => {
      store.set("sherpa.decision", DEC);
      const d = E.decision(D.decision, DEC.w, DEC.n), a = E.allProducts(D, P), order = d.scores.map((s, j) => j).sort((x, y) => d.scores[y] - d.scores[x]);
      $("#decRes").innerHTML = `<h2>Classement</h2>${Math.abs(d.sumW - 1) > 0.001 ? `<div class="warn">La somme des poids est ${fmt(d.sumW * 100)} % (elle devrait être 100 %) : les scores sont normalisés.</div>` : ""}
      ${order.map((j, k) => `<div class="row" style="margin:.3rem 0"><b style="width:1.5rem">${k + 1}</b><span style="width:8rem">${esc(pr[j])}</span><div class="bar" style="flex:1;min-width:160px"><i style="width:${d.scores[j] / 5 * 100}%;background:${COL[k === 0 ? 0 : 8]}"></i></div><span style="width:4rem;text-align:right"><b>${fmt(d.scores[j], 2)}</b></span><span class="note" style="width:9rem;text-align:right">${fmt(a.rows[j].total)} €/t</span></div>`).join("")}`;
    };
    root.addEventListener("input", e => { const t = e.target; if (t.dataset.w != null) DEC.w[+t.dataset.w] = parseFloat(t.value) || 0; if (t.dataset.n) { const [i, j] = t.dataset.n.split(",").map(Number); DEC.n[i][j] = Math.min(5, Math.max(1, parseFloat(t.value) || 1)); } upd(); });
    $("#decReset").onclick = () => { DEC.w = crit.map(c => c.poids); DEC.n = crit.map(c => c.notes.slice()); store.set("sherpa.decision", DEC); RENDER.decision(); };
    upd();
  };

  /* ---------- Hybride PV-éolien (Dakhla) ---------- */
  RENDER.hybride = function () {
    const H = D.hybride, root = $("#tab-hybride"), get = n => (H.parametres.find(p => p.param.startsWith(n)) || {}).valeur;
    root.innerHTML = `<div class="grid g2"><div class="card"><h2>Répartition de la charge selon la fraction PV f</h2>
      <label for="hQ">Demande journalière Qd <span class="v" id="hQ_v">10 kWh/j</span></label><input type="range" id="hQ" min="1" max="10" step="0.5" value="10">
      <label for="hF">Fraction PV f <span class="v" id="hF_v">0,1</span></label><input type="range" id="hF" min="0" max="1" step="0.1" value="0.1">
      <div id="hOut"></div><div id="hChart"></div>${legend([{ l: "Part PV", c: COL[1] }, { l: "Part éolienne", c: COL[0] }])}
      <p class="note">Équations (3)–(4) de l'article : S_pv·e_pv = f·Qd et S_e·e_e = (1−f)·Qd. Les surfaces nécessitent les énergies spécifiques mensuelles e_pv et e_e, qui ne sont pas publiées sous forme de tableau.</p></div>
      <div class="card"><h2>Résultats publiés (Dakhla, ${esc(get("Demande journalière"))} kWh/j)</h2>${table([{ k: "scenario", label: "Scénario" }, { k: "config", label: "Configuration" }, { k: "f", label: "f", n: 1 }, { k: "cout", label: "Coût (DH)", n: 1, fmt: v => v == null ? "non indiqué" : fmt(v) }], H.resultats)}
      <p class="note">Le mois le plus défavorable (décembre) renchérit le meilleur système hybride de ${fmt(H.resultats[3].cout - H.resultats[1].cout)} DH, soit +${fmt((H.resultats[3].cout / H.resultats[1].cout - 1) * 100)} %.</p>
      <h3>Coûts d'équipements publiés (2004)</h3>${table([{ k: "comp", label: "Composant" }, { k: "cout", label: "Coût", n: 1, fmt: fmt }, { k: "unite", label: "Unité" }], H.couts)}
      <div class="warn">Coûts de 2004 en DH, périmètre capital uniquement (câbles et accessoires exclus) : à utiliser comme repère de méthode, pas comme prix actuels.</div></div></div>
      <div class="card" style="margin-top:1rem"><h2>Paramètres et hypothèses de l'étude</h2>${table([{ k: "param", label: "Paramètre" }, { k: "valeur", label: "Valeur" }, { k: "unite", label: "Unité" }, { k: "remarque", label: "Remarque" }], H.parametres)}</div>`;
    const draw = () => {
      const Q = parseFloat($("#hQ").value), f = parseFloat($("#hF").value);
      $("#hQ_v").textContent = fmt(Q, 1) + " kWh/j"; $("#hF_v").textContent = fmt(f, 1);
      $("#hOut").innerHTML = `<p><b>PV :</b> ${fmt(f * Q, 2)} kWh/j · <b>Éolien :</b> ${fmt((1 - f) * Q, 2)} kWh/j</p>`;
      $("#hChart").innerHTML = `<svg viewBox="0 0 440 120" style="width:100%" role="img" aria-label="Répartition PV et éolien">${H.balayage.map((r, i) => { const x = 10 + i * 39, h1 = r.pv * 90, h2 = r.eol * 90, on = Math.abs(r.f - f) < 1e-9; return `<g opacity="${on ? 1 : .55}"><rect x="${x}" y="${100 - h2}" width="30" height="${h2}" fill="${COL[0]}"/><rect x="${x}" y="${100 - h2 - h1}" width="30" height="${h1}" fill="${COL[1]}"/><text x="${x + 15}" y="114" font-size="10" text-anchor="middle" class="m">${fmt(r.f, 1)}</text></g>`; }).join("")}</svg>`;
    };
    $("#hQ").oninput = draw; $("#hF").oninput = draw; draw();
  };

  /* ---------- Base de connaissances ---------- */
  const KB = {
    projets: ["Projets e-fuels (35)", () => D.projets, [{ k: "n", label: "#" }, { k: "projet", label: "Projet" }, { k: "pays", label: "Pays" }, { k: "efuel", label: "E-fuel" }, { k: "enr", label: "ENR" }, { k: "cap", label: "kt/an", n: 1, fmt: v => fmt(v, 1) }, { k: "trlMin", label: "TRL", html: r => esc(r.trlMin === r.trlMax ? r.trlMin : r.trlMin + "–" + r.trlMax) }, { k: "financement", label: "Financement" }, { k: "dev", label: "Développeurs" }], ["efuel", "pays"]],
    pays: ["Prix de l'électricité par pays", () => D.paysLcoe, [{ k: "pays", label: "Pays" }, { k: "source", label: "Source d'électricité" }, { k: "min", label: "Min (€/MWh)", n: 1 }, { k: "max", label: "Max (€/MWh)", n: 1 }, { k: "co2", label: "Source CO2" }, { k: "voieH2", label: "Voie H2" }]],
    politiques: ["Politiques et réglementation", () => D.politiques, [{ k: "region", label: "Région" }, { k: "cat", label: "Catégorie" }, { k: "instrument", label: "Instrument" }, { k: "detail", label: "Détail" }, { k: "chiffre", label: "Chiffre clé" }, { k: "pertinence", label: "Pertinence e-fuels / Maroc" }], ["region", "cat"]],
    barrieres: ["Barrières et risques", () => D.barrieres, [{ k: "cat", label: "Catégorie" }, { k: "barriere", label: "Barrière / risque" }, { k: "gravite", label: "Gravité" }, { k: "mitigation", label: "Atténuation" }, { k: "statut", label: "Statut" }], ["cat", "gravite"]],
    maroc: ["Contexte Maroc [HYP]", () => D.maroc, [{ k: "theme", label: "Thème" }, { k: "element", label: "Élément" }, { k: "confiance", label: "Confiance" }, { k: "valider", label: "Où valider" }], ["theme", "confiance"]],
    opp: ["Pistes d'innovation", () => D.opportunites, [{ k: "id", label: "ID" }, { k: "idee", label: "Idée" }, { k: "valeur", label: "Valeur" }, { k: "risqueTech", label: "Risque tech." }, { k: "risqueMarche", label: "Risque marché" }, { k: "next", label: "Prochaine étape" }], ["valeur"]],
    hyp: ["Registre des hypothèses", () => D.hypotheses, [{ k: "id", label: "ID" }, { k: "hyp", label: "Hypothèse" }, { k: "valeur", label: "Valeur" }, { k: "unite", label: "Unité" }, { k: "plage", label: "Plage plausible" }, { k: "impact", label: "Impact" }, { k: "valider", label: "À valider par" }], ["impact"]],
    alertes: ["Alertes qualité des données", () => D.alertes, [{ k: "sujet", label: "Sujet" }, { k: "alerte", label: "Alerte" }, { k: "gravite", label: "Gravité" }], ["gravite"]],
    voies: ["Voies et procédés", () => D.voies, [{ k: "voie", label: "Voie" }, { k: "etape", label: "Étape" }, { k: "equation", label: "Équation" }, { k: "T", label: "T (°C)" }, { k: "P", label: "P (bar)" }, { k: "catalyseurs", label: "Catalyseurs" }, { k: "produits", label: "Produits" }]],
    fiches: ["Fiches produits", () => D.produitsFiches, [{ k: "produit", label: "Produit" }, { k: "voie", label: "Voie" }, { k: "usage", label: "Usage" }, { k: "compat", label: "Compatibilité" }, { k: "coutTxt", label: "Coût (article)" }, { k: "capexNear", label: "CAPEX proche terme" }, { k: "capexLong", label: "CAPEX long terme" }]],
    synthese: ["Messages clés", () => D.synthese, [{ k: "theme", label: "Thème" }, { k: "message", label: "Message" }, { k: "chiffre", label: "Chiffre clé" }, { k: "source", label: "Source" }], ["theme"]]
  };
  let kbCur = "projets";
  RENDER.kb = function () {
    const root = $("#tab-kb");
    root.innerHTML = `<div class="chips" id="kbNav">${Object.entries(KB).map(([k, v]) => `<button type="button" data-k="${k}" aria-pressed="${k === kbCur}">${esc(v[0])}</button>`).join("")}</div><div class="card"><div class="row" id="kbFilters"></div><div id="kbTable"></div><p class="note" id="kbCount"></p></div>`;
    $("#kbNav").onclick = e => { const b = e.target.closest("button"); if (b) { kbCur = b.dataset.k; RENDER.kb(); } };
    const [title, rows, cols, filt] = KB[kbCur], all = rows();
    $("#kbFilters").innerHTML = `<div style="flex:1;min-width:200px"><input type="search" id="kbQ" placeholder="Rechercher dans « ${esc(title)} »" aria-label="Recherche"></div>` + (filt || []).map(f => `<div><select data-f="${f}" aria-label="Filtre ${esc(f)}"><option value="">${esc(cols.find(c => c.k === f).label)} : tous</option>${[...new Set(all.map(r => r[f]))].filter(v => v != null).sort().map(v => `<option>${esc(v)}</option>`).join("")}</select></div>`).join("") + (kbCur === "projets" ? `<button class="btn ghost small" id="kbCsv" type="button">Exporter CSV</button>` : "");
    const draw = () => {
      const q = $("#kbQ").value.toLowerCase(), fs = [...root.querySelectorAll("select[data-f]")].filter(s => s.value);
      const out = all.filter(r => (!q || Object.values(r).join(" ").toLowerCase().includes(q)) && fs.every(s => String(r[s.dataset.f]) === s.value));
      let extra = "";
      if (kbCur === "pays") { const mx = Math.max(...out.map(r => r.max)) || 1; extra = `<div style="margin:.6rem 0">${out.map(r => `<div class="row" style="margin:.2rem 0"><span style="width:8rem">${esc(r.pays)}</span><div style="flex:1;position:relative;height:1rem;background:var(--line);border-radius:3px"><i style="position:absolute;left:${r.min / mx * 100}%;width:${(r.max - r.min) / mx * 100}%;height:100%;background:${r.pays.startsWith("Maroc") ? COL[1] : COL[0]};border-radius:3px"></i></div><span class="note" style="width:5rem">${fmt(r.min)}–${fmt(r.max)}</span></div>`).join("")}</div>`; }
      $("#kbTable").innerHTML = extra + table(cols, out); $("#kbCount").textContent = out.length + " ligne(s) sur " + all.length + ".";
      const b = $("#kbCsv"); if (b) b.onclick = () => download("projets_efuels.csv", cols.map(c => c.label).join(";") + "\n" + out.map(r => cols.map(c => '"' + String(r[c.k] == null ? "" : r[c.k]).replace(/"/g, '""') + '"').join(";")).join("\n"));
    };
    root.addEventListener("input", draw); root.addEventListener("change", draw); draw();
  };

  /* ---------- Études PtX ---------- */
  RENDER.ptx = function () {
    const root = $("#tab-ptx"), dec = D.rreh.decomposition, names = Object.keys(dec), mx = Math.max(...names.map(n => dec[n].reduce((a, x) => a + x[1], 0)));
    const compCol = {}; let ci = 0; names.forEach(n => dec[n].forEach(([c]) => { if (!(c in compCol)) compCol[c] = COL[ci++ % COL.length]; }));
    root.innerHTML = `<div class="card"><h2>Coût par vecteur énergétique — hub renouvelable distant (arXiv 2507.07681, estimation 2030)</h2>
      ${names.map(n => { const tot = dec[n].reduce((a, x) => a + x[1], 0); return `<div style="margin:.6rem 0"><div class="row" style="justify-content:space-between;margin:0"><b>${esc(n)}</b><span>${fmt(tot, 1)} €/MWh</span></div><div class="bar" style="width:${tot / mx * 100}%">${dec[n].map(([c, v]) => `<i style="width:${v / tot * 100}%;background:${compCol[c]}" title="${esc(c)} : ${fmt(v, 1)}"></i>`).join("")}</div></div>`; }).join("")}
      ${legend(Object.entries(compCol).slice(0, 14).map(([l, c]) => ({ l, c })))}<p class="note">Survolez un segment pour lire le poste de coût. Contributions lues sur la Figure 3 de l'article (écart à la légende ≤ 0,6 €/MWh).</p></div>
      <div class="grid g2" style="margin-top:1rem"><div class="card"><h2>Résultats du modèle</h2><div style="max-height:360px;overflow:auto">${table([{ k: 0, label: "Indicateur" }, { k: 1, label: "Vecteur" }, { k: 3, label: "Valeur", n: 1, fmt: v => fmt(v, 2) }, { k: 4, label: "Unité" }], D.rreh.resultats)}</div></div>
      <div class="card"><h2>Liquéfaction de l'hydrogène — cycles J-B en cascade (revue Cryo 2025)</h2><div style="max-height:360px;overflow:auto">${table([{ k: 0, label: "Réf." }, { k: 1, label: "Pré-refroidissement" }, { k: 4, label: "SEC (kWh/kg)", n: 1, fmt: v => v == null ? "—" : fmt(v, 2) }, { k: 5, label: "EXE (%)", n: 1, fmt: v => v == null ? "—" : fmt(v, 1) }, { k: 6, label: "t/j", n: 1, fmt: v => v == null ? "—" : fmt(v, 1) }], D.cryo)}</div><p class="note">Études par simulation. Minimum théorique : 2,7 kWh/kg ; moyenne des usines actuelles ≈ 10 kWh/kg.</p></div></div>
      <div class="card" style="margin-top:1rem"><h2>Paramètres technico-économiques PtX (PTX Business Opportunity Analyser v1.0)</h2><div class="row"><input type="search" id="pQ" placeholder="Rechercher (ex. PEM, DAC, ammoniac, CAPEX…)" aria-label="Recherche" style="flex:1;min-width:220px"><select id="pCat" style="max-width:260px" aria-label="Catégorie"><option value="">Toutes les catégories</option>${[...new Set(D.ptx.map(r => r[0]))].map(c => `<option>${esc(c)}</option>`).join("")}</select></div><div id="pTab" style="max-height:480px;overflow:auto"></div><p class="note" id="pCount"></p></div>`;
    const draw = () => {
      const q = $("#pQ").value.toLowerCase(), c = $("#pCat").value, out = D.ptx.filter(r => (!c || r[0] === c) && (!q || r.join(" ").toLowerCase().includes(q)));
      $("#pTab").innerHTML = table([{ k: 0, label: "Catégorie" }, { k: 1, label: "Technologie" }, { k: 2, label: "Paramètre" }, { k: 3, label: "Scénario" }, { k: 4, label: "Année" }, { k: 5, label: "Valeur", n: 1, fmt: v => fmt(v, 3) }, { k: 6, label: "Max", n: 1, fmt: v => v == null ? "" : fmt(v, 3) }, { k: 7, label: "Unité" }, { k: 8, label: "Table" }, { k: 9, label: "Page", n: 1 }], out.slice(0, 300));
      $("#pCount").textContent = out.length + " ligne(s)" + (out.length > 300 ? " (300 premières affichées : affinez la recherche)" : "") + ". Sources primaires dans les classeurs Excel du dépôt.";
    };
    $("#pQ").oninput = draw; $("#pCat").onchange = draw; draw();
  };

  /* ---------- Assistant ---------- */
  const norm = s => String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  const STOP = new Set("le la les un une des de du et en au aux pour sur dans que qui est quel quelle quels quelles ce ces par avec a il elle on se sa son ses ou mais plus comment combien quoi donne moi".split(" "));
  const tok = s => norm(s).split(/[^a-z0-9]+/).filter(w => w.length > 2 && !STOP.has(w));
  let DOCS = null;
  function docs() {
    if (DOCS) return DOCS;
    DOCS = [];
    D.synthese.forEach(s => DOCS.push({ t: s.theme, x: s.message + " " + (s.chiffre || ""), s: s.source }));
    D.hypotheses.forEach(h => DOCS.push({ t: "Hypothèse " + h.id + " : " + h.hyp, x: `Valeur ${h.valeur == null ? "n.d." : h.valeur} ${h.unite}, plage ${h.plage}. ${h.justif} Impact ${h.impact}. À valider par ${h.valider}.`, s: "Registre des hypothèses" }));
    D.barrieres.forEach(b => DOCS.push({ t: "Risque " + b.cat + " : " + b.barriere, x: `Gravité ${b.gravite}. Atténuation : ${b.mitigation}`, s: b.ref }));
    D.maroc.forEach(m => DOCS.push({ t: "Maroc — " + m.theme, x: m.element + " (confiance " + m.confiance + "). Valider : " + m.valider, s: "Contexte Maroc [HYP]" }));
    D.opportunites.forEach(o => DOCS.push({ t: "Piste " + o.id + " : " + o.idee, x: `${o.justif}. Valeur ${o.valeur}, risque technique ${o.risqueTech}, risque marché ${o.risqueMarche}. Prochaine étape : ${o.next}`, s: "Opportunités d'innovation" }));
    D.alertes.forEach(a => DOCS.push({ t: "Alerte " + a.sujet, x: a.alerte + " (gravité " + a.gravite + ")", s: "Alertes qualité" }));
    D.politiques.forEach(p => DOCS.push({ t: p.region + " — " + p.instrument, x: `${p.detail || ""} ${p.chiffre || ""}. ${p.pertinence || ""}`, s: p.source || "Politiques" }));
    D.projets.forEach(p => DOCS.push({ t: "Projet " + p.projet + " (" + p.pays + ")", x: `${p.efuel}, ${p.enr}, ${p.cap} kt/an, TRL ${p.trlMin}-${p.trlMax}, ${p.financement}`, s: "Table 5 " + p.ref }));
    D.produitsFiches.forEach(p => DOCS.push({ t: "Produit " + p.produit, x: `${p.voie}. ${p.usage}. ${p.compat}. ${p.coutTxt}`, s: "Fiches produits" }));
    D.voies.forEach(v => DOCS.push({ t: v.voie + " — " + v.etape, x: `${v.equation}, T ${v.T} °C, P ${v.P} bar, catalyseurs ${v.catalyseurs}`, s: "Voies et procédés" }));
    DOCS.forEach(d => { d.k = new Set(tok(d.t + " " + d.x)); d.tk = new Set(tok(d.t)); });
    return DOCS;
  }
  const ALIAS = [["e-methanol", /methanol/], ["e-DME", /\bdme\b/], ["e-kerosene", /kerosene|jet|aviation/], ["e-diesel", /diesel/], ["e-gasoline", /essence|gasoline/], ["e-ammonia", /ammoniac|ammonia|\bnh3\b/]];
  function localAnswer(q) {
    const n = norm(q), a = E.allProducts(D, P), prodHit = ALIAS.find(([, re]) => re.test(n)), dc = E.decision(D.decision, DEC.w, DEC.n);
    if (/classement|meilleur|recommand|prioris|quel.*(produit|e-fuel)/.test(n) && !prodHit) {
      const o = dc.scores.map((s, j) => j).sort((x, y) => dc.scores[y] - dc.scores[x]);
      return "Classement de la matrice de décision (poids et notes actuels) :\n" + o.map((j, k) => `${k + 1}. ${D.decision.produits[j]} — score ${fmt(dc.scores[j], 2)}/5, coût ${fmt(a.rows[j].total)} €/t`).join("\n") + "\nNotes = jugement préliminaire Sherpa [HYP], à confronter lors d'un atelier.";
    }
    if (prodHit && /cout|prix|combien|lcoe|production|capex|invest/.test(n)) {
      const r = a.rows.find(x => x.nom === prodHit[0]), s = E.sizing(D, P, prodByName(prodHit[0]));
      return `${r.nom} (prix élec. ${P.price} €/MWh, ${fmt(P.hours)} h/an, ${P.tech}, WACC ${fmt(P.wacc * 100, 1)} %) :\n• Coût de production : ${fmt(r.total)} €/t (${fmt(r.eurMwh)} €/MWh PCI), soit ×${fmt(r.ratioFossil, 1)} le prix fossile indicatif.\n• Hydrogène = ${fmt(r.partH2 * 100)} % du coût ; efficacité électricité→carburant ${fmt(r.efficiency * 100)} %.\n• Pour ${fmt(P.tonnage)} t/an : électrolyseur ${fmt(s.mw)} MW, CAPEX ${fmt(s.total)} M€ hors ENR (${fmt(s.totalEnr)} M€ avec ENR).`;
    }
    if (/lcoh|hydrogene/.test(n) && /cout|prix|combien|lcoh/.test(n)) return `LCOH actuel : ${fmt(a.L.total, 2)} €/kg H2 (électricité ${fmt(a.L.elec, 2)}, électrolyseur ${fmt(a.L.capex, 2)}, eau ${fmt(a.L.water, 3)}). Fourchette de l'article : 3–6 €/kg.`;
    const qt = tok(q), sc = docs().map(d => ({ d, s: qt.reduce((x, w) => x + (d.k.has(w) ? 1 : 0) + (d.tk.has(w) ? 1.5 : 0), 0) })).filter(x => x.s > 0).sort((x, y) => y.s - x.s).slice(0, 3);
    if (!sc.length) return "Je n'ai rien trouvé de précis dans la base. Essayez avec un produit (ex. « coût de l'e-méthanol »), « classement », « risques », « hypothèses » ou « CAPEX ».";
    return sc.map(x => `• ${x.d.t} — ${x.d.x.trim()} [${x.d.s}]`).join("\n\n");
  }
  async function ask(q) {
    const api = store.get("sherpa.api", "");
    if (api) {
      const a = E.allProducts(D, P), ctrl = new AbortController(), to = setTimeout(() => ctrl.abort(), 15000);
      try {
        const res = await fetch(api.replace(/\/$/, "") + "/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q, context: { params: P, lcoh: a.L.total, produits: a.rows.map(r => ({ nom: r.nom, cout_eur_t: r.total })) } }), signal: ctrl.signal });
        if (!res.ok) throw new Error("HTTP " + res.status);
        const ct = res.headers.get("content-type") || "", j = ct.includes("json") ? await res.json() : { answer: await res.text() };
        setApi(true); return String(j.answer || j.response || j.reply || JSON.stringify(j));
      } catch (e) { setApi(false); return localAnswer(q) + "\n\n(API indisponible : " + e.message + " — réponse locale.)"; } finally { clearTimeout(to); }
    }
    return localAnswer(q);
  }
  function setApi(on) { const p = $("#apiStatus"); p.textContent = on ? "API connectée" : "Mode autonome"; p.classList.toggle("on", on); }
  RENDER.assistant = function () {
    const root = $("#tab-assistant");
    if (!root.dataset.ready) {
      root.dataset.ready = 1;
      root.innerHTML = `<div class="grid g2" style="grid-template-columns:2fr 1fr"><div class="card"><h2>Assistant</h2><div class="chips" id="sugg">${["Quel e-fuel est le mieux classé ?", "Coût de l'e-méthanol", "Coût de l'e-ammoniac", "Quels sont les principaux risques ?", "Quelle hypothèse a le plus d'impact ?", "Projets e-fuels en Europe"].map(s => `<button type="button">${esc(s)}</button>`).join("")}</div>
        <div class="chat" id="chat" aria-live="polite"><div class="msg a">Bonjour. Je réponds à partir de la base Sherpa et de vos paramètres actuels (simulateur, matrice de décision).</div></div>
        <form id="chatForm" class="row"><input type="text" id="chatIn" placeholder="Posez une question…" aria-label="Question" style="flex:1;min-width:200px" autocomplete="off"><button class="btn" type="submit">Envoyer</button></form></div>
        <div class="card"><h3>Connexion au backend (optionnel)</h3><label for="apiUrl">URL de l'API</label><input type="text" id="apiUrl" placeholder="http://localhost:8000" value="${esc(store.get("sherpa.api", ""))}"><div class="row"><button class="btn small" id="apiSave" type="button">Enregistrer</button></div>
        <p class="note">Sans URL, l'assistant répond localement. Avec une URL : <code>POST {URL}/ask</code>, corps <code>{question, context}</code>, réponse <code>{answer}</code>. Adapter à <code>src/ai_assistant.py</code> si le contrat diffère.</p></div></div>`;
      const add = (c, t) => { const d = document.createElement("div"); d.className = "msg " + c; d.textContent = t; $("#chat").appendChild(d); $("#chat").scrollTop = 1e9; return d; };
      const go = async q => { if (!q.trim()) return; add("u", q); const w = add("a", "…"); w.textContent = await ask(q); };
      $("#chatForm").onsubmit = e => { e.preventDefault(); const v = $("#chatIn").value; $("#chatIn").value = ""; go(v); };
      $("#sugg").onclick = e => { if (e.target.tagName === "BUTTON") go(e.target.textContent); };
      $("#apiSave").onclick = () => { store.set("sherpa.api", $("#apiUrl").value.trim()); setApi(false); };
    }
  };

  /* ---------- Démarrage ---------- */
  $("#themeBtn").onclick = () => { const r = document.documentElement, cur = r.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"); r.dataset.theme = cur === "dark" ? "light" : "dark"; store.set("sherpa.theme", r.dataset.theme); };
  $("#printBtn").onclick = () => window.print();
  const th = store.get("sherpa.theme", null); if (th) document.documentElement.dataset.theme = th;
  const start = (location.hash || "").slice(1);
  show(TABS.some(t => t[0] === start) ? start : "dashboard");
})();
