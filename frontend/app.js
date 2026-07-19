const API = window.location.hostname === "localhost" || 
            window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://polxium-mvp.onrender.com";
let currentSymbol = "";
let currentData = null;
let chartMode = "candle";
let currencySymbol = "₹";

// ── QUICK PICK BUTTONS ────────────────────
document.querySelectorAll(".quick-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const symbol = btn.dataset.symbol;
        document.getElementById("stockInput").value = symbol;
        currentSymbol = symbol;
        setTimeout(() => runAnalysis(), 50);
    });
});

// ── ANALYZE BUTTON ────────────────────────
document.getElementById("analyzeBtn").addEventListener("click", runAnalysis);
document.getElementById("stockInput").addEventListener("keydown", e => {
    if (e.key === "Enter") runAnalysis();
});
// ── CHART TOGGLE ──────────────────────────
document.getElementById("candleBtn").addEventListener("click", () => {
    chartMode = "candle";
    document.getElementById("candleBtn").classList.add("active");
    document.getElementById("lineBtn").classList.remove("active");
    if (currentData) drawMainChart(currentData);
});

document.getElementById("lineBtn").addEventListener("click", () => {
    chartMode = "line";
    document.getElementById("lineBtn").classList.add("active");
    document.getElementById("candleBtn").classList.remove("active");
    if (currentData) drawMainChart(currentData);
});

// ── ABOUT TOGGLE ──────────────────────────
document.getElementById("aboutToggle").addEventListener("click", () => {
    const content = document.getElementById("aboutContent");
    const icon = document.querySelector(".toggle-icon");
    content.classList.toggle("hidden");
    icon.classList.toggle("open");
});

// ── MAIN ANALYSIS FUNCTION ────────────────
async function runAnalysis() {
    const rawInput = document.getElementById("stockInput")
        .value.trim().toUpperCase();
    const symbol = rawInput.replace(/\s+/g, "");
    const period = document.getElementById("periodSelect").value;

    if (!symbol) {
        showError("Please enter a stock symbol or company name");
        return;
    }

    const btn = document.getElementById("analyzeBtn");
    btn.textContent = "ANALYZING...";
    btn.disabled = true;

    currentSymbol = symbol;
    showLoading(true);
    hideResults();
    hideError();

    try {
        const res = await fetch(
            `${API}/insights/${symbol}?period=${period}`
        );

        if (!res.ok) {
            const err = await res.json();
            throw new Error(
                err.detail || "Could not fetch data for this symbol"
            );
        }

        const data = await res.json();
        currentData = data;

        fillCompanyHeader(data);
        fillVerdictCard(data.verdict);
        drawMainChart(data);
        drawBollingerChart(data);
        fillRSICard(data.indicators.rsi);
        fillMACDCard(data.indicators.macd, data);
        fillBollingerCard(data.indicators.bollinger);
        fillAboutSection(data.company);

        showResults();

    } catch (err) {
        showError(err.message);
    } finally {
        showLoading(false);
        const btn = document.getElementById("analyzeBtn");
        btn.textContent = "ANALYZE";
        btn.disabled = false;
    }
}

// ── FILL COMPANY HEADER ───────────────────
function fillCompanyHeader(data) {
    const company = data.company;
    currencySymbol = data.currency_symbol || "₹";

    document.getElementById("companyName").textContent =
        company?.name || data.resolved_symbol || currentSymbol;
    document.getElementById("companySector").textContent =
        company
            ? `${company.sector || "—"} · ${company.industry || "—"}`
            : "—";

    // Format price with correct currency
    const price = data.current_price;
    const formatted = price > 100
        ? price.toLocaleString("en-IN", { maximumFractionDigits: 2 })
        : price.toFixed(2);

    document.getElementById("currentPrice").textContent =
        `${currencySymbol}${formatted}`;
}


// ── VERDICT CARD ──────────────────────────
function fillVerdictCard(verdict) {
    const card = document.getElementById("verdictCard");
    card.className = `verdict-card ${verdict.verdict}`;
    document.getElementById("verdictLabel").textContent =
        verdict.verdict;
    document.getElementById("verdictScore").textContent =
        `${verdict.score}/100`;
    document.getElementById("verdictSummary").textContent =
        verdict.summary;
}

