/* Moteur de calcul e-fuels — reprend fidèlement les formules des classeurs
   efuels_maroc_base_donnees.xlsx (Calculateur_LCOE) et capex_data.xlsx (Dimensionnement).
   Aucune dépendance : fonctionne dans le navigateur et sous Node (tests). */
(function (root) {
  const M = { H2: 2.016, CO2: 44.01, N2: 28.014, MeOH: 32.04, DME: 46.07, NH3: 17.031, CH2: 14.027 };
  const DEFAULTS = {
    price: 30, hours: 5000, tech: "PEM", co2src: "Point source", wacc: 0.08, life: 20, fx: 0.92,
    waterPrice: 2, waterStoich: 8.92, waterOver: 0.25, rhoH2: 0.08988, util: 0.9, opexSynth: 0.04,
    yield: 0.95, n2Elec: 0.11, horizon: "near", loc: 1, indirect: 0.2, contingency: 0.15, capexShare: 0.6,
    pvCapex: 650, windCapex: 1300, pvShare: 0.5, pvCF: 0.3, windCF: 0.45, tonnage: 100000, product: "e-methanol"
  };
  const crf = (w, n) => (w === 0 ? 1 / n : (w * Math.pow(1 + w, n)) / (Math.pow(1 + w, n) - 1));
  const avg = (a, b) => (a + b) / 2;

  function stoich(name, y) {
    switch (name) {
      case "e-methanol": return { h2: 3 * M.H2 / M.MeOH / y, co2: M.CO2 / M.MeOH / y, n2: 0 };
      case "e-DME": return { h2: 6 * M.H2 / M.DME / y, co2: 2 * M.CO2 / M.DME / y, n2: 0 };
      case "e-ammonia": return { h2: 3 * M.H2 / (2 * M.NH3) / y, co2: 0, n2: M.N2 / (2 * M.NH3) / y };
      default: return { h2: 3 * M.H2 / M.CH2 / y, co2: M.CO2 / M.CH2 / y, n2: 0 }; // FT / MTG : (CH2)n
    }
  }
  function electro(D, P) {
    const e = D.electro[P.tech];
    const kwhNm3 = avg(e.kwhNm3Min, e.kwhNm3Max);
    return {
      kwhNm3, kwhKg: kwhNm3 / P.rhoH2,
      capex: P.capexElec != null ? P.capexElec : avg(e.capexMin, e.capexMax),
      opex: avg(e.opexMin, e.opexMax) / 100
    };
  }
  function co2Usd(D, P) {
    const c = D.co2[P.co2src];
    return P.co2Usd != null ? P.co2Usd : avg(c.min, c.max);
  }
  function lcoh(D, P) {
    const e = electro(D, P), f = crf(P.wacc, P.life);
    const waterReal = P.waterStoich * (1 + P.waterOver);
    const elec = P.price * e.kwhKg / 1000;
    const capex = e.capex * (f + e.opex) / (P.hours / e.kwhKg);
    const water = P.waterPrice * waterReal / 1000;
    return { elec, capex, water, total: elec + capex + water, kwhKg: e.kwhKg, waterReal, crf: f, elecCapex: e.capex };
  }
  function productCost(D, P, prod, L) {
    L = L || lcoh(D, P);
    const s = stoich(prod.nom, P.yield), f = L.crf;
    const capexConv = avg(prod.capexMin, prod.capexMax);
    const co2Eur = co2Usd(D, P) * P.fx;
    const h2 = s.h2 * 1000 * L.total;
    const co2 = s.co2 * co2Eur;
    const synthKwh = prod.elecSynth + s.n2 * 1000 * P.n2Elec;
    const annuity = (prod.pci * 1000 / 3.6 / 8760 / P.util) * capexConv * (f + P.opexSynth);
    const elecSynth = synthKwh / 1000 * P.price;
    const total = h2 + co2 + annuity + elecSynth;
    const mwhPci = prod.pci * 1000 / 3600;
    const elecTot = s.h2 * 1000 * L.kwhKg / 1000 + s.co2 * D.co2[P.co2src].energie + synthKwh / 1000;
    return {
      nom: prod.nom, h2, co2, annuity, elecSynth, total, eurMwh: total / mwhPci, elecMwhT: elecTot,
      efficiency: mwhPci / elecTot, waterM3: s.h2 * L.waterReal, partH2: h2 / total,
      ratioFossil: total / avg(prod.fossMin, prod.fossMax), s, synthKwh, other: total - h2 - elecSynth
    };
  }
  function allProducts(D, P) {
    const L = lcoh(D, P);
    return { L, rows: D.produits.map(p => productCost(D, P, p, L)) };
  }
  function capexRetenu(prod, horizon) {
    if (horizon === "long" && prod.capexLongMin != null && prod.capexLongMax != null) return avg(prod.capexLongMin, prod.capexLongMax);
    return avg(prod.capexMin, prod.capexMax);
  }
  function sizing(D, P, prod, tonnes) {
    const t = tonnes != null ? tonnes : P.tonnage, e = electro(D, P), f = crf(P.wacc, P.life);
    const s = stoich(prod.nom, P.yield), waterReal = P.waterStoich * (1 + P.waterOver);
    const h2 = t * s.h2, co2 = t * s.co2, n2 = t * s.n2;
    const mw = h2 * 1000 * e.kwhKg / P.hours / 1000;
    const gwh = h2 * 1000 * e.kwhKg / 1e6;
    const water = h2 * 1000 * waterReal / 1000;
    const capexImpl = P.capexShare * co2Usd(D, P) * P.fx / f; // € par t/an de CO2
    const cEl = mw * 1000 * e.capex * P.loc / 1e6;
    const cSy = (t * prod.pci * 1000 / 3.6 / 8760 / P.util) * capexRetenu(prod, P.horizon) * P.loc / 1e6;
    const cCo = co2 * capexImpl * P.loc / 1e6;
    const direct = cEl + cSy + cCo, ind = direct * P.indirect, imp = (direct + ind) * P.contingency;
    const total = direct + ind + imp;
    const cf = P.pvShare * P.pvCF + (1 - P.pvShare) * P.windCF;
    const enrPrice = P.pvShare * P.pvCapex + (1 - P.pvShare) * P.windCapex;
    const enrMw = gwh * 1000 / (cf * 8760), enrCapex = enrMw * 1000 * enrPrice / 1e6;
    return { nom: prod.nom, t, h2, co2, n2, mw, gwh, water, cEl, cSy, cCo, direct, ind, imp, total,
      perKt: total / (t / 1000), enrMw, enrCapex, totalEnr: total + enrCapex, annuity: total * f,
      perT: (cSy + cCo) / t, h2PerT: s.h2, kwhKg: e.kwhKg };
  }
  function gridSizeElec(D, P, prod, sizes, capexList) {
    const base = sizing(D, P, prod, P.tonnage), k = (1 + P.indirect) * (1 + P.contingency);
    return sizes.map(t => capexList.map(c => k * ((t * base.h2PerT * 1000 * base.kwhKg / P.hours / 1000) * c * P.loc / 1000 + t * base.perT)));
  }
  function gridSizeLoc(D, P, prod, sizes, facs) {
    const base = sizing(D, P, prod, P.tonnage), e = electro(D, P), k = (1 + P.indirect) * (1 + P.contingency);
    const perTraw = base.perT / (P.loc || 1);
    return sizes.map(t => facs.map(x => k * x * ((t * base.h2PerT * 1000 * base.kwhKg / P.hours / 1000) * e.capex / 1000 + t * perTraw)));
  }
  function heatLcoh(D, P, prices, hoursList) {
    const e = electro(D, P), f = crf(P.wacc, P.life), w = P.waterPrice * P.waterStoich * (1 + P.waterOver) / 1000;
    return prices.map(p => hoursList.map(h => p * e.kwhKg / 1000 + e.capex * (f + e.opex) / (h / e.kwhKg) + w));
  }
  function heatProduct(D, P, prod, prices, capexList) {
    const e = electro(D, P), f = crf(P.wacc, P.life), w = P.waterPrice * P.waterStoich * (1 + P.waterOver) / 1000;
    const r = productCost(D, P, prod), h2t = r.s.h2;
    return prices.map(p => capexList.map(c => h2t * 1000 * (p * e.kwhKg / 1000 + c * (f + e.opex) / (P.hours / e.kwhKg) + w) + r.co2 + r.annuity + r.synthKwh / 1000 * p));
  }
  function tornado(D, P, prod) {
    const e = D.electro[P.tech], c = D.co2[P.co2src];
    const base = productCost(D, P, prod).total;
    const defs = [
      ["Prix de l'électricité (22–45 €/MWh)", { price: 22 }, { price: 45 }],
      ["Heures de pleine charge (3 500–7 500 h)", { hours: 3500 }, { hours: 7500 }],
      ["WACC (6–12 %)", { wacc: 0.06 }, { wacc: 0.12 }],
      ["Durée de vie (15–25 ans)", { life: 15 }, { life: 25 }],
      ["CAPEX électrolyseur (min–max Table 4)", { capexElec: e.capexMin }, { capexElec: e.capexMax }],
      ["Coût du CO2 (min–max Table 2)", { co2Usd: c.min }, { co2Usd: c.max }],
      ["Taux €/$ (0,85–1,00)", { fx: 0.85 }, { fx: 1.0 }],
      ["Utilisation synthèse (80–95 %)", { util: 0.95 }, { util: 0.8 }],
      ["OPEX synthèse (3–6 %)", { opexSynth: 0.03 }, { opexSynth: 0.06 }],
      ["Rendement matière (90–98 %)", { yield: 0.98 }, { yield: 0.9 }]
    ];
    return defs.map(([label, lo, hi]) => {
      const a = productCost(D, Object.assign({}, P, lo), prod).total, b = productCost(D, Object.assign({}, P, hi), prod).total;
      return { label, low: Math.min(a, b) - base, high: Math.max(a, b) - base, base };
    }).sort((x, y) => Math.abs(y.high - y.low) - Math.abs(x.high - x.low));
  }
  function decision(dec, weights, notes) {
    const sw = weights.reduce((a, b) => a + b, 0) || 1;
    const scores = dec.produits.map((_, j) => weights.reduce((a, w, i) => a + w * notes[i][j], 0) / sw);
    const rank = scores.map(s => 1 + scores.filter(x => x > s + 1e-12).length);
    return { scores, rank, sumW: sw };
  }
  const api = { M, DEFAULTS, crf, stoich, lcoh, productCost, allProducts, sizing, gridSizeElec, gridSizeLoc, heatLcoh, heatProduct, tornado, decision, capexRetenu };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.Engine = api;
})(typeof window !== "undefined" ? window : globalThis);
