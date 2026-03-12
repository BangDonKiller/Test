"""
Python 記帳程式 (Accounting Program with Calendar)
Author: GitHub Copilot
Python 3.8+
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import calendar
import json
import os
from datetime import date, datetime


# ── Constants ─────────────────────────────────────────────────────────────────
DATA_FILE = "transactions.json"

INCOME_CATEGORIES = ["薪資", "獎金", "投資收益", "其他收入"]
EXPENSE_CATEGORIES = ["餐飲", "交通", "娛樂", "購物", "醫療", "教育", "住房", "其他支出"]

WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"]

COLOR_BG = "#F7F9FC"
COLOR_PRIMARY = "#4A90D9"
COLOR_INCOME = "#27AE60"
COLOR_EXPENSE = "#E74C3C"
COLOR_TODAY = "#FFF3CD"
COLOR_SELECTED = "#D6EAF8"
COLOR_HAS_TRANS = "#EBF5FB"
COLOR_HEADER = "#2C3E50"
COLOR_BTN_ADD = "#27AE60"
COLOR_BTN_EDIT = "#F39C12"
COLOR_BTN_DEL = "#E74C3C"


# ── Data Layer ─────────────────────────────────────────────────────────────────
def load_data() -> dict:
    """Load transactions from JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_data(data: dict) -> None:
    """Persist transactions to JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Main Application ───────────────────────────────────────────────────────────
class AccountingApp(tk.Tk):
    """Root window for the accounting application."""

    def __init__(self):
        super().__init__()
        self.title("記帳程式 📒")
        self.geometry("960x660")
        self.minsize(820, 580)
        self.configure(bg=COLOR_BG)
        self.resizable(True, True)

        # App state
        self.data: dict = load_data()           # {date_str: [transaction, ...]}
        self.today = date.today()
        self.current_year = self.today.year
        self.current_month = self.today.month
        self.selected_date: date | None = self.today

        self._build_ui()
        self._refresh_calendar()
        self._refresh_transaction_list()
        self._refresh_summary()

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        """Create all widgets."""
        # ── Top bar ───────────────────────────────────────────────────────────
        top_bar = tk.Frame(self, bg=COLOR_HEADER, pady=10)
        top_bar.pack(fill="x")

        tk.Label(
            top_bar, text="📒  記帳程式", font=("Arial", 18, "bold"),
            bg=COLOR_HEADER, fg="white"
        ).pack(side="left", padx=20)

        # ── Main area (left=calendar, right=transactions) ──────────────────────
        main = tk.Frame(self, bg=COLOR_BG)
        main.pack(fill="both", expand=True, padx=15, pady=10)

        left = tk.Frame(main, bg=COLOR_BG)
        left.pack(side="left", fill="both", expand=False)

        right = tk.Frame(main, bg=COLOR_BG)
        right.pack(side="left", fill="both", expand=True, padx=(15, 0))

        self._build_calendar_panel(left)
        self._build_transaction_panel(right)
        self._build_summary_bar()

    def _build_calendar_panel(self, parent):
        """Build the monthly calendar view."""
        # Navigation header
        nav = tk.Frame(parent, bg=COLOR_BG)
        nav.pack(fill="x", pady=(0, 5))

        tk.Button(
            nav, text="◀", command=self._prev_month,
            bg=COLOR_PRIMARY, fg="white", relief="flat",
            font=("Arial", 11, "bold"), width=3, cursor="hand2"
        ).pack(side="left")

        self.month_label = tk.Label(
            nav, text="", font=("Arial", 13, "bold"),
            bg=COLOR_BG, fg=COLOR_HEADER, width=16
        )
        self.month_label.pack(side="left", expand=True)

        tk.Button(
            nav, text="▶", command=self._next_month,
            bg=COLOR_PRIMARY, fg="white", relief="flat",
            font=("Arial", 11, "bold"), width=3, cursor="hand2"
        ).pack(side="right")

        # Weekday headers
        header = tk.Frame(parent, bg=COLOR_BG)
        header.pack(fill="x")
        for i, day in enumerate(WEEKDAYS):
            color = COLOR_EXPENSE if i >= 5 else COLOR_HEADER
            tk.Label(
                header, text=day, font=("Arial", 10, "bold"),
                bg=COLOR_BG, fg=color, width=4, anchor="center"
            ).grid(row=0, column=i)

        # Calendar grid (6 rows × 7 cols)
        self.cal_frame = tk.Frame(parent, bg=COLOR_BG)
        self.cal_frame.pack(fill="both")
        self.day_buttons: list[tk.Button] = []

    def _build_transaction_panel(self, parent):
        """Build the transaction list + action buttons for selected date."""
        self.trans_title = tk.Label(
            parent, text="", font=("Arial", 12, "bold"),
            bg=COLOR_BG, fg=COLOR_HEADER, anchor="w"
        )
        self.trans_title.pack(fill="x", pady=(0, 6))

        # Treeview
        cols = ("type", "category", "amount", "note")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", height=14)
        self.tree.heading("type", text="類型")
        self.tree.heading("category", text="分類")
        self.tree.heading("amount", text="金額")
        self.tree.heading("note", text="備註")
        self.tree.column("type", width=55, anchor="center")
        self.tree.column("category", width=90, anchor="center")
        self.tree.column("amount", width=90, anchor="e")
        self.tree.column("note", width=200, anchor="w")

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="left", fill="y")

        # Style tags
        self.tree.tag_configure("income", foreground=COLOR_INCOME)
        self.tree.tag_configure("expense", foreground=COLOR_EXPENSE)

        # Action buttons (packed to the right of the tree)
        btn_frame = tk.Frame(parent, bg=COLOR_BG)
        btn_frame.pack(side="left", fill="y", padx=(8, 0))

        for text, cmd, color in [
            ("➕ 新增", self._add_transaction, COLOR_BTN_ADD),
            ("✏️ 編輯", self._edit_transaction, COLOR_BTN_EDIT),
            ("🗑 刪除", self._delete_transaction, COLOR_BTN_DEL),
        ]:
            tk.Button(
                btn_frame, text=text, command=cmd,
                bg=color, fg="white", relief="flat",
                font=("Arial", 10, "bold"), width=10,
                pady=6, cursor="hand2"
            ).pack(pady=5)

    def _build_summary_bar(self):
        """Build monthly summary bar at the bottom."""
        bar = tk.Frame(self, bg=COLOR_HEADER, pady=8)
        bar.pack(fill="x", side="bottom")

        self.lbl_income = tk.Label(
            bar, text="", font=("Arial", 11), bg=COLOR_HEADER, fg="#2ECC71"
        )
        self.lbl_income.pack(side="left", padx=30)

        self.lbl_expense = tk.Label(
            bar, text="", font=("Arial", 11), bg=COLOR_HEADER, fg="#E74C3C"
        )
        self.lbl_expense.pack(side="left", padx=30)

        self.lbl_balance = tk.Label(
            bar, text="", font=("Arial", 11, "bold"), bg=COLOR_HEADER, fg="white"
        )
        self.lbl_balance.pack(side="left", padx=30)

    # ── Calendar rendering ─────────────────────────────────────────────────────

    def _refresh_calendar(self):
        """Redraw the calendar grid for the current month/year."""
        year, month = self.current_year, self.current_month
        self.month_label.config(text=f"{year} 年 {month:02d} 月")

        # Remove old buttons
        for widget in self.cal_frame.winfo_children():
            widget.destroy()
        self.day_buttons.clear()

        cal = calendar.monthcalendar(year, month)
        today_str = self.today.isoformat()

        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0:
                    lbl = tk.Label(self.cal_frame, text="", bg=COLOR_BG, width=4, height=2)
                    lbl.grid(row=r, column=c, padx=1, pady=1)
                    continue

                d = date(year, month, day)
                date_str = d.isoformat()

                has_trans = date_str in self.data and len(self.data[date_str]) > 0
                is_today = date_str == today_str
                is_selected = (self.selected_date and d == self.selected_date)

                if is_selected:
                    bg = COLOR_SELECTED
                elif is_today:
                    bg = COLOR_TODAY
                elif has_trans:
                    bg = COLOR_HAS_TRANS
                else:
                    bg = "white"

                fg = COLOR_EXPENSE if c >= 5 else COLOR_HEADER
                font_style = ("Arial", 10, "bold") if is_today else ("Arial", 10)

                btn = tk.Button(
                    self.cal_frame, text=str(day),
                    bg=bg, fg=fg, font=font_style,
                    relief="flat", width=4, height=2,
                    cursor="hand2",
                    command=lambda _d=d: self._select_date(_d)
                )
                # Show dot indicator if transactions exist
                if has_trans:
                    btn.config(text=f"{day}\n●")

                btn.grid(row=r, column=c, padx=1, pady=1)
                self.day_buttons.append(btn)

    # ── Transaction list ───────────────────────────────────────────────────────

    def _refresh_transaction_list(self):
        """Reload the Treeview for the selected date."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        if self.selected_date is None:
            self.trans_title.config(text="請選擇日期")
            return

        date_str = self.selected_date.isoformat()
        transactions = self.data.get(date_str, [])
        self.trans_title.config(
            text=f"📅  {self.selected_date.strftime('%Y 年 %m 月 %d 日')}  共 {len(transactions)} 筆"
        )

        for i, t in enumerate(transactions):
            amount_str = f"{'＋' if t['type'] == 'income' else '－'} {t['amount']:,.0f}"
            tag = t["type"]
            self.tree.insert(
                "", "end", iid=str(i),
                values=(
                    "收入" if t["type"] == "income" else "支出",
                    t.get("category", ""),
                    amount_str,
                    t.get("note", ""),
                ),
                tags=(tag,),
            )

    # ── Monthly summary ────────────────────────────────────────────────────────

    def _refresh_summary(self):
        """Update the bottom summary bar for the current month."""
        year, month = self.current_year, self.current_month
        income_total = 0.0
        expense_total = 0.0

        for date_str, transactions in self.data.items():
            try:
                d = date.fromisoformat(date_str)
            except ValueError:
                continue
            if d.year == year and d.month == month:
                for t in transactions:
                    if t["type"] == "income":
                        income_total += t["amount"]
                    else:
                        expense_total += t["amount"]

        balance = income_total - expense_total
        balance_color = "#2ECC71" if balance >= 0 else "#E74C3C"

        self.lbl_income.config(text=f"本月收入：＋ {income_total:,.0f} 元")
        self.lbl_expense.config(text=f"本月支出：－ {expense_total:,.0f} 元")
        self.lbl_balance.config(
            text=f"結餘：{'＋' if balance >= 0 else '－'} {abs(balance):,.0f} 元",
            fg=balance_color
        )

    # ── Event handlers ─────────────────────────────────────────────────────────

    def _select_date(self, d: date):
        self.selected_date = d
        self._refresh_calendar()
        self._refresh_transaction_list()

    def _prev_month(self):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._refresh_calendar()
        self._refresh_summary()

    def _next_month(self):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._refresh_calendar()
        self._refresh_summary()

    # ── CRUD dialogs ───────────────────────────────────────────────────────────

    def _add_transaction(self):
        if self.selected_date is None:
            messagebox.showwarning("提示", "請先在日曆上選擇一個日期")
            return
        dialog = TransactionDialog(self, title="新增記帳")
        if dialog.result:
            date_str = self.selected_date.isoformat()
            self.data.setdefault(date_str, []).append(dialog.result)
            save_data(self.data)
            self._refresh_calendar()
            self._refresh_transaction_list()
            self._refresh_summary()

    def _edit_transaction(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "請先選擇要編輯的記帳記錄")
            return
        idx = int(selected[0])
        date_str = self.selected_date.isoformat()
        original = self.data[date_str][idx]

        dialog = TransactionDialog(self, title="編輯記帳", initial=original)
        if dialog.result:
            self.data[date_str][idx] = dialog.result
            save_data(self.data)
            self._refresh_calendar()
            self._refresh_transaction_list()
            self._refresh_summary()

    def _delete_transaction(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "請先選擇要刪除的記帳記錄")
            return
        if not messagebox.askyesno("確認刪除", "確定要刪除這筆記帳記錄嗎？"):
            return
        idx = int(selected[0])
        date_str = self.selected_date.isoformat()
        self.data[date_str].pop(idx)
        if not self.data[date_str]:
            del self.data[date_str]
        save_data(self.data)
        self._refresh_calendar()
        self._refresh_transaction_list()
        self._refresh_summary()


