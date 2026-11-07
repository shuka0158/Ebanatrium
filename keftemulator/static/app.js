"use strict";
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const api = async (url, opt = {}) => {
  const r = await fetch(url, opt);
  if (r.status === 401) { location.href = "/login"; throw new Error("login required"); }
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.statusText);
  return r.json();
};
const toast = msg => { const t = $("#toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove("show"), 2600); };

const COLORS = {
  username:"#4fd1a5", email:"#79b8ff", domain:"#b392f0", ip:"#f0883e", phone:"#e8b04a", name:"#ff7eb6",
  account:"#56d4dd", location:"#ef6b6b", link:"#5c6573", image:"#d2a8ff", image_url:"#d2a8ff", face:"#ffa657",
  vin:"#a5d6ff", plate:"#a5d6ff", btc:"#f7931a", eth:"#8a92b2", breach:"#ff5f5f", vuln:"#ff5f5f",
  port:"#9da5b4", profile:"#ff7eb6", device:"#c9d1d9", info:"#8b949e", url:"#79b8ff",
  company:"#ffd166", screenshot:"#9ecbff", leak:"#ff5f5f", case:"#ffd166",
  contact_tree:"#6366f1", section_header:"#6366f1",
};
const ORDER = ["section_header","contact_tree","profile","name","company","account","email","username","phone","location","face","device","breach",
  "leak","screenshot","domain","ip","port","vuln","btc","eth","vin","plate","image","image_url","url","info","link"];
const col = t => COLORS[t] || "#8b949e";

const S = { modules: [], scan: null, nodes: new Map(), edges: [], sinceNode: 0, sinceLog: 0, timer: null,
            cy: null, map: null, markers: null, filterType: null, sel: null, geocoded: new Set() };


/* ------------------------------------------------------------- navigation */
$$(".nav").forEach(b => b.onclick = () => showPage(b.dataset.page));
function showPage(p) {
  $$(".nav").forEach(b => b.classList.toggle("active", b.dataset.page === p));
  $$(".page").forEach(el => el.classList.toggle("active", el.id === "page-" + p));
  if (p === "scans") loadScans();
  if (p === "modules") renderModCards();
  if (p === "tools") loadTools();
  if (p === "settings") loadSettings();
  if (p === "cases") loadCases();
  if (p === "monitors") loadMonitors();
}

/* ------------------------------------------------------------- scan form */
const TYPE_LABEL = {auto:"Auto-detect", username:"Username", email:"Email", domain:"Domain", ip:"IP address",
  phone:"Phone number", name:"Person name", company:"Company (GE registry)", image:"Image / photo", image_url:"Image URL", vin:"Vehicle VIN",
  plate:"License plate", btc:"Bitcoin address", eth:"Ethereum address", url:"URL"};

function detect(v) {
  v = v.trim();
  if (/^[^@\s]+@[^@\s]+\.[a-z]{2,}$/i.test(v)) return "email";
  if (/^(\d{1,3}\.){3}\d{1,3}$/.test(v)) return "ip";
  if (/^https?:\/\/\S+\.(jpe?g|png|gif|webp|bmp|tiff?)(\?\S*)?$/i.test(v)) return "image_url";
  if (/^https?:\/\//i.test(v)) return "url";
  if (/^0x[a-f0-9]{40}$/i.test(v)) return "eth";
  if (/^(bc1[a-z0-9]{25,59}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})$/.test(v)) return "btc";
  if (/^[a-z]{2}-\d{3}-[a-z]{2}$/i.test(v)) return "plate";
  if (/^[A-HJ-NPR-Z0-9]{17}$/i.test(v) && /\d/.test(v) && /[a-z]/i.test(v)) return "vin";
  // Phone with formatting: has + or spaces/dashes
  if (/^\+?[\d\s\-().]{7,20}$/.test(v) && (v.startsWith("+") || /[\s\-()]/.test(v)) && v.replace(/\D/g, "").length >= 7) return "phone";
  // Georgian ID: exactly 11 pure digits
  if (/^\d{11}$/.test(v)) return "name";
  // Plain phone: 7+ digits
  if (/^\+?[\d\s\-().]{7,20}$/.test(v) && v.replace(/\D/g, "").length >= 7) return "phone";
  if (/^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/i.test(v)) return "domain";
  if (/\s/.test(v)) return "name";
  return v ? "username" : "";
}
function curType() { const t = $("#ttype").value; return t === "auto" ? detect($("#target").value) : t; }

async function initForm() {
  const types = await api("/api/types");
  $("#ttype").innerHTML = types.map(t => `<option value="${t}">${TYPE_LABEL[t] || t}</option>`).join("");
  S.modules = await api("/api/modules");
  renderModList();
  applyPreset("default");
}
function renderModList() {
  const t = curType();
  const groups = {};
  S.modules.forEach(m => (groups[m.category] ??= []).push(m));
  const prev = new Set($$("#moduleList input:checked").map(i => i.value));
  const first = !$("#moduleList").children.length;
  $("#moduleList").innerHTML = Object.entries(groups).map(([g, ms]) => `<div class="modgrp">${esc(g)}</div>` +
    ms.map(m => {
      const rel = !t || m.accepts.includes(t) || t === "auto";
      return `<label class="modrow ${m.available ? "" : "off"}" title="${esc(m.description)}" style="${rel ? "" : "opacity:.55"}">
        <input type="checkbox" value="${m.name}" ${m.available ? "" : "disabled"} ${(first ? m.default : prev.has(m.name)) && m.available ? "checked" : ""}>
        <span class="t">${esc(m.title)}${m.external ? '<span class="ext">tool</span>' : ""}
        ${m.available ? "" : `<span class="why">${esc(m.status)}</span>`}</span></label>`;
    }).join("")).join("");
}
function applyPreset(p) {
  $$("#moduleList input").forEach(i => {
    const m = S.modules.find(x => x.name === i.value);
    if (!m || !m.available) return;
    i.checked = p === "all" ? true : p === "none" ? false : p === "fast" ? (m.default && !m.external) : m.default;
  });
}
$$(".presets button").forEach(b => b.onclick = () => applyPreset(b.dataset.preset));
$("#depth").oninput = e => $("#depthVal").textContent = e.target.value;

function onTargetChange() {
  const t = curType();
  $("#detected").innerHTML = t ? `Detected: <b>${TYPE_LABEL[t] || t}</b>` : "Type auto-detected as you type";
  $("#dropzone").classList.toggle("hidden", $("#ttype").value !== "image");
  $("#target").classList.toggle("hidden", $("#ttype").value === "image");
  renderModList();
}
$("#target").oninput = onTargetChange;
$("#ttype").onchange = onTargetChange;

const dz = $("#dropzone");
["dragover","dragenter"].forEach(e => dz.addEventListener(e, ev => { ev.preventDefault(); dz.classList.add("over"); }));
["dragleave","drop"].forEach(e => dz.addEventListener(e, () => dz.classList.remove("over")));
$("#imageFile").onchange = () => {
  const f = $("#imageFile").files[0];
  if (!f) return;
  const img = $("#imgPreview"); img.src = URL.createObjectURL(f); img.classList.remove("hidden");
};
$$(".examples button").forEach(b => b.onclick = () => { $("#ttype").value = "auto"; $("#target").value = b.dataset.ex; onTargetChange(); });

$("#scanForm").onsubmit = async e => {
  e.preventDefault();
  const mods = $$("#moduleList input:checked").map(i => i.value);
  const depth = +$("#depth").value;
  let res;
  try {
    $("#runBtn").disabled = true;
    if ($("#ttype").value === "image") {
      const f = $("#imageFile").files[0];
      if (!f) return toast("Choose an image first");
      const fd = new FormData(); fd.append("image", f); fd.append("modules", JSON.stringify(mods)); fd.append("depth", depth); fd.append("case_id", $("#caseSel").value);
      res = await api("/api/scans", { method: "POST", body: fd });
    } else {
      const target = $("#target").value.trim();
      if (!target) return toast("Enter a target");
      res = await api("/api/scans", { method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ target, type: $("#ttype").value, modules: mods, depth, case_id: $("#caseSel").value || null }) });
    }
    openScan(res.id);
  } catch (err) { toast(err.message); }
  finally { $("#runBtn").disabled = false; }
};

