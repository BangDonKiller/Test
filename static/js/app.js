/**
 * 記帳程式 – Web Front-end
 * Handles calendar rendering, API communication, and UI interactions.
 */

/* ── Constants ─────────────────────────────────────────────────────────────── */
const INCOME_CATEGORIES  = ["薪資", "獎金", "投資收益", "其他收入"];
const EXPENSE_CATEGORIES = ["餐飲", "交通", "娛樂", "購物", "醫療", "教育", "住房", "其他支出"];

/* ── State ─────────────────────────────────────────────────────────────────── */
const today        = new Date();
let   currentYear  = today.getFullYear();
let   currentMonth = today.getMonth() + 1;   // 1-based
let   selectedDate = null;                    // "YYYY-MM-DD" string
let   editIndex    = null;                    // non-null → edit mode
let   pendingDeleteIndex = null;
let   monthSummary = null;                    // last fetched month summary

/* ── DOM references ────────────────────────────────────────────────────────── */
const monthLabel    = document.getElementById("month-label");
const calDays       = document.getElementById("cal-days");
const transTitle    = document.getElementById("trans-title");
const transBody     = document.getElementById("trans-body");

const sumIncome     = document.getElementById("sum-income");
const sumExpense    = document.getElementById("sum-expense");
const sumBalance    = document.getElementById("sum-balance");

const btnPrev       = document.getElementById("btn-prev");
const btnNext       = document.getElementById("btn-next");
const btnAdd        = document.getElementById("btn-add");

const modalOverlay  = document.getElementById("modal-overlay");
const modalTitle    = document.getElementById("modal-title");
const modalForm     = document.getElementById("modal-form");
const selCategory   = document.getElementById("sel-category");
const inpAmount     = document.getElementById("inp-amount");
const inpNote       = document.getElementById("inp-note");
const formError     = document.getElementById("form-error");
const btnCancel     = document.getElementById("btn-cancel");

const confirmOverlay = document.getElementById("confirm-overlay");
const btnConfirmOk   = document.getElementById("btn-confirm-ok");
const btnConfirmCancel = document.getElementById("btn-confirm-cancel");

/* ── Toast notification ─────────────────────────────────────────────────────── */
const toastEl = document.getElementById("toast");
let toastTimer = null;

function showToast(msg, isError = false) {
  clearTimeout(toastTimer);
  toastEl.textContent = msg;
  toastEl.classList.toggle("toast--error", isError);
  toastEl.classList.remove("hidden");
  toastTimer = setTimeout(() => toastEl.classList.add("hidden"), 3000);
}

/* ── API helpers ────────────────────────────────────────────────────────────── */
async function apiFetch(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "伺服器錯誤");
  return data;
}

