// ====== STATE KATEGORI (1 TAB UTAMA) ======
let currentTabId = null;      // tab kategori
let categoryUrls = [];
let currentCategoryIndex = 0;
let categoriesFlowActive = false;

// ====== STATE PRODUK (QUEUE) ======
let productQueue = [];        // item: { url, sendResponse }
let isProcessing = false;     // sedang memproses 1 tab produk?

function log(color, ...args) {
  console.log(`%c${args.join(" ")}`, `color:${color};font-weight:bold;`);
}

// ========== RESET STATE ==========
function resetState() {
  currentTabId = null;
  categoryUrls = [];
  currentCategoryIndex = 0;
  categoriesFlowActive = false;
  productQueue = [];
  isProcessing = false;
  console.log("🔄 State background.js direset (startup/installed).");
}

// Sinkronkan backend agar status jadi STOPPED setelah reload extension
async function forceStopScraper() {
  try {
    await fetch("http://127.0.0.1:8000/stop-scrape", { method: "POST" });
    console.log("⏸ Backend status direset ke STOPPED setelah reload extension.");
  } catch (e) {
    console.warn("⚠️ Gagal reset backend status:", e);
  }
}

// Trigger saat extension di-install ulang / di-enable
chrome.runtime.onInstalled.addListener(() => {
  resetState();
  forceStopScraper();
});
chrome.runtime.onStartup.addListener(() => {
  resetState();
  forceStopScraper();
});

// ---------- KATEGORI ----------
function openNextCategory() {
  if (!currentTabId) {
    console.warn("⚠️ currentTabId hilang. Abaikan nextCategory.");
    return;
  }
  if (currentCategoryIndex >= categoryUrls.length) {
    log("green", "✅ Semua kategori selesai.");
    categoriesFlowActive = false;
    return;
  }

  const url = categoryUrls[currentCategoryIndex];
  log("#00aaff", `🔗 Membuka kategori ${currentCategoryIndex + 1}/${categoryUrls.length}: ${url}`);

  chrome.tabs.update(currentTabId, { url, active: true });
  currentCategoryIndex++;
}

// ---------- PRODUK ----------
async function processQueue() {
  if (isProcessing || productQueue.length === 0) return;

  isProcessing = true;
  const { url, sendResponse } = productQueue.shift();
  log("#3498db", `🟢 [QUEUE] Buka tab produk: ${url} | Sisa antrian: ${productQueue.length}`);

  const tab = await chrome.tabs.create({ url, active: true });
  const tabId = tab.id;

  const delay = Math.floor(Math.random() * (20000 - 5000 + 1)) + 5000;

  const handleRemoved = (closedId) => {
    if (closedId === tabId) {
      chrome.tabs.onRemoved.removeListener(handleRemoved);
      log("#27ae60", `✅ Tab produk ditutup: ${url}`);
      try { sendResponse({ done: true }); } catch (e) { /* no-op */ }
      isProcessing = false;
      processQueue(); // lanjut produk berikutnya
    }
  };
  chrome.tabs.onRemoved.addListener(handleRemoved);

  setTimeout(() => {
    chrome.tabs.remove(tabId, () => {
      log("#f39c12", "⏳ Menutup tab produk (setelah delay)...");
    });
  }, delay);
}

// ---------- MESSAGE HANDLER ----------
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.action) {
    case "openCategories": {
      if (categoriesFlowActive) {
        log("#e67e22", "⚠️ openCategories diabaikan (sudah aktif).");
        break;
      }
      categoriesFlowActive = true;

      categoryUrls = Array.isArray(message.urls) ? message.urls : [];
      currentCategoryIndex = 0;

      chrome.tabs.create({ url: categoryUrls[0], active: true }, (tab) => {
        currentTabId = tab.id;
        currentCategoryIndex = 1; // kategori pertama sudah dibuka
        log("#ffaa00", "📄 Tab kategori utama dibuat.");
      });
      break;
    }

    case "nextCategory": {
      openNextCategory();
      break;
    }

    case "openUrl": {
      productQueue.push({ url: message.url, sendResponse });
      processQueue();
      return true; // agar sendResponse valid async
    }
  }
});
