// ========= UTIL =========
const delay = (ms) => new Promise(res => setTimeout(res, ms));

async function httpText(url) {
  const res = await fetch(url);
  return res.text();
}
async function httpJson(url) {
  const res = await fetch(url);
  return res.json();
}

// ========= BACKEND API =========
async function getScrapeStatus() {
  const data = await httpJson("http://127.0.0.1:8000/scrape/status");
  return data.status;
}
async function fetchPageUrls() {
  const text = await httpText("http://127.0.0.1:8000/scrape/page-urls");
  return text.split("\n").map(s => s.trim()).filter(Boolean);
}
async function fetchUrlsTxt() {
  try {
    const txt = await httpText("http://127.0.0.1:8000/scrape/urls");
    return txt.split("\n").map(u => u.trim()).filter(u => u.startsWith("https://shopee.co.id"));
  } catch (e) {
    console.error("❌ Gagal baca Urls.txt:", e);
    return [];
  }
}
async function clearUrlsTxt() {
  try {
    await fetch("http://127.0.0.1:8000/scrape/urls/clear", { method: "POST" });
    console.log("🧹 Urls.txt dibersihkan via backend.");
  } catch (e) {
    console.error("❌ Gagal clear Urls.txt:", e);
  }
}

// ========= LOG KE BACKEND =========
async function writeLogLine(categoryUrl, productUrl) {
  try {
    await fetch("http://127.0.0.1:8000/scrape/log", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ line: `${categoryUrl} | ${productUrl}` })
    });
  } catch (e) {
    console.error("❌ Gagal tulis log:", e);
  }
}

// ========= LOG CONSOLE =========
function log(color, ...args) {
  console.log(`%c${args.join(" ")}`, `color:${color};font-weight:bold;`);
}

// ========= DETEKSI HALAMAN =========
const href = window.location.href;
const isDashboard = href.startsWith("http://127.0.0.1:8000/scrape");
const isShopee = href.startsWith("https://shopee.co.id/");
const isCategory =
  isShopee && (href.includes("cat.") || href.includes("page_type=search") || href.includes("/search?"));

// ========= GLOBAL CONTROL =========
let shouldStopScraping = false; // flag baru: berhenti jika status berubah jadi stopped

// ========= DASHBOARD MONITOR =========
async function runDashboard() {
  let lastStatus = "stopped";
  let hasStartedThisSession = false;

  setInterval(async () => {
    try {
      const status = await getScrapeStatus();

      // 🚀 Deteksi mulai
      if (status === "running" && lastStatus !== "running") {
        if (!hasStartedThisSession) {
          log("#2ecc71", "🚀 Status RUNNING terdeteksi. Memulai scraping kategori...");
          hasStartedThisSession = true;
          shouldStopScraping = false;
          const urls = await fetchPageUrls();
          chrome.runtime.sendMessage({ action: "openCategories", urls });
        } else {
          log("#f39c12", "⚠️ RUNNING terdeteksi namun sudah dijalankan di sesi ini.");
        }
      }

      // ⛔ Deteksi berhenti → hentikan scraping di tab Shopee
      if (status === "stopped" && lastStatus === "running") {
        log("#e74c3c", "⛔ Scrape dihentikan (backend STOPPED).");
        shouldStopScraping = true;
        hasStartedThisSession = false;
      }

      lastStatus = status;
    } catch (e) {
      console.error("⚠️ Gagal cek status:", e);
    }
  }, 3000);
}

// ========= FLOW: KATEGORI =========
async function openUrlsSequentiallyPerPage() {
  const categoryUrl = window.location.href;

  let urls = await fetchUrlsTxt();
  let tries = 0;
  while (urls.length === 0 && tries < 4) {
    if (shouldStopScraping) {
      log("#e74c3c", "⏹ Berhenti: status backend STOPPED.");
      return;
    }
    log("#e67e22", "⚠️ Urls.txt kosong, tunggu 5s lalu cek lagi...");
    await delay(5000);
    urls = await fetchUrlsTxt();
    tries++;
  }

  if (urls.length === 0) {
    log("#e67e22", "♻️ Urls.txt masih kosong. Reload 1x untuk memantik network.");
    location.reload();
    return;
  }

  for (let i = 0; i < urls.length; i++) {
    if (shouldStopScraping) {
      log("#e74c3c", "⏹ Berhenti sebelum membuka produk berikutnya.");
      return;
    }
    const productUrl = urls[i];
    await writeLogLine(categoryUrl, productUrl);

    log("#3498db", `🔗 [Page] ${categoryUrl} | Produk ${i + 1}/${urls.length}: ${productUrl}`);

    await new Promise((resolve) => {
      chrome.runtime.sendMessage({ action: "openUrl", url: productUrl }, (resp) => {
        if (resp && resp.done) resolve();
      });
    });
  }

  await clearUrlsTxt();
}

async function paginateCategoryTillEnd() {
  let page = 1;
  while (true) {
    if (shouldStopScraping) {
      log("#e74c3c", "⏹ Berhenti pagination: status backend STOPPED.");
      break;
    }

    log("#9b59b6", `📄 Halaman ${page}`);
    await openUrlsSequentiallyPerPage();

    const nextBtn =
      document.querySelector('a.shopee-icon-button--right') ||
      document.querySelector('.shopee-icon-button.shopee-icon-button--right');

    const disabled =
      !nextBtn ||
      nextBtn.getAttribute("aria-disabled") === "true" ||
      nextBtn.classList.contains("disabled") ||
      nextBtn.style.pointerEvents === "none";

    if (disabled) {
      log("green", "✅ Halaman terakhir kategori ini. Pindah ke kategori berikutnya.");
      chrome.runtime.sendMessage({ action: "nextCategory" });
      break;
    }

    nextBtn.click();
    log("#f39c12", "➡️ Klik Next. Tunggu halaman termuat 3s...");
    page++;
    await delay(3000);
  }
}

// ========= ENTRY =========
(async () => {
  if (isDashboard) {
    runDashboard();
    return;
  }

  if (isCategory) {
    await delay(3000);
    paginateCategoryTillEnd();
  }
})();