# ── Transaction Dialog ─────────────────────────────────────────────────────────
class TransactionDialog(tk.Toplevel):
    """Modal dialog for adding / editing a transaction."""

    def __init__(self, parent, title: str, initial: dict | None = None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=COLOR_BG, padx=20, pady=20)

        self.result: dict | None = None
        initial = initial or {}

        # ── Type ──────────────────────────────────────────────────────────────
        tk.Label(self, text="類型", bg=COLOR_BG, font=("Arial", 10)).grid(
            row=0, column=0, sticky="w", pady=5)
        self.type_var = tk.StringVar(value=initial.get("type", "expense"))
        type_frame = tk.Frame(self, bg=COLOR_BG)
        type_frame.grid(row=0, column=1, sticky="w")
        tk.Radiobutton(
            type_frame, text="支出", variable=self.type_var, value="expense",
            bg=COLOR_BG, fg=COLOR_EXPENSE, font=("Arial", 10),
            command=self._update_categories
        ).pack(side="left")
        tk.Radiobutton(
            type_frame, text="收入", variable=self.type_var, value="income",
            bg=COLOR_BG, fg=COLOR_INCOME, font=("Arial", 10),
            command=self._update_categories
        ).pack(side="left")

        # ── Category ──────────────────────────────────────────────────────────
        tk.Label(self, text="分類", bg=COLOR_BG, font=("Arial", 10)).grid(
            row=1, column=0, sticky="w", pady=5)
        self.category_var = tk.StringVar(value=initial.get("category", EXPENSE_CATEGORIES[0]))
        self.category_combo = ttk.Combobox(
            self, textvariable=self.category_var, width=18, state="readonly"
        )
        self.category_combo.grid(row=1, column=1, sticky="w")
        self._update_categories()
        if initial.get("category"):
            self.category_var.set(initial["category"])

        # ── Amount ────────────────────────────────────────────────────────────
        tk.Label(self, text="金額", bg=COLOR_BG, font=("Arial", 10)).grid(
            row=2, column=0, sticky="w", pady=5)
        self.amount_var = tk.StringVar(value=str(initial.get("amount", "")))
        tk.Entry(self, textvariable=self.amount_var, width=20).grid(
            row=2, column=1, sticky="w")

        # ── Note ──────────────────────────────────────────────────────────────
        tk.Label(self, text="備註", bg=COLOR_BG, font=("Arial", 10)).grid(
            row=3, column=0, sticky="w", pady=5)
        self.note_var = tk.StringVar(value=initial.get("note", ""))
        tk.Entry(self, textvariable=self.note_var, width=20).grid(
            row=3, column=1, sticky="w")

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_frame = tk.Frame(self, bg=COLOR_BG)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(15, 0))
        tk.Button(
            btn_frame, text="確認", command=self._confirm,
            bg=COLOR_PRIMARY, fg="white", relief="flat",
            font=("Arial", 10, "bold"), width=8, cursor="hand2"
        ).pack(side="left", padx=5)
        tk.Button(
            btn_frame, text="取消", command=self.destroy,
            bg="#95A5A6", fg="white", relief="flat",
            font=("Arial", 10, "bold"), width=8, cursor="hand2"
        ).pack(side="left", padx=5)

        # Centre the dialog relative to parent
        self.update_idletasks()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        dw, dh = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px + (pw - dw) // 2}+{py + (ph - dh) // 2}")
        self.wait_window()

    def _update_categories(self):
        cats = INCOME_CATEGORIES if self.type_var.get() == "income" else EXPENSE_CATEGORIES
        self.category_combo["values"] = cats
        if self.category_var.get() not in cats:
            self.category_var.set(cats[0])

    def _confirm(self):
        raw = self.amount_var.get().strip()
        try:
            amount = float(raw)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("輸入錯誤", "請輸入有效的正數金額", parent=self)
            return
        self.result = {
            "type": self.type_var.get(),
            "category": self.category_var.get(),
            "amount": amount,
            "note": self.note_var.get().strip(),
        }
        self.destroy()


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = AccountingApp()
    app.mainloop()
