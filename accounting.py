"""
記帳程式 - Python Accounting Program with Calendar
A personal finance tracker with calendar view built using tkinter.
"""

import json
import os
import calendar
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import date, datetime
from collections import defaultdict


DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "accounting_data.json")

CATEGORIES_INCOME = ["薪資", "兼職", "投資", "獎金", "其他收入"]
CATEGORIES_EXPENSE = ["餐飲", "交通", "購物", "娛樂", "醫療", "教育", "住房", "水電", "其他支出"]


# ---------------------------------------------------------------------------
# Data Layer
# ---------------------------------------------------------------------------

def load_data() -> list[dict]:
    """Load transactions from JSON file."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []
    return []


def save_data(transactions: list[dict]) -> None:
    """Save transactions to JSON file."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(transactions, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Transaction Dialog
# ---------------------------------------------------------------------------

class TransactionDialog(tk.Toplevel):
    """Dialog for adding or editing a transaction."""

    def __init__(self, parent, title: str = "新增記錄", transaction: dict | None = None,
                 preset_date: str | None = None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result: dict | None = None
        self.grab_set()

        today = date.today().isoformat()
        t = transaction or {}

        # ---- Type ----
        tk.Label(self, text="類型:", anchor="w").grid(row=0, column=0, padx=10, pady=6, sticky="w")
        self.type_var = tk.StringVar(value=t.get("type", "支出"))
        type_frame = tk.Frame(self)
        type_frame.grid(row=0, column=1, padx=10, pady=6, sticky="w")
        tk.Radiobutton(type_frame, text="收入", variable=self.type_var, value="收入",
                       command=self._update_categories).pack(side="left")
        tk.Radiobutton(type_frame, text="支出", variable=self.type_var, value="支出",
                       command=self._update_categories).pack(side="left")

        # ---- Date ----
        tk.Label(self, text="日期 (YYYY-MM-DD):", anchor="w").grid(row=1, column=0, padx=10, pady=6, sticky="w")
        self.date_var = tk.StringVar(value=t.get("date", preset_date or today))
        tk.Entry(self, textvariable=self.date_var, width=15).grid(row=1, column=1, padx=10, pady=6, sticky="w")

        # ---- Amount ----
        tk.Label(self, text="金額 (NT$):", anchor="w").grid(row=2, column=0, padx=10, pady=6, sticky="w")
        self.amount_var = tk.StringVar(value=str(t.get("amount", "")))
        tk.Entry(self, textvariable=self.amount_var, width=15).grid(row=2, column=1, padx=10, pady=6, sticky="w")

        # ---- Category ----
        tk.Label(self, text="分類:", anchor="w").grid(row=3, column=0, padx=10, pady=6, sticky="w")
        self.category_var = tk.StringVar(value=t.get("category", CATEGORIES_EXPENSE[0]))
        self.category_combo = ttk.Combobox(self, textvariable=self.category_var, state="readonly", width=13)
        self.category_combo.grid(row=3, column=1, padx=10, pady=6, sticky="w")
        self._update_categories()
        if t.get("category"):
            self.category_var.set(t["category"])

        # ---- Note ----
        tk.Label(self, text="備註:", anchor="w").grid(row=4, column=0, padx=10, pady=6, sticky="w")
        self.note_var = tk.StringVar(value=t.get("note", ""))
        tk.Entry(self, textvariable=self.note_var, width=25).grid(row=4, column=1, padx=10, pady=6, sticky="w")

        # ---- Buttons ----
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        tk.Button(btn_frame, text="確認", width=8, command=self._confirm).pack(side="left", padx=8)
        tk.Button(btn_frame, text="取消", width=8, command=self.destroy).pack(side="left", padx=8)

        self.transient(parent)
        self.wait_window(self)

    def _update_categories(self):
        if self.type_var.get() == "收入":
            self.category_combo["values"] = CATEGORIES_INCOME
            if self.category_var.get() not in CATEGORIES_INCOME:
                self.category_var.set(CATEGORIES_INCOME[0])
        else:
            self.category_combo["values"] = CATEGORIES_EXPENSE
            if self.category_var.get() not in CATEGORIES_EXPENSE:
                self.category_var.set(CATEGORIES_EXPENSE[0])

    def _confirm(self):
        # Validate date
        date_str = self.date_var.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("錯誤", "日期格式錯誤，請輸入 YYYY-MM-DD", parent=self)
            return

        # Validate amount
        amount_str = self.amount_var.get().strip()
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的正數金額", parent=self)
            return

        self.result = {
            "type": self.type_var.get(),
            "date": date_str,
            "amount": amount,
            "category": self.category_var.get(),
            "note": self.note_var.get().strip(),
        }
        self.destroy()


# ---------------------------------------------------------------------------
# Calendar Frame
# ---------------------------------------------------------------------------

class CalendarFrame(tk.Frame):
    """Monthly calendar widget that highlights days with transactions."""

    DAY_NAMES = ["一", "二", "三", "四", "五", "六", "日"]

    def __init__(self, parent, on_day_click=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_day_click = on_day_click
        today = date.today()
        self._year = today.year
        self._month = today.month
        self._daily_totals: dict[str, dict] = {}

        self._build_header()
        self._build_grid()
        self.refresh()

    # ---- public ----

    def set_daily_totals(self, totals: dict[str, dict[str, float]]):
        """Update daily totals and redraw."""
        self._daily_totals = totals
        self.refresh()

    def get_ym(self) -> tuple[int, int]:
        return self._year, self._month

    # ---- private ----

    def _build_header(self):
        nav = tk.Frame(self)
        nav.pack(fill="x", padx=4, pady=4)
        tk.Button(nav, text="◀", width=3, command=self._prev_month).pack(side="left")
        self._title_var = tk.StringVar()
        tk.Label(nav, textvariable=self._title_var, font=("Arial", 13, "bold"), width=14).pack(side="left", expand=True)
        tk.Button(nav, text="▶", width=3, command=self._next_month).pack(side="right")

        day_hdr = tk.Frame(self)
        day_hdr.pack(fill="x", padx=4)
        for d in self.DAY_NAMES:
            color = "#c0392b" if d == "日" else ("#2980b9" if d == "六" else "black")
            tk.Label(day_hdr, text=d, width=6, font=("Arial", 9, "bold"), fg=color).pack(side="left")

    def _build_grid(self):
        self._grid_frame = tk.Frame(self)
        self._grid_frame.pack(fill="both", expand=True, padx=4)

    def _prev_month(self):
        if self._month == 1:
            self._year -= 1
            self._month = 12
        else:
            self._month -= 1
        self.refresh()

    def _next_month(self):
        if self._month == 12:
            self._year += 1
            self._month = 1
        else:
            self._month += 1
        self.refresh()

    def refresh(self):
        self._title_var.set(f"{self._year} 年 {self._month:02d} 月")

        # Clear previous grid
        for w in self._grid_frame.winfo_children():
            w.destroy()

        today = date.today()
        cal = calendar.monthcalendar(self._year, self._month)

        for week in cal:
            row = tk.Frame(self._grid_frame)
            row.pack(fill="x")
            for day_idx, day in enumerate(week):
                if day == 0:
                    tk.Label(row, text="", width=6, height=3).pack(side="left")
                    continue

                day_str = f"{self._year}-{self._month:02d}-{day:02d}"
                totals = self._daily_totals.get(day_str, {})
                income = totals.get("income", 0)
                expense = totals.get("expense", 0)

                # Background colour
                is_today = (self._year == today.year and self._month == today.month and day == today.day)
                bg = "#fffacd" if is_today else ("#e8f5e9" if income > 0 and expense == 0
                                                  else "#fce4ec" if expense > 0 and income == 0
                                                  else "#e3f2fd" if income > 0 or expense > 0
                                                  else "#f5f5f5")

                cell = tk.Frame(self._grid_frame, bg=bg, bd=1, relief="groove",
                                width=70, height=58)
                cell.pack_propagate(False)
                cell.pack(side="left", padx=1, pady=1)

                tk.Label(cell, text=str(day), bg=bg,
                         fg="#c0392b" if day_idx == 6 else "#2980b9" if day_idx == 5 else "black",
                         font=("Arial", 9, "bold")).pack(anchor="nw")

                if income > 0:
                    tk.Label(cell, text=f"+{income:,.0f}", bg=bg, fg="#27ae60",
                             font=("Arial", 7)).pack(anchor="w")
                if expense > 0:
                    tk.Label(cell, text=f"-{expense:,.0f}", bg=bg, fg="#e74c3c",
                             font=("Arial", 7)).pack(anchor="w")

                # Bind click
                for w in [cell] + cell.winfo_children():
                    w.bind("<Button-1>", lambda e, d=day_str: self._on_click(d))
                    w.bind("<Enter>", lambda e, c=cell: c.config(cursor="hand2"))

    def _on_click(self, day_str: str):
        if self.on_day_click:
            self.on_day_click(day_str)


# ---------------------------------------------------------------------------
# Main Application
# ---------------------------------------------------------------------------

class AccountingApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("記帳程式 💰")
        self.geometry("1100x680")
        self.minsize(900, 580)
        self.configure(bg="#ecf0f1")

        self.transactions: list[dict] = load_data()
        self._selected_date: str | None = None

        self._build_ui()
        self._refresh_all()

    # ---- UI Construction ----

    def _build_ui(self):
        # Top toolbar
        toolbar = tk.Frame(self, bg="#2c3e50", pady=6)
        toolbar.pack(fill="x")
        tk.Label(toolbar, text="💰 個人記帳程式", bg="#2c3e50", fg="white",
                 font=("Arial", 16, "bold")).pack(side="left", padx=16)
        tk.Button(toolbar, text="＋ 新增記錄", bg="#27ae60", fg="white",
                  font=("Arial", 11, "bold"), relief="flat", padx=10,
                  command=self._add_transaction).pack(side="right", padx=8)

        # Main layout: left calendar, right panel
        main = tk.Frame(self, bg="#ecf0f1")
        main.pack(fill="both", expand=True, padx=10, pady=8)

        # Left: calendar
        left = tk.Frame(main, bg="white", bd=1, relief="solid")
        left.pack(side="left", fill="y", padx=(0, 6))

        self.calendar = CalendarFrame(left, on_day_click=self._on_day_click,
                                      bg="white")
        self.calendar.pack(fill="both", expand=True)

        # Monthly summary below calendar
        self.summary_frame = tk.Frame(left, bg="white", pady=6)
        self.summary_frame.pack(fill="x", padx=8, pady=(0, 8))
        self._income_lbl = tk.Label(self.summary_frame, text="", bg="white",
                                    fg="#27ae60", font=("Arial", 10, "bold"))
        self._income_lbl.pack(anchor="w")
        self._expense_lbl = tk.Label(self.summary_frame, text="", bg="white",
                                     fg="#e74c3c", font=("Arial", 10, "bold"))
        self._expense_lbl.pack(anchor="w")
        self._balance_lbl = tk.Label(self.summary_frame, text="", bg="white",
                                     font=("Arial", 10, "bold"))
        self._balance_lbl.pack(anchor="w")

        # Right: transaction list
        right = tk.Frame(main, bg="white", bd=1, relief="solid")
        right.pack(side="left", fill="both", expand=True)

        # Right header
        right_hdr = tk.Frame(right, bg="#34495e", pady=5)
        right_hdr.pack(fill="x")
        self._list_title = tk.Label(right_hdr, text="所有記錄", bg="#34495e", fg="white",
                                    font=("Arial", 11, "bold"))
        self._list_title.pack(side="left", padx=10)
        tk.Button(right_hdr, text="顯示全部", bg="#7f8c8d", fg="white",
                  relief="flat", command=self._show_all).pack(side="right", padx=8)

        # Filter row
        filter_row = tk.Frame(right, bg="#f0f0f0", pady=4)
        filter_row.pack(fill="x")
        tk.Label(filter_row, text="篩選類型:", bg="#f0f0f0").pack(side="left", padx=8)
        self._filter_var = tk.StringVar(value="全部")
        for v in ["全部", "收入", "支出"]:
            tk.Radiobutton(filter_row, text=v, variable=self._filter_var, value=v,
                           bg="#f0f0f0", command=self._apply_filter).pack(side="left")

        # Treeview
        cols = ("date", "type", "category", "amount", "note")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("date", text="日期")
        self.tree.heading("type", text="類型")
        self.tree.heading("category", text="分類")
        self.tree.heading("amount", text="金額 (NT$)")
        self.tree.heading("note", text="備註")
        self.tree.column("date", width=100, anchor="center")
        self.tree.column("type", width=60, anchor="center")
        self.tree.column("category", width=90, anchor="center")
        self.tree.column("amount", width=110, anchor="e")
        self.tree.column("note", width=200)

        self.tree.tag_configure("income", foreground="#27ae60")
        self.tree.tag_configure("expense", foreground="#e74c3c")

        vsb = ttk.Scrollbar(right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        vsb.pack(side="right", fill="y", pady=4, padx=(0, 4))

        # Bottom action buttons
        btn_bar = tk.Frame(right, bg="white", pady=6)
        btn_bar.pack(fill="x", padx=8)
        tk.Button(btn_bar, text="✏️ 編輯", width=10, command=self._edit_transaction).pack(side="left", padx=4)
        tk.Button(btn_bar, text="🗑️ 刪除", width=10, command=self._delete_transaction).pack(side="left", padx=4)

        self.tree.bind("<Double-1>", lambda e: self._edit_transaction())

    # ---- Data Helpers ----

    def _compute_daily_totals(self, year: int, month: int) -> dict[str, dict[str, float]]:
        totals: dict[str, dict[str, float]] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
        prefix = f"{year}-{month:02d}-"
        for t in self.transactions:
            if t["date"].startswith(prefix):
                if t["type"] == "收入":
                    totals[t["date"]]["income"] += t["amount"]
                else:
                    totals[t["date"]]["expense"] += t["amount"]
        return dict(totals)

    def _compute_monthly_summary(self, year: int, month: int) -> tuple[float, float]:
        prefix = f"{year}-{month:02d}-"
        income = sum(t["amount"] for t in self.transactions
                     if t["date"].startswith(prefix) and t["type"] == "收入")
        expense = sum(t["amount"] for t in self.transactions
                      if t["date"].startswith(prefix) and t["type"] == "支出")
        return income, expense

    # ---- UI Refresh ----

    def _refresh_calendar(self):
        y, m = self.calendar.get_ym()
        totals = self._compute_daily_totals(y, m)
        self.calendar.set_daily_totals(totals)

        income, expense = self._compute_monthly_summary(y, m)
        balance = income - expense
        self._income_lbl.config(text=f"本月收入：NT$ {income:,.0f}")
        self._expense_lbl.config(text=f"本月支出：NT$ {expense:,.0f}")
        color = "#27ae60" if balance >= 0 else "#e74c3c"
        self._balance_lbl.config(text=f"本月結餘：NT$ {balance:,.0f}", fg=color)

    def _refresh_list(self, transactions: list[dict] | None = None):
        for row in self.tree.get_children():
            self.tree.delete(row)

        data = transactions if transactions is not None else self.transactions
        ftype = self._filter_var.get()
        if ftype != "全部":
            data = [t for t in data if t["type"] == ftype]

        data = sorted(data, key=lambda t: t["date"], reverse=True)
        for t in data:
            sign = "+" if t["type"] == "收入" else "-"
            tag = "income" if t["type"] == "收入" else "expense"
            self.tree.insert("", "end", values=(
                t["date"], t["type"], t["category"],
                f"{sign}{t['amount']:,.0f}", t.get("note", "")
            ), tags=(tag,))

    def _refresh_all(self):
        self._refresh_calendar()
        if self._selected_date:
            filtered = [t for t in self.transactions if t["date"] == self._selected_date]
            self._refresh_list(filtered)
        else:
            self._refresh_list()

    # ---- Event Handlers ----

    def _on_day_click(self, day_str: str):
        self._selected_date = day_str
        self._list_title.config(text=f"📅 {day_str} 的記錄")
        filtered = [t for t in self.transactions if t["date"] == day_str]
        self._refresh_list(filtered)

    def _show_all(self):
        self._selected_date = None
        self._list_title.config(text="所有記錄")
        self._refresh_list()

    def _apply_filter(self):
        if self._selected_date:
            filtered = [t for t in self.transactions if t["date"] == self._selected_date]
            self._refresh_list(filtered)
        else:
            self._refresh_list()

    def _add_transaction(self):
        dlg = TransactionDialog(self, title="新增記錄",
                                preset_date=self._selected_date)
        if dlg.result:
            self.transactions.append(dlg.result)
            save_data(self.transactions)
            self._refresh_all()

    def _edit_transaction(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "請先選取一筆記錄")
            return
        idx = self.tree.index(sel[0])

        # Rebuild display list to find the original transaction
        ftype = self._filter_var.get()
        source = (
            [t for t in self.transactions if t["date"] == self._selected_date]
            if self._selected_date else list(self.transactions)
        )
        if ftype != "全部":
            source = [t for t in source if t["type"] == ftype]
        source = sorted(source, key=lambda t: t["date"], reverse=True)
        original = source[idx]

        dlg = TransactionDialog(self, title="編輯記錄", transaction=original)
        if dlg.result:
            pos = self.transactions.index(original)
            self.transactions[pos] = dlg.result
            save_data(self.transactions)
            self._refresh_all()

    def _delete_transaction(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "請先選取一筆記錄")
            return
        if not messagebox.askyesno("確認刪除", "確定要刪除這筆記錄嗎？"):
            return

        idx = self.tree.index(sel[0])
        ftype = self._filter_var.get()
        source = (
            [t for t in self.transactions if t["date"] == self._selected_date]
            if self._selected_date else list(self.transactions)
        )
        if ftype != "全部":
            source = [t for t in source if t["type"] == ftype]
        source = sorted(source, key=lambda t: t["date"], reverse=True)
        original = source[idx]

        self.transactions.remove(original)
        save_data(self.transactions)
        self._refresh_all()


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = AccountingApp()
    app.mainloop()