/* ── Utility ────────────────────────────────────────────────────────────────── */
function toDateStr(year, month, day) {
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function todayStr() {
  return toDateStr(today.getFullYear(), today.getMonth() + 1, today.getDate());
}

function fmtAmount(amount, type) {
  const sign = type === "income" ? "＋" : "－";
  return `${sign} ${Number(amount).toLocaleString("zh-Hant", { maximumFractionDigits: 0 })}`;
}

function daysInMonth(year, month) {
  return new Date(year, month, 0).getDate();
}

/** Returns 0=Mon … 6=Sun index for the first day of the month. */
function firstDayIndex(year, month) {
  const jsDay = new Date(year, month - 1, 1).getDay(); // 0=Sun … 6=Sat
  return jsDay === 0 ? 6 : jsDay - 1;                  // convert to Mon-first
}

/* ── Calendar rendering ─────────────────────────────────────────────────────── */
async function renderCalendar() {
  monthLabel.textContent = `${currentYear} 年 ${String(currentMonth).padStart(2, "0")} 月`;

  // Fetch month summary (includes which days have transactions)
  try {
    monthSummary = await apiFetch(`/api/transactions/month/${currentYear}/${currentMonth}`);
  } catch {
    monthSummary = { days_with_transactions: [], income: 0, expense: 0, balance: 0 };
  }

  const daysWithTrans = new Set(monthSummary.days_with_transactions);
  const total         = daysInMonth(currentYear, currentMonth);
  const startIdx      = firstDayIndex(currentYear, currentMonth);
  const tStr          = todayStr();

  calDays.innerHTML = "";

  // Leading blank cells
  for (let i = 0; i < startIdx; i++) {
    const blank = document.createElement("div");
    blank.className = "day-cell empty";
    calDays.appendChild(blank);
  }

  // Day cells
  for (let day = 1; day <= total; day++) {
    const dateStr = toDateStr(currentYear, currentMonth, day);
    const btn     = document.createElement("button");
    btn.type      = "button";

    const isToday    = dateStr === tStr;
    const isSelected = dateStr === selectedDate;
    const hasTrans   = daysWithTrans.has(dateStr);
    // Column index (0=Mon … 6=Sun)
    const colIdx     = (startIdx + day - 1) % 7;
    const isWeekend  = colIdx >= 5;

    const classes = ["day-cell"];
    if (isToday)    classes.push("today");
    if (isSelected) classes.push("selected");
    if (hasTrans && !isSelected) classes.push("has-trans");
    if (isWeekend)  classes.push("weekend");
    btn.className = classes.join(" ");

    btn.setAttribute("aria-label", dateStr);
    btn.setAttribute("aria-pressed", isSelected ? "true" : "false");

    btn.innerHTML = `<span>${day}</span>${hasTrans ? '<span class="day-cell__dot">●</span>' : ""}`;
    btn.addEventListener("click", () => selectDate(dateStr));
    calDays.appendChild(btn);
  }

  renderSummary();
}

function renderSummary() {
  if (!monthSummary) return;
  const { income, expense, balance } = monthSummary;
  sumIncome.textContent  = `本月收入：＋ ${Number(income).toLocaleString("zh-Hant", { maximumFractionDigits: 0 })} 元`;
  sumExpense.textContent = `本月支出：－ ${Number(expense).toLocaleString("zh-Hant", { maximumFractionDigits: 0 })} 元`;
  const balSign = balance >= 0 ? "＋" : "－";
  sumBalance.textContent  = `結餘：${balSign} ${Math.abs(balance).toLocaleString("zh-Hant", { maximumFractionDigits: 0 })} 元`;
  sumBalance.classList.toggle("negative", balance < 0);
}

/* ── Transaction list ───────────────────────────────────────────────────────── */
async function renderTransactions() {
  if (!selectedDate) {
    transTitle.textContent = "請選擇日期";
    transBody.innerHTML = `<tr class="empty-row"><td colspan="5">請先點選日期</td></tr>`;
    return;
  }

  let transactions = [];
  try {
    transactions = await apiFetch(`/api/transactions/${selectedDate}`);
  } catch {
    transactions = [];
  }

  const [y, m, d] = selectedDate.split("-");
  transTitle.textContent = `📅 ${y} 年 ${m} 月 ${d} 日  共 ${transactions.length} 筆`;

  if (transactions.length === 0) {
    transBody.innerHTML = `<tr class="empty-row"><td colspan="5">此日期尚無記帳資料</td></tr>`;
    return;
  }

  transBody.innerHTML = transactions.map((t, i) => {
    const isIncome = t.type === "income";
    return `
      <tr>
        <td><span class="badge badge--${t.type}">${isIncome ? "收入" : "支出"}</span></td>
        <td>${escHtml(t.category)}</td>
        <td class="text-right amount--${t.type}">${fmtAmount(t.amount, t.type)}</td>
        <td class="hide-sm">${escHtml(t.note || "")}</td>
        <td class="col-actions">
          <div class="btn-row">
            <button class="btn btn--edit" aria-label="編輯第${i + 1}筆" onclick="openEdit(${i})">✏️</button>
            <button class="btn btn--danger" aria-label="刪除第${i + 1}筆" onclick="confirmDelete(${i})">🗑</button>
          </div>
        </td>
      </tr>`;
  }).join("");
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/* ── Date selection ─────────────────────────────────────────────────────────── */
async function selectDate(dateStr) {
  selectedDate = dateStr;
  await Promise.all([renderCalendar(), renderTransactions()]);
}

/* ── Month navigation ───────────────────────────────────────────────────────── */
btnPrev.addEventListener("click", async () => {
  if (currentMonth === 1) { currentMonth = 12; currentYear--; }
  else currentMonth--;
  await renderCalendar();
});

btnNext.addEventListener("click", async () => {
  if (currentMonth === 12) { currentMonth = 1; currentYear++; }
  else currentMonth++;
  await renderCalendar();
});

/* ── Modal: open / close ────────────────────────────────────────────────────── */
function openModal(title) {
  modalTitle.textContent = title;
  formError.textContent  = "";
  formError.classList.add("hidden");
  modalOverlay.classList.remove("hidden");
  inpAmount.focus();
}

function closeModal() {
  modalOverlay.classList.add("hidden");
  modalForm.reset();
  editIndex = null;
  updateCategoryOptions();
}

btnCancel.addEventListener("click", closeModal);
modalOverlay.addEventListener("click", e => { if (e.target === modalOverlay) closeModal(); });

/* ── Category dropdown ──────────────────────────────────────────────────────── */
function updateCategoryOptions() {
  const typeVal = modalForm.querySelector('input[name="type"]:checked').value;
  const cats    = typeVal === "income" ? INCOME_CATEGORIES : EXPENSE_CATEGORIES;
  const current = selCategory.value;
  selCategory.innerHTML = cats.map(c => `<option value="${c}">${c}</option>`).join("");
  if (cats.includes(current)) selCategory.value = current;
}

modalForm.querySelectorAll('input[name="type"]').forEach(r =>
  r.addEventListener("change", updateCategoryOptions)
);

/* ── Add transaction ────────────────────────────────────────────────────────── */
btnAdd.addEventListener("click", () => {
  if (!selectedDate) { showToast("請先點選日期", true); return; }
  editIndex = null;
  modalForm.reset();
  updateCategoryOptions();
  openModal("新增記帳");
});

/* ── Edit transaction ───────────────────────────────────────────────────────── */
window.openEdit = async function (index) {
  let transactions;
  try {
    transactions = await apiFetch(`/api/transactions/${selectedDate}`);
  } catch { return; }

  const t = transactions[index];
  if (!t) return;

  editIndex = index;
  modalForm.reset();

  // Set type radio
  modalForm.querySelector(`input[name="type"][value="${t.type}"]`).checked = true;
  updateCategoryOptions();
  selCategory.value = t.category || "";
  inpAmount.value   = t.amount;
  inpNote.value     = t.note || "";

  openModal("編輯記帳");
};

/* ── Form submit ────────────────────────────────────────────────────────────── */
modalForm.addEventListener("submit", async e => {
  e.preventDefault();
  formError.classList.add("hidden");

  const type     = modalForm.querySelector('input[name="type"]:checked').value;
  const category = selCategory.value;
  const amount   = parseFloat(inpAmount.value);
  const note     = inpNote.value.trim();

  if (!category) { showFormError("請選擇分類"); return; }
  if (isNaN(amount) || amount <= 0) { showFormError("請輸入有效的正數金額"); return; }

  const payload = { type, category, amount, note };

  try {
    if (editIndex !== null) {
      await apiFetch(`/api/transactions/${selectedDate}/${editIndex}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    } else {
      await apiFetch(`/api/transactions/${selectedDate}`, {
        method: "POST",
        body: JSON.stringify(payload),
      });
    }
    closeModal();
    await Promise.all([renderCalendar(), renderTransactions()]);
  } catch (err) {
    showFormError(err.message);
  }
});

function showFormError(msg) {
  formError.textContent = msg;
  formError.classList.remove("hidden");
}

/* ── Delete transaction ─────────────────────────────────────────────────────── */
window.confirmDelete = function (index) {
  pendingDeleteIndex = index;
  confirmOverlay.classList.remove("hidden");
};

btnConfirmOk.addEventListener("click", async () => {
  confirmOverlay.classList.add("hidden");
  if (pendingDeleteIndex === null) return;
  try {
    await apiFetch(`/api/transactions/${selectedDate}/${pendingDeleteIndex}`, {
      method: "DELETE",
    });
    pendingDeleteIndex = null;
    await Promise.all([renderCalendar(), renderTransactions()]);
  } catch (err) {
    showToast(`刪除失敗：${err.message}`, true);
  }
});

btnConfirmCancel.addEventListener("click", () => {
  confirmOverlay.classList.add("hidden");
  pendingDeleteIndex = null;
});

confirmOverlay.addEventListener("click", e => {
  if (e.target === confirmOverlay) {
    confirmOverlay.classList.add("hidden");
    pendingDeleteIndex = null;
  }
});

/* ── Keyboard: close modal on Escape ────────────────────────────────────────── */
document.addEventListener("keydown", e => {
  if (e.key === "Escape") {
    if (!modalOverlay.classList.contains("hidden"))   closeModal();
    if (!confirmOverlay.classList.contains("hidden")) {
      confirmOverlay.classList.add("hidden");
      pendingDeleteIndex = null;
    }
  }
});

/* ── Initial render ─────────────────────────────────────────────────────────── */
(async () => {
  selectedDate = todayStr();
  await renderCalendar();
  await renderTransactions();
})();