/* ------------------------------------------------------------- scan view */
function openScan(id, caseId) {
  showPage("investigate");
  clearInterval(S.timer);
  Object.assign(S, { scan: { id }, nodes: new Map(), edges: [], sinceNode: 0, sinceLog: 0, filterType: null, sel: null,
                     caseId: caseId || null, src: caseId ? `/api/cases/${caseId}` : `/api/scans/${id}` });
  $("#notes").dataset.sid = "";
  S.geocoded = new Set();
  $("#log").innerHTML = ""; $("#embeds").innerHTML = ""; $("#empty").classList.add("hidden"); $("#scanView").classList.remove("hidden");
  $("#detail").classList.add("hidden");
  ["Json","Csv","Html"].forEach(f => $("#ex" + f).href = `/api/scans/${id}/export?fmt=${f.toLowerCase()}`);
  if (caseId) $("#exHtml").href = `/api/cases/${caseId}/export`;
  ["#exJson","#exCsv","#caseBtn","#monBtn"].forEach(sel => $(sel).classList.toggle("hidden", !!caseId));
  if (S.cy) S.cy.elements().remove();
  if (S.markers) S.markers.clearLayers();
  poll();
  S.timer = setInterval(poll, 1500);
}

async function poll() {
  const id = S.scan.id;
  let d;
  try { d = await api(`${S.src}?since_node=${S.sinceNode}&since_log=${S.sinceLog}`); }
  catch { return; }
  if (S.scan.id !== id && !(S.caseId && S.scan.id === `case${S.caseId}`)) return;
  S.scan = d.scan;
  if (d.full) S.nodes = new Map();
  [...d.nodes, ...d.updated].forEach(n => S.nodes.set(n.id, n));
  if (d.nodes.length && !d.full) S.sinceNode = d.nodes[d.nodes.length - 1].id;
  if (d.scans) renderCaseScans(d.scans);
  else $("#caseScans").classList.add("hidden");
  S.edges = d.edges;
  d.logs.forEach(l => {
    S.sinceLog = l.id;
    const line = document.createElement("div");
    line.className = l.level;
    line.textContent = `${new Date(l.ts * 1000).toLocaleTimeString()}  ${l.msg}`;
    $("#log").appendChild(line);
  });
  renderHead();
  if (d.nodes.length || d.updated.length) { renderResults(); updateGraph(d.nodes); updateMap(); }
  if (S.sel && S.nodes.has(S.sel)) showDetail(S.sel, true);
  if (S.scan.status !== "running") clearInterval(S.timer);
  if ($("#notes").dataset.sid != S.scan.id) { $("#notes").value = S.scan.notes || ""; $("#notes").dataset.sid = S.scan.id; }
}

