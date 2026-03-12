# 記帳程式 💰

A personal finance tracker (記帳程式) built with Python and tkinter, featuring a **calendar view** for daily transaction summaries.

## Features

- **📅 Calendar View** — Monthly calendar highlighting days with income (green), expense (red), or both (blue)
- **➕ Add Transactions** — Record income or expenses with date, amount, category, and notes
- **✏️ Edit / 🗑️ Delete** — Manage existing transactions
- **📊 Monthly Summary** — See total income, expenses, and balance for the displayed month
- **🔍 Filter** — Filter the list by All / Income / Expense
- **Click a day** — Click any calendar cell to view transactions for that day
- **💾 Persistent Storage** — All data is saved to `accounting_data.json` in the same folder

## Requirements

- Python 3.10+
- `tkinter` (included with standard Python; on Linux install `python3-tk`)

## Running

```bash
python accounting.py
```

## Categories

| Income (收入)          | Expense (支出)                     |
|------------------------|------------------------------------|
| 薪資, 兼職, 投資, 獎金, 其他收入 | 餐飲, 交通, 購物, 娛樂, 醫療, 教育, 住房, 水電, 其他支出 |

## Data Storage

Transactions are stored in `accounting_data.json` next to `accounting.py`.
Each record contains: `type`, `date`, `amount`, `category`, `note`.