// ── MAIN CHART ────────────────────────────
function drawMainChart(data) {
    const raw = data.raw;
    const layout = getChartLayout();

    if (chartMode === "candle") {
        const trace = {
            type: "candlestick",
            x: raw.dates,
            open: raw.open,
            high: raw.high,
            low: raw.low,
            close: raw.close,
            increasing: { line: { color: "#10b981" } },
            decreasing: { line: { color: "#ef4444" } },
            name: currentSymbol
        };
        const mlNoticeCandle = document.getElementById("mlNotice");
    if (mlNoticeCandle) mlNoticeCandle.style.display = "none";
        Plotly.newPlot("mainChart", [trace], layout, plotConfig());
    
    } else {
        const trace = {
            type: "scatter",
            mode: "lines",
            x: raw.dates,
            y: raw.close,
            line: { color: "#a78bfa", width: 2 },
            name: "Price"
        };
    
        let traces = [trace];
    
        // Only show ML trend when enough data exists
        // SVR needs minimum 60 data points to be meaningful
        // Short periods like 1M and 3M don't have enough
        const mlNotice = document.getElementById("mlNotice");
    
        if (data.chart && data.chart.dates && data.chart.dates.length >= 60) {
            traces.push({
                type: "scatter",
                mode: "lines",
                x: data.chart.dates,
                y: data.chart.predicted,
                line: {
                    color: "#f59e0b",
                    width: 1.5,
                    dash: "dot"
                },
                name: "ML Trend"
            });
            // Hide notice when ML trend shows
            if (mlNotice) mlNotice.style.display = "none";
        } else {
            // Show notice when ML trend cannot display
            if (mlNotice) mlNotice.style.display = "block";
        }
    
        const mlNoticeCandle = document.getElementById("mlNotice");
if (mlNoticeCandle) mlNoticeCandle.style.display = "none";
        Plotly.newPlot("mainChart", traces, layout, plotConfig());
        return;
    }
}

// ── BOLLINGER CHART ───────────────────────
function drawBollingerChart(data) {
    const raw = data.raw;
    const layout = {
        ...getChartLayout(),
        height: 200,
        margin: { t: 8, r: 10, b: 30, l: 55 },
    };

    const traces = [
        {
            type: "scatter",
            mode: "lines",
            x: raw.dates,
            y: raw.close,
            line: { color: "#a78bfa", width: 1.5 },
            name: "Price"
        },
        {
            type: "scatter",
            mode: "lines",
            x: raw.dates,
            y: raw.bb_upper,
            line: { color: "#6b7280", width: 1, dash: "dash" },
            name: "Upper Band"
        },
        {
            type: "scatter",
            mode: "lines",
            x: raw.dates,
            y: raw.bb_middle,
            line: { color: "#7c3aed", width: 1 },
            name: "Middle"
        },
        {
            type: "scatter",
            mode: "lines",
            x: raw.dates,
            y: raw.bb_lower,
            line: { color: "#6b7280", width: 1, dash: "dash" },
            name: "Lower Band",
            fill: "tonexty",
            fillcolor: "rgba(124, 58, 237, 0.05)"
        }
    ];

    Plotly.newPlot("bollingerChart", traces, layout, plotConfig());
}

// ── RSI CARD ──────────────────────────────
function fillRSICard(rsi) {
    document.getElementById("rsiValue").textContent =
        rsi.value.toFixed(1);
    document.getElementById("rsiLabel").textContent =
        rsi.label;
    document.getElementById("rsiLabel").className =
        `insight-label ${rsi.signal}`;
    document.getElementById("rsiExplanation").textContent =
        rsi.explanation;

    // Move marker on bar
    const pct = (rsi.value / 100) * 100;
    document.getElementById("rsiMarker").style.left = `${pct}%`;
}

// ── MACD CARD ─────────────────────────────
function fillMACDCard(macd, data) {
    document.getElementById("macdLabel").textContent =
        macd.label;
    document.getElementById("macdLabel").className =
        `insight-label ${macd.signal}`;
    document.getElementById("macdExplanation").textContent =
        macd.explanation;

    // Mini MACD chart
    if (data.raw) {
        const layout = {
            paper_bgcolor: "#10101a",
            plot_bgcolor: "#10101a",
            font: { color: "#6b7280", size: 9 },
            margin: { t: 4, r: 4, b: 20, l: 40 },
            showlegend: false,
            xaxis: { showgrid: false, showticklabels: false },
            yaxis: { gridcolor: "#1f1f35", zeroline: true,
                zerolinecolor: "#6b7280" }
        };

        // We'd need MACD history from backend for this
        // For now show a placeholder bar chart
        Plotly.newPlot("macdMiniChart", [], layout, plotConfig());
    }
}

// ── BOLLINGER CARD ────────────────────────
function fillBollingerCard(bb) {
    document.getElementById("bbLabel").textContent = bb.label;
    document.getElementById("bbLabel").className =
        `insight-label ${bb.signal}`;
    document.getElementById("bbExplanation").textContent =
        bb.explanation;
}

// ── ABOUT SECTION ─────────────────────────
function fillAboutSection(company) {
    const descEl = document.getElementById("companyDesc");
    const countryEl = document.getElementById("companyCountry");
    const websiteEl = document.getElementById("companyWebsite");

    if (!company) {
        descEl.textContent = "Company information not available for this stock.";
        countryEl.textContent = "";
        websiteEl.textContent = "";
        return;
    }

    const desc = company.description;
    if (!desc || desc === "N/A" || desc.length < 20) {
        descEl.textContent = "Detailed company description not available.";
    } else {
        descEl.textContent = desc;
    }

    countryEl.textContent = company.country && company.country !== "N/A"
        ? company.country : "";

    if (company.website && company.website !== "N/A") {
        websiteEl.innerHTML = `<a href="${company.website}" 
            target="_blank" 
            style="color:#a78bfa; text-decoration:none;">
            ${company.website}
        </a>`;
    } else {
        websiteEl.textContent = "";
    }
}

// ── AI CHATBOX ────────────────────────────
document.getElementById("askBtn").addEventListener("click", askQuestion);
document.getElementById("chatInput").addEventListener("keydown", e => {
    if (e.key === "Enter") askQuestion();
});

async function askQuestion() {
    const input = document.getElementById("chatInput");
    const question = input.value.trim();

    if (!question) return;
    if (!currentData) {
        showError("Please analyze a stock first");
        return;
    }

    appendMessage(question, "user");
    input.value = "";

    const context = `
Stock: ${currentSymbol}
Current Price: ${currentData.current_price}
Overall Verdict: ${currentData.verdict.verdict} (${currentData.verdict.score}/100)
RSI: ${currentData.indicators.rsi.value} — ${currentData.indicators.rsi.label}
MACD: ${currentData.indicators.macd.label}
Bollinger: ${currentData.indicators.bollinger.label}
Verdict Summary: ${currentData.verdict.summary}
    `.trim();

    try {
        const res = await fetch(`${API}/ask`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question, context })
        });
    
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            const errMsg = errData.detail || "AI service error";
            appendMessage(`Could not get answer: ${errMsg}`, "ai");
            return;
        }
    
        const data = await res.json();
    
        if (!data.answer) {
            appendMessage("Received empty response. Try again.", "ai");
            return;
        }
    
        appendMessage(data.answer, "ai");
    
    } catch (err) {
        console.error("Ask error:", err);
        appendMessage(
            "Connection error. Check your internet and try again.",
            "ai"
        );
    }
}

function appendMessage(text, sender) {
    const history = document.getElementById("chatHistory");
    const div = document.createElement("div");
    div.className = `chat-message ${sender}`;
    div.textContent = text;
    history.appendChild(div);
    history.scrollTop = history.scrollHeight;
}

// ── CHART HELPERS ─────────────────────────
function getChartLayout() {
    return {
        paper_bgcolor: "#10101a",
        plot_bgcolor: "#10101a",
        font: { color: "#9ca3af", size: 10 },
        margin: { t: 10, r: 10, b: 40, l: 55 },
        legend: {
            orientation: "h",
            y: -0.15,
            font: { size: 10 }
        },
        xaxis: {
            gridcolor: "#1f1f35",
            showgrid: true,
            rangeslider: { visible: false }
        },
        yaxis: {
            gridcolor: "#1f1f35",
            showgrid: true
        }
    };
}

function plotConfig() {
    return {
        responsive: true,
        displayModeBar: false
    };
}

// ── UI HELPERS ────────────────────────────
function showLoading(show) {
    document.getElementById("loading")
        .classList.toggle("hidden", !show);
}

function showResults() {
    document.getElementById("results").classList.remove("hidden");
}

function hideResults() {
    document.getElementById("results").classList.add("hidden");
}

function showError(msg) {
    const box = document.getElementById("errorBox");
    document.getElementById("errorMsg").textContent = msg;
    box.classList.remove("hidden");
}

function hideError() {
    document.getElementById("errorBox").classList.add("hidden");
}