function renderHead() {
  const s = S.scan;
  $("#shTarget").textContent = s.target;
  $("#shType").textContent = s.ttype; $("#shType").style.color = col(s.ttype);
  $("#shStatus").textContent = s.status; $("#shStatus").className = "status " + s.status;
  $("#shCount").textContent = S.nodes.size;
  const end = s.finished || Date.now() / 1000;
  $("#shTime").textContent = `${Math.round(end - s.created)}s · depth ${s.depth} · ${s.modules.length} modules`;
  $("#stopBtn").classList.toggle("hidden", s.status !== "running" || !!S.caseId);
  const counts = {};
  S.nodes.forEach(n => counts[n.type] = (counts[n.type] || 0) + 1);
  $("#stats").innerHTML = ORDER.filter(t => counts[t]).concat(Object.keys(counts).filter(t => !ORDER.includes(t)))
    .map(t => `<span class="stat ${S.filterType === t ? "on" : ""}" data-t="${t}"><span style="color:${col(t)}">●</span> ${t} <b>${counts[t]}</b></span>`).join("");
  $$("#stats .stat").forEach(el => el.onclick = () => { S.filterType = S.filterType === el.dataset.t ? null : el.dataset.t; renderHead(); renderResults(); });
}

function summary(n) {
  const d = n.data || {};
  const bits = [d.name, d.bio, d.location || d.city, d.country, d.carrier, d.line_type, d.title, d.breach, d.date,
                d.description, d.isp, d.Make && `${d.Make} ${d.Model || ""} ${d.ModelYear || ""}`, d.balance_btc != null && `${d.balance_btc} BTC`]
    .filter(Boolean);
  return bits.slice(0, 3).join(" · ");
}

function renderResults() {
  const q = $("#filter").value.trim().toLowerCase();
  const groups = {};
  S.nodes.forEach(n => {
    if (S.filterType && n.type !== S.filterType) return;
    if (q && !(n.value + " " + n.label + " " + JSON.stringify(n.data)).toLowerCase().includes(q)) return;
    (groups[n.type] ??= []).push(n);
  });
  const types = ORDER.filter(t => groups[t]).concat(Object.keys(groups).filter(t => !ORDER.includes(t)));
  // Populate categorized results
  const categorized = {"images": [], "domain": [], "threat": [], "people": [], "media": [], "relationships": [], "intelligence": [], "other": []};
  Object.values(groups).forEach(grp => grp.forEach(n => {
    const mod = (n.module || "").toLowerCase();
    const type = (n.type || "").toLowerCase();

    if (mod.includes("image") || mod.includes("screenshot") || mod.includes("exif") || mod.includes("hash") || mod.includes("photo") || type.includes("image")) categorized.images.push(n);
    else if (mod.includes("dns") || mod.includes("whois") || mod.includes("domain") || mod.includes("email") || type === "email_address") categorized.domain.push(n);
    else if (mod.includes("urlscan") || mod.includes("threat") || mod.includes("virus") || mod.includes("abuse") || mod.includes("malware")) categorized.threat.push(n);
    else if (mod.includes("phone") || mod.includes("hunter") || mod.includes("sherlock") || type === "phone") categorized.people.push(n);
    else if (mod.includes("pdf") || mod.includes("video") || mod.includes("media")) categorized.media.push(n);
    else if (mod.includes("graph") || mod.includes("entity") || mod.includes("relationship") || mod.includes("family")) categorized.relationships.push(n);
    else if (mod.includes("timeline") || mod.includes("case") || mod.includes("evidence") || mod.includes("court") || mod.includes("intelligence")) categorized.intelligence.push(n);
    else categorized.other.push(n);
  }));

  // Categories disabled - using plain text results instead

  // Plain text results output
  const plainTextResults = types.map(t => {
    const typeHeader = `${t}`;
    const typeResults = groups[t].map(n => {
      const label = esc(n.label || n.value);
      const module = esc(n.module);
      return `${label}\n${module}`;
    }).join("\n\n");
    return typeHeader + "\n" + typeResults;
  }).join("\n\n");

  $("#resultList").textContent = plainTextResults || (S.scan.status === "running" ? "Collecting…" : "No results.");

  // Add click handlers
  $$(".category .item, #resultList .item").forEach(el => el.onclick = () => showDetail(+el.dataset.id));
  renderEmbeds();

  // Auto-trigger AI analysis if results exist
  if (S.nodes.size > 0) triggerAIAnalysis();
}

async function triggerAIAnalysis() {
  if (!S.scan || S.scan.status === "running") return;
  if (S._aiTriggered) return;
  S._aiTriggered = true;

  const target = S.scan.target;
  const analysisEl = $("#ai-analysis-results");
  if (!analysisEl) return;

  try {
    analysisEl.innerHTML = '<div style="padding:20px; text-align:center; color:#999;">🧠 Claude analyzing findings...</div>';

    const bridgeUrl = `http://${window.location.hostname}:7778/analyze`;
    const ctrl = new AbortController();
    const timeoutId = setTimeout(() => ctrl.abort(), 120000);

    const resp = await fetch(bridgeUrl, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({target, type: "deep_analysis"}),
      signal: ctrl.signal
    });

    clearTimeout(timeoutId);

    if (!resp.ok) throw new Error("Bridge error: " + resp.status);
    const data = await resp.json();

    if (data.success && data.analysis) {
      analysisEl.innerHTML = `<div class="analysis-results">${esc(data.analysis)}</div>`;
    } else if (data.status === "analysis_requested") {
      analysisEl.innerHTML = '<div style="padding:20px; color:#999;">⏳ Waiting for Claude analysis from terminal...<br/><small>Bridge is waiting for your response here in the chat.</small></div>';
    } else {
      analysisEl.innerHTML = '<div style="padding:20px; color:#999;">⏳ Bridge connecting...</div>';
    }
  } catch (err) {
    analysisEl.innerHTML = `<div style="padding:20px; color:#ff6b6b;">⚠️ Bridge error: ${err.message}</div>`;
  }
}

// Submit analysis from textarea
function submitAnalysis() {
  const input = $("#ai-analysis-input");
  const analysis = input.value.trim();

  if (!analysis) {
    alert("Paste analysis first");
    return;
  }

  const resultsDiv = $("#ai-analysis-results");
  resultsDiv.innerHTML = `<div class="analysis-results" style="white-space: pre-wrap; word-break: break-word;">${esc(analysis)}</div>`;

  // Clear input
  input.value = "";
  alert("✅ Analysis submitted and displayed!");
}

$("#filter").oninput = renderResults;

/* live third-party search pages, loaded in the viewer's own browser */
function renderEmbeds() {
  S.nodes.forEach(n => {
    const e = n.data && n.data.embed;
    if (!e || $(`#embed-${n.id}`)) return;
    const variants = Array.isArray(e.variants) ? e.variants : Object.entries(e.variants || { [n.value]: n.data.url });
    const box = document.createElement("section");
    box.className = "embed"; box.id = `embed-${n.id}`;
    // The site refuses to be framed, so each spelling of the plate opens its search in a new tab.
    box.innerHTML = `<div class="embedbar"><b>${esc(e.title)}</b></div>
      <div class="vehbtns">
        <a class="primary vehbtn" target="_blank" rel="noopener noreferrer" href="${esc(variants[0][1])}">See vehicle image ↗</a>
        ${variants.length > 1 ? `<span class="muted">other spellings:</span>` : ""}
        ${variants.slice(1).map(([label, url]) => `<a class="btn" target="_blank" rel="noopener noreferrer" href="${esc(url)}">${esc(label)}</a>`).join("")}
      </div>`;
    $("#embeds").appendChild(box);
  });
}

