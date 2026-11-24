(() => {
  const byId = (id) => document.getElementById(id);
  const statusEl = byId("sim-status");
  const errorEl = byId("sim-error");
  const opEl = byId("sim-op");
  const acEl = byId("sim-ac");
  const tranEl = byId("sim-tran");
  const runBtn = byId("sim-run");
  if (!runBtn) return;

  let acChart = null;
  let tranChart = null;

  function setStatus(text, kind = "") {
    statusEl.textContent = text;
    statusEl.className = `status-box ${kind}`.trim();
  }

  function showError(message) {
    errorEl.hidden = false;
    errorEl.textContent = message;
  }

  function clearResults() {
    errorEl.hidden = true;
    errorEl.textContent = "";
    opEl.hidden = true;
    ["op-vb", "op-ve", "op-vc", "op-vce", "op-ic"].forEach((id) => {
      const el = byId(id);
      if (el) el.textContent = "-";
    });
    acEl.hidden = true;
    tranEl.hidden = true;
    if (acChart) {
      acChart.destroy();
      acChart = null;
    }
    if (tranChart) {
      tranChart.destroy();
      tranChart = null;
    }
  }

  function num(id) {
    return byId(id).value.trim();
  }

  function payload() {
    return {
      analysis: byId("sim-analysis").value,
      vcc: num("sim-vcc"),
      r1: num("sim-r1"),
      r2: num("sim-r2"),
      rc: num("sim-rc"),
      re: num("sim-re"),
      rl: num("sim-rl"),
      cin: num("sim-cin"),
      cout: num("sim-cout"),
      amp: num("sim-amp"),
      freq: num("sim-freq"),
    };
  }

  function fmt(v, digits = 4) {
    if (typeof v !== "number" || !Number.isFinite(v)) return "-";
    return v.toFixed(digits);
  }

  function renderOp(data) {
    const op = data.op || {};
    byId("op-vb").textContent = fmt(op.vb);
    byId("op-ve").textContent = fmt(op.ve);
    byId("op-vc").textContent = fmt(op.vc);
    byId("op-vce").textContent = fmt(op.vce);
    byId("op-ic").textContent = fmt(op.ic_ma);
    opEl.hidden = false;
  }

  function renderAc(data) {
    const ac = data.ac || {};
    const freq = ac.freq_hz || [];
    const gain = ac.gain_db || [];
    const phase = ac.phase_deg || [];
    acEl.hidden = false;
    const ctx = byId("acChart").getContext("2d");
    acChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: freq,
        datasets: [
          {
            label: "Gain (dB)",
            data: gain,
            borderColor: "#1d638b",
            backgroundColor: "rgba(29,99,139,0.08)",
            yAxisID: "yGain",
            pointRadius: 0,
            borderWidth: 2,
          },
          {
            label: "Phase (deg)",
            data: phase,
            borderColor: "#c05a2b",
            backgroundColor: "rgba(192,90,43,0.08)",
            yAxisID: "yPhase",
            pointRadius: 0,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        interaction: { mode: "index", intersect: false },
        scales: {
          x: {
            type: "logarithmic",
            title: { display: true, text: "Frequency (Hz)" },
          },
          yGain: {
            type: "linear",
            position: "left",
            title: { display: true, text: "Gain (dB)" },
          },
          yPhase: {
            type: "linear",
            position: "right",
            title: { display: true, text: "Phase (deg)" },
            grid: { drawOnChartArea: false },
          },
        },
      },
    });
  }

  function renderTran(data) {
    const tran = data.tran || {};
    const t = tran.time_ms || [];
    const vin = tran.vin_v || [];
    const vout = tran.vout_v || [];
    tranEl.hidden = false;
    const ctx = byId("tranChart").getContext("2d");
    tranChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: t,
        datasets: [
          {
            label: "Vin (V)",
            data: vin,
            borderColor: "#2e7d32",
            pointRadius: 0,
            borderWidth: 2,
          },
          {
            label: "Vout (V)",
            data: vout,
            borderColor: "#1d638b",
            pointRadius: 0,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        interaction: { mode: "index", intersect: false },
        scales: {
          x: { title: { display: true, text: "Time (ms)" } },
          y: { title: { display: true, text: "Voltage (V)" } },
        },
      },
    });
  }

  async function runSimulation() {
    clearResults();
    setStatus("กำลังรัน ngspice simulation...", "");
    runBtn.disabled = true;
    try {
      const res = await fetch('/api/simulate', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload()),
      });
      const data = await res.json();
      if (!data.ok) {
        setStatus("Simulation ล้มเหลว", "error");
        showError(data.error || "ไม่ทราบสาเหตุ");
        return;
      }
      setStatus(`สำเร็จ (${data.analysis}) · Engine: ${data.engine} · Model: ${data.model} · Run: ${data.run_id}`, "ok");
      if (data.analysis === "op") renderOp(data);
      if (data.analysis === "ac") renderAc(data);
      if (data.analysis === "tran") renderTran(data);
    } catch (err) {
      setStatus("Simulation ล้มเหลว", "error");
      showError(err && err.message ? err.message : "เชื่อมต่อ API ไม่สำเร็จ");
    } finally {
      runBtn.disabled = false;
    }
  }

  runBtn.addEventListener("click", runSimulation);
})();