/* ------------------------------------------------------------- detail */
const PIVOTABLE = ["username","email","domain","ip","phone","name","company","vin","plate","btc","eth","url","image_url"];
function fmt(v) {
  if (v == null) return "";
  if (typeof v === "object") return `<pre>${esc(JSON.stringify(v, null, 1))}</pre>`;
  const s = String(v);
  return /^https?:\/\//.test(s) ? `<a href="${esc(s)}" target="_blank" rel="noopener noreferrer">${esc(s)}</a>` : esc(s);
}
function showDetail(id, quiet) {
  const n = S.nodes.get(id); if (!n) return;
  S.sel = id;
  if (!quiet) $$("#view-results .item").forEach(el => el.classList.toggle("sel", +el.dataset.id === id));
  const d = n.data || {};
  const img = d.avatar || d.preview || (n.type === "face" ? n.value : null);
  const url = d.url || (/^https?:\/\//.test(n.value) ? n.value : null);
  const rels = S.edges.filter(e => e.dst === id).map(e => S.nodes.get(e.src)).filter(Boolean);
  const kids = S.edges.filter(e => e.src === id).length;
  const geo = d.lat != null ? `https://www.openstreetmap.org/?mlat=${d.lat}&mlon=${d.lon}#map=15/${d.lat}/${d.lon}` : null;
  $("#detailBody").innerHTML = `
    <span class="tag" style="color:${col(n.type)}">${esc(n.type)}</span>
    <h3>${esc(n.label || n.value)}</h3>
    <div class="muted" style="font-size:12px">via ${esc(n.module)} · depth ${n.depth}${rels.length ? " · from " + rels.map(r => esc(r.label || r.value)).join(", ") : ""}${kids ? ` · ${kids} linked` : ""}</div>
    ${img ? `<img class="avatar" src="${esc(img)}" alt="" referrerpolicy="no-referrer">` : ""}
    <div class="dact">
      ${PIVOTABLE.includes(n.type) && n.depth > 0 ? `<button class="primary" id="pivotBtn">Investigate this →</button>` : ""}
      ${url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">Open ↗</a>` : ""}
      ${geo ? `<a href="${geo}" target="_blank" rel="noopener">Map ↗</a>` : ""}
      <button id="copyBtn">Copy value</button>
      <button id="graphBtn">Show in graph</button>
    </div>
    <dl class="kv">${Object.entries(d).filter(([k, v]) => v !== "" && v != null && !(Array.isArray(v) && !v.length) && k !== "root")
      .map(([k, v]) => `<dt>${esc(k)}</dt><dd>${fmt(v)}</dd>`).join("")}</dl>`;
  $("#detail").classList.remove("hidden");
  $("#copyBtn").onclick = () => navigator.clipboard.writeText(n.value).then(() => toast("Copied"));
  $("#graphBtn").onclick = () => { switchView("graph"); const el = S.cy.$id(String(id)); S.cy.animate({ center: { eles: el }, zoom: 1.6 }); el.select(); };
  const pb = $("#pivotBtn");
  if (pb) pb.onclick = () => { $("#ttype").value = n.type; $("#target").value = n.value; onTargetChange(); $("#scanForm").requestSubmit(); };
}
$("#closeDetail").onclick = () => { $("#detail").classList.add("hidden"); S.sel = null; };

/* ------------------------------------------------------------- views */
$$(".tab").forEach(b => b.onclick = () => switchView(b.dataset.view));
function switchView(v) {
  $$(".tab").forEach(b => b.classList.toggle("active", b.dataset.view === v));
  $$(".view").forEach(el => el.classList.toggle("active", el.id === "view-" + v));
  if (v === "graph") { initGraph(); S.cy.resize(); relayout(); }
  if (v === "map") { initMap(); setTimeout(() => { S.map.invalidateSize(); updateMap(true); }, 50); }
}

/* graph (Maltego-style link analysis) */
function initGraph() {
  if (S.cy) return;
  S.cy = cytoscape({
    container: $("#cy"), wheelSensitivity: 0.25, minZoom: 0.1, maxZoom: 4,
    style: [
      { selector: "node", style: { "background-color": "data(c)", label: "data(l)", color: "#c9d1d9", "font-size": 9,
          "font-family": "IBM Plex Mono", "text-valign": "bottom", "text-margin-y": 4, width: "data(s)", height: "data(s)",
          "text-max-width": 140, "text-wrap": "ellipsis", "border-width": 0, "min-zoomed-font-size": 8 } },
      { selector: "node[img]", style: { "background-image": "data(img)", "background-fit": "cover", "border-width": 2, "border-color": "data(c)" } },
      { selector: "node:selected", style: { "border-width": 3, "border-color": "#fff" } },
      { selector: "edge", style: { width: 1, "line-color": "#323a46", "target-arrow-color": "#323a46", "target-arrow-shape": "triangle",
          "arrow-scale": .6, "curve-style": "bezier", label: "data(l)", "font-size": 7, color: "#5c6573", "text-rotation": "autorotate" } },
    ],
  });
  S.cy.on("tap", "node", e => showDetail(+e.target.id()));
  $("#fitBtn").onclick = () => S.cy.fit(undefined, 30);
  $("#layoutBtn").onclick = relayout;
  $("#hideLinks").onchange = () => { S.cy.elements().remove(); updateGraph([...S.nodes.values()]); relayout(); };
  updateGraph([...S.nodes.values()]);
}
function updateGraph(newNodes) {
  if (!S.cy) return;
  const hide = $("#hideLinks").checked;
  const add = [];
  newNodes.forEach(n => {
    if (hide && n.type === "link") return;
    if (S.cy.$id(String(n.id)).length) return;
    const img = n.data.avatar || n.data.preview;
    add.push({ group: "nodes", data: { id: String(n.id), l: (n.label || n.value).slice(0, 40), c: col(n.type),
      s: n.depth === 0 ? 34 : ["link","port","info"].includes(n.type) ? 10 : 18, ...(img ? { img } : {}) } });
  });
  S.cy.add(add);
  const edges = S.edges.filter(e => S.cy.$id(String(e.src)).length && S.cy.$id(String(e.dst)).length && !S.cy.$id(`e${e.src}_${e.dst}`).length)
    .map(e => ({ group: "edges", data: { id: `e${e.src}_${e.dst}`, source: String(e.src), target: String(e.dst), l: e.label } }));
  S.cy.add(edges);
  if (add.length && $("#view-graph").classList.contains("active")) { clearTimeout(S._lay); S._lay = setTimeout(relayout, 600); }
}
function relayout() { S.cy && S.cy.layout({ name: "cose", animate: false, nodeRepulsion: 9000, idealEdgeLength: 90, nodeOverlap: 20, componentSpacing: 80, padding: 30, randomize: false }).run(); }

/* map */
function initMap() {
  if (S.map) return;
  S.map = L.map("map", { worldCopyJump: true }).setView([30, 20], 2);
  const key = document.body.dataset.carto;
  const tiles = key
    ? `https://basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png?key=${encodeURIComponent(key)}`
    : "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
  L.tileLayer(tiles, {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
    maxZoom: 19 }).addTo(S.map);
  S.markers = L.featureGroup().addTo(S.map);
}
async function updateMap(fit) {
  if (!S.map) return;
  S.markers.clearLayers();
  const pts = [];
  for (const n of S.nodes.values()) {
    let { lat, lon } = n.data;
    if (lat == null && n.type === "location" && !S.geocoded.has(n.id)) {
      S.geocoded.add(n.id);
      try {
        const r = await fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(n.value)}`).then(r => r.json());
        if (r[0]) { n.data.lat = lat = +r[0].lat; n.data.lon = lon = +r[0].lon; n.data.geocoded = r[0].display_name; }
        await new Promise(res => setTimeout(res, 1100));
      } catch {}
    }
    if (lat == null || lon == null) continue;
    pts.push([lat, lon]);
    L.circleMarker([lat, lon], { radius: 8, color: col(n.type), fillOpacity: .7 })
      .bindPopup(`<b>${esc(n.label || n.value)}</b><br>${esc(n.data.accuracy || n.type)}`).on("click", () => showDetail(n.id)).addTo(S.markers);
  }
  if (fit && pts.length) S.map.fitBounds(pts, { maxZoom: 10, padding: [40, 40] });
}

/* stop + notes */
$("#stopBtn").onclick = async () => { await api(`/api/scans/${S.scan.id}/stop`, { method: "POST" }); toast("Stopping…"); };
$("#notes").oninput = () => { clearTimeout(S._nt); S._nt = setTimeout(() =>
  api(S.caseId ? `/api/cases/${S.caseId}/notes` : `/api/scans/${S.scan.id}/notes`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ notes: $("#notes").value }) }), 600); };

/* ------------------------------------------------------------- scans page */
async function loadScans() {
  const rows = await api("/api/scans");
  $("#scanRows").innerHTML = rows.map(s => `<tr>
    <td class="mono">${s.id}</td><td class="mono"><a href="#" data-open="${s.id}">${esc(s.target)}</a></td>
    <td><span class="tag" style="color:${col(s.ttype)}">${esc(s.ttype)}</span></td>
    <td class="status ${s.status}">${s.status}</td><td>${s.n}</td>
    <td>${new Date(s.created * 1000).toLocaleString()}</td>
    <td><button class="btn" data-del="${s.id}">Delete</button></td></tr>`).join("") ||
    `<tr><td colspan=7 class="muted">No scans yet.</td></tr>`;
  $$("[data-open]").forEach(a => a.onclick = e => { e.preventDefault(); openScan(+a.dataset.open); });
  $$("[data-del]").forEach(b => b.onclick = async () => { if (confirm("Delete scan #" + b.dataset.del + "?")) { await api(`/api/scans/${b.dataset.del}`, { method: "DELETE" }); loadScans(); } });

  // Clear all scans button
  const clearBtn = $("#clearScansBtn");
  if (clearBtn) {
    clearBtn.onclick = async () => {
      if (!rows.length) { alert("No scans to clear"); return; }
      if (!confirm("Delete ALL " + rows.length + " scans? This cannot be undone.")) return;
      for (const s of rows) await api(`/api/scans/${s.id}`, { method: "DELETE" });
      toast("✅ All scans cleared");
      loadScans();
    };
  }
}

/* ------------------------------------------------------------- modules page */
async function renderModCards() {
  S.modules = await api("/api/modules");
  $("#modCards").innerHTML = S.modules.map(m => `<div class="card">
    <h4><span>${esc(m.title)}</span><span class="${m.available ? "ok" : "no"}">${m.available ? "● ready" : "○ " + esc(m.status)}</span></h4>
    <div class="acc">${esc(m.category)} · accepts: ${m.accepts.join(", ")}${m.external ? " · external tool" : ""}</div>
    <p>${esc(m.description)}</p>
    ${m.homepage ? `<a href="${esc(m.homepage)}" target="_blank" rel="noopener" style="font-size:12px">${esc(m.homepage)}</a>` : ""}</div>`).join("");
  renderModList();
}

/* ------------------------------------------------------------- tools page */
let toolTimer;
async function loadTools() {
  const d = await api("/api/tools");
  $("#toolRows").innerHTML = d.tools.map(t => `<div class="toolrow"><span>${esc(t.title)}</span>
    <b class="${t.installed ? "ok" : "no"}">${t.installed ? "installed" : "missing"}</b>
    <button data-inst="${t.name}" ${d.running ? "disabled" : ""}>${t.installed ? "Reinstall" : "Install"}</button></div>`).join("");
  $$("[data-inst]").forEach(b => b.onclick = () => install(b.dataset.inst));
  $("#installAll").disabled = !!d.running;
  const log = $("#installLog"); log.textContent = d.log || "Installer idle."; log.scrollTop = log.scrollHeight;
  clearTimeout(toolTimer);
  if (d.running && $("#page-tools").classList.contains("active")) toolTimer = setTimeout(loadTools, 1500);
  else if (!d.running) { S.modules = await api("/api/modules"); renderModList(); }
}
async function install(name) {
  try { await api(`/api/tools/${name}/install`, { method: "POST" }); loadTools(); } catch (e) { toast(e.message); }
}
$("#installAll").onclick = () => install("all");

/* ------------------------------------------------------------- settings */
const KEY_HELP = { shodan: "shodan.io", hibp: "haveibeenpwned.com/API/Key", hunter: "hunter.io", virustotal: "virustotal.com",
  abuseipdb: "abuseipdb.com", numverify: "numverify.com", github_token: "github.com/settings/tokens (raises rate limit)", carto: "carto.com basemaps (map tiles)",
  intelx: "intelx.io → Account → Developer (free)", urlscan: "urlscan.io (optional, raises limit)",
  ntfy_topic: "ntfy.sh topic name for monitor alerts (any random name)" };
async function loadSettings() {
  const c = await api("/api/config");
  $("#keyFields").innerHTML = Object.keys(c.api_keys).map(k => `<label>${k} <small>${KEY_HELP[k] || ""}</small>
    <input name="key_${k}" value="${esc(c.api_keys[k])}" autocomplete="off" type="password" placeholder="not set"></label>`).join("");
  ["max_entities","threads","tool_timeout"].forEach(k => $(`[name=${k}]`).value = c[k]);
}
$("#testNotify").onclick = async () => {
  try { await api("/api/notify/test", { method: "POST" }); toast("Test notification sent"); } catch (e) { toast(e.message); }
};
$("#settingsForm").onsubmit = async e => {
  e.preventDefault();
  const body = { api_keys: {} };
  $$("#keyFields input").forEach(i => body.api_keys[i.name.slice(4)] = i.value);
  ["max_entities","threads","tool_timeout"].forEach(k => body[k] = $(`[name=${k}]`).value);
  await api("/api/config", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body) });
  $("#saved").textContent = "Saved."; setTimeout(() => $("#saved").textContent = "", 2000);
  S.modules = await api("/api/modules"); renderModList();
};

/* ------------------------------------------------------------- cases */
let CASES = [];
async function refreshCaseLists() {
  CASES = await api("/api/cases");
  const opts = CASES.map(c => `<option value="${c.id}">${esc(c.name)}</option>`).join("");
  const cur = $("#caseSel").value;
  $("#caseSel").innerHTML = `<option value="">No case</option>${opts}<option value="__new">+ New case…</option>`;
  if ([...$("#caseSel").options].some(o => o.value === cur)) $("#caseSel").value = cur;
}
async function newCase() {
  const name = prompt("Case name");
  if (!name) return null;
  const r = await api("/api/cases", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ name }) });
  await refreshCaseLists();
  return r.id;
}
$("#caseSel").onchange = async () => {
  if ($("#caseSel").value !== "__new") return;
  const id = await newCase();
  $("#caseSel").value = id ? String(id) : "";
};
async function loadCases() {
  await refreshCaseLists();
  $("#caseRows").innerHTML = CASES.map(c => `<tr>
    <td class="mono">${c.id}</td><td><a href="#" data-case="${c.id}">${esc(c.name)}</a></td>
    <td>${c.scans}</td><td>${new Date(c.created * 1000).toLocaleString()}</td>
    <td><button class="btn" data-delcase="${c.id}">Delete</button></td></tr>`).join("") ||
    `<tr><td colspan=5 class="muted">No cases yet. A case groups several scans about the same person or organisation into one graph and one report.</td></tr>`;
  $$("[data-case]").forEach(a => a.onclick = e => { e.preventDefault(); openCase(+a.dataset.case); });
  $$("[data-delcase]").forEach(b => b.onclick = async () => {
    if (confirm("Delete this case? Its scans are kept.")) { await api(`/api/cases/${b.dataset.delcase}`, { method: "DELETE" }); loadCases(); }
  });
}
$("#newCaseBtn").onclick = async () => { if (await newCase()) loadCases(); };
function openCase(id) { openScan(`case${id}`, id); }
function renderCaseScans(scans) {
  const el = $("#caseScans");
  el.classList.remove("hidden");
  el.innerHTML = `<span class="muted">Scans in this case:</span> ` + (scans.map(s =>
    `<a href="#" data-open="${s.id}" class="stat"><span style="color:${col(s.ttype)}">●</span> ${esc(s.target)} <b>${esc(s.status)}</b></a>`).join(" ")
    || `<span class="muted">none yet — start a scan with this case selected.</span>`);
  $$("[data-open]", el).forEach(a => a.onclick = e => { e.preventDefault(); openScan(+a.dataset.open); });
}
$("#caseBtn").onclick = async () => {
  await refreshCaseLists();
  const list = CASES.map(c => `${c.id}: ${c.name}`).join("\n");
  const ans = prompt(`Add this scan to which case? Enter the number, or a new name.\n\n${list || "(no cases yet)"}`);
  if (!ans) return;
  let cid = CASES.find(c => String(c.id) === ans.trim())?.id;
  if (!cid) cid = (await api("/api/cases", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ name: ans.trim() }) })).id;
  await api(`/api/scans/${S.scan.id}/case`, { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ case_id: cid }) });
  toast("Added to case"); refreshCaseLists();
};

/* ------------------------------------------------------------- monitors */
const INTERVALS = [[1,"every hour"],[6,"every 6 hours"],[24,"daily"],[168,"weekly"]];
$("#monBtn").onclick = async () => {
  const ans = prompt("Re-run this scan automatically and alert on anything new.\nHow often? Enter hours (1 = hourly, 24 = daily, 168 = weekly)", "24");
  if (!ans) return;
  try {
    await api("/api/monitors", { method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ scan_id: S.scan.id, interval_hours: +ans || 24 }) });
    toast("Monitor created — see the Monitors tab");
  } catch (e) { toast(e.message); }
};
const ago = ts => { if (!ts) return "never"; const m = Math.round((Date.now() / 1000 - ts) / 60);
  return m < 1 ? "just now" : m < 60 ? `${m} min ago` : m < 1440 ? `${Math.round(m / 60)} h ago` : `${Math.round(m / 1440)} d ago`; };
const until = ts => { if (!ts) return "—"; const m = Math.round((ts - Date.now() / 1000) / 60);
  return m <= 1 ? "soon" : m < 60 ? `in ${m} min` : m < 1440 ? `in ${Math.round(m / 60)} h` : `in ${Math.round(m / 1440)} d`; };
async function loadMonitors() {
  const ms = await api("/api/monitors");
  const unseen = ms.reduce((a, m) => a + (m.unseen || 0), 0);
  $("#monBadge").textContent = unseen || ""; $("#monBadge").classList.toggle("hidden", !unseen);
  if (!$("#page-monitors").classList.contains("active")) return;
  $("#monRows").innerHTML = ms.map(m => `<tr>
    <td><span class="tag" style="color:${col(m.ttype)}">${esc(m.ttype)}</span> <span class="mono">${esc(m.target)}</span>
      ${m.case_name ? `<div class="muted" style="font-size:12px">case: ${esc(m.case_name)}</div>` : ""}</td>
    <td><select data-int="${m.id}">${INTERVALS.map(([h, l]) => `<option value="${h}" ${+m.interval_hours === h ? "selected" : ""}>${l}</option>`).join("")}
      ${INTERVALS.some(([h]) => h === +m.interval_hours) ? "" : `<option selected value="${m.interval_hours}">every ${m.interval_hours} h</option>`}</select></td>
    <td>${m.running ? '<span class="status running">running</span>' : ago(m.last_run)}<div class="muted" style="font-size:12px">next: ${m.enabled ? until(m.next_run) : "paused"}</div></td>
    <td>${m.last_new ? `<b class="ok">+${m.last_new} new</b>` : '<span class="muted">no changes</span>'} ${m.unseen ? '<span class="badge">unseen</span>' : ""}</td>
    <td><div class="rowbtns">
      <label class="switch"><input type="checkbox" data-en="${m.id}" ${m.enabled ? "checked" : ""}> on</label>
      <button class="btn" data-run="${m.id}" ${m.running ? "disabled" : ""}>Run now</button>
      <button class="btn" data-ev="${m.id}">Changes</button>
      ${m.last_scan_id ? `<button class="btn" data-open="${m.last_scan_id}">Latest scan</button>` : ""}
      <button class="btn danger" data-delmon="${m.id}">Delete</button></div></td></tr>
    <tr class="hidden evrow" id="ev-${m.id}"><td colspan=5></td></tr>`).join("") ||
    `<tr><td colspan=5 class="muted">No monitors yet. Open any scan and click “Monitor” to re-run it on a schedule and get alerted about new findings.</td></tr>`;
  const patch = (id, body) => api(`/api/monitors/${id}`, { method: "PATCH", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body) });
  $$("[data-int]").forEach(el => el.onchange = () => patch(el.dataset.int, { interval_hours: +el.value }).then(loadMonitors));
  $$("[data-en]").forEach(el => el.onchange = () => patch(el.dataset.en, { enabled: el.checked }).then(loadMonitors));
  $$("[data-run]").forEach(b => b.onclick = async () => { await api(`/api/monitors/${b.dataset.run}/run`, { method: "POST" }); toast("Running…"); setTimeout(loadMonitors, 800); });
  $$("#monRows [data-open]").forEach(b => b.onclick = () => openScan(+b.dataset.open));
  $$("[data-delmon]").forEach(b => b.onclick = async () => { if (confirm("Delete this monitor?")) { await api(`/api/monitors/${b.dataset.delmon}`, { method: "DELETE" }); loadMonitors(); } });
  $$("[data-ev]").forEach(b => b.onclick = async () => {
    const row = $(`#ev-${b.dataset.ev}`); row.classList.toggle("hidden");
    if (row.classList.contains("hidden")) return;
    const ev = await api(`/api/monitors/${b.dataset.ev}/events`);
    row.firstElementChild.innerHTML = ev.map(e => `<div class="ev"><b>${new Date(e.ts * 1000).toLocaleString()}</b> —
      ${e.new_count ? `${e.new_count} new` : "no changes"} <a href="#" data-open="${e.scan_id}">open scan</a>
      <ul>${e.items.slice(0, 50).map(i => `<li><span style="color:${col(i.type)}">${esc(i.type)}</span> ${esc(i.label)}</li>`).join("")}</ul></div>`).join("")
      || '<span class="muted">No runs yet.</span>';
    $$("[data-open]", row).forEach(a => a.onclick = e => { e.preventDefault(); openScan(+a.dataset.open); });
  });
}
setInterval(() => loadMonitors().catch(() => {}), 30000);

/* ------------------------------------------------------------- help guide */
let guideLoaded = false;
$("#helpBtn").onclick = async () => {
  const modal = $("#guideModal");
  const content = $("#guideContent");

  if (!guideLoaded) {
    try {
      const resp = await fetch("/static/guide.html");
      const html = await resp.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      const body = doc.body;
      content.innerHTML = Array.from(body.children).map(el => el.outerHTML).join("");
      guideLoaded = true;
    } catch (e) {
      content.innerHTML = "<p style='color: #ff6b6b;'>Error loading guide. Please refresh and try again.</p>";
    }
  }

  modal.style.display = "flex";
};

$("#guideClose").onclick = () => $("#guideModal").style.display = "none";
$("#guideModal").onclick = (e) => {
  if (e.target.id === "guideModal") $("#guideModal").style.display = "none";
};
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && $("#guideModal").style.display === "flex") {
    $("#guideModal").style.display = "none";
  }
});

initForm().then(() => { refreshCaseLists(); loadMonitors(); const pg = location.hash.match(/page=(\w+)/); if (pg) showPage(pg[1]); const cs = location.hash.match(/case=(\d+)/); if (cs) openCase(+cs[1]); const m = location.hash.match(/scan=(\d+)/); if (m) { openScan(+m[1]); const v = location.hash.match(/view=(\w+)/); if (v) setTimeout(() => switchView(v[1]), 1500); } });

// Auto-poll bridge for analysis updates
setInterval(async function checkForAnalysis() {
  try {
    const resp = await fetch(`http://${window.location.hostname}:7778/check`);
    if (resp.status === 200) {
      const data = await resp.json();
      if (data.analysis) {
        const el = $("#ai-analysis-results");
        if (el) {
          el.innerHTML = `<div class="analysis-results" style="white-space: pre-wrap; word-break: break-word;">${esc(data.analysis)}</div>`;
          console.log("✅ Analysis loaded! Click 🧠 AI Analysis tab to view.");
          // Just load data - don't force tab switch
          // User can click the tab themselves
        }
      }
    }
  } catch (e) {
    // Bridge not responding - normal
  }
}, 2000); // Check every 2 seconds

