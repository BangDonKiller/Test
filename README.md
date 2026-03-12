# 📒 記帳程式

一個支援**桌面版（Tkinter）**與**網頁版（Flask）**的記帳應用程式，內建月曆功能，可依日期查看、新增、編輯和刪除收支記錄。網頁版完整支援手機與平板瀏覽。

## 功能特色

- **月曆視圖** — 以月份瀏覽，有記帳的日期會顯示標記（●）
- **收支管理** — 支援「收入」與「支出」兩種類型，各有預設分類
- **新增 / 編輯 / 刪除** — 每一筆記錄包含類型、分類、金額、備註
- **月份摘要** — 頁面底部即時顯示本月總收入、總支出及結餘
- **資料持久化** — 自動儲存至 `transactions.json`，重新開啟後資料不流失
- **響應式設計（網頁版）** — 自動適應手機、平板與桌機螢幕

## 網頁版截圖

| 桌面版 | 手機版 |
|--------|--------|
| ![desktop](https://github.com/user-attachments/assets/a1d0d6f6-4435-4019-96b1-f3ab6a690fa0) | ![mobile](https://github.com/user-attachments/assets/ba13919b-d452-4198-82d4-a4325b446391) |

---

## 🌐 網頁版（Flask）

### 系統需求

| 項目 | 版本 |
|------|------|
| Python | 3.8 以上 |
| Flask | 3.0 以上 |

### 安裝與執行

```bash
# 1. 安裝依賴套件
pip install -r requirements.txt

# 2. 啟動伺服器
python app.py
```

伺服器預設只監聽本機 `http://127.0.0.1:5000`，以瀏覽器開啟即可使用。若需對外提供服務，可設定環境變數 `FLASK_HOST=0.0.0.0`。

### 目錄結構

```
├── app.py              # Flask 後端（REST API）
├── requirements.txt    # Python 依賴套件
├── transactions.json   # 資料儲存檔（自動建立）
├── templates/
│   └── index.html      # 單頁面應用程式
└── static/
    ├── css/style.css   # 響應式樣式
    └── js/app.js       # 前端邏輯
```

### REST API 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| GET | `/` | 網頁首頁 |
| GET | `/api/transactions` | 取得所有交易記錄 |
| GET | `/api/transactions/month/{year}/{month}` | 取得指定月份摘要與標記日 |
| GET | `/api/transactions/{date}` | 取得指定日期的交易記錄 |
| POST | `/api/transactions/{date}` | 新增交易記錄 |
| PUT | `/api/transactions/{date}/{index}` | 修改交易記錄 |
| DELETE | `/api/transactions/{date}/{index}` | 刪除交易記錄 |

---

## 🖥️ 桌面版（Tkinter）

### 系統需求

| 項目 | 版本 |
|------|------|
| Python | 3.8 以上 |
| Tkinter | 內建於標準 Python（Windows / macOS 預設已包含）|

> **Linux 使用者**：若 Tkinter 未安裝，請執行：
> ```bash
> sudo apt install python3-tk   # Debian / Ubuntu
> sudo dnf install python3-tkinter  # Fedora
> ```

### 安裝與執行

```bash
# 複製或下載此儲存庫後，直接執行
python accounting.py
```

不需要額外安裝第三方套件，僅使用 Python 標準函式庫。

---

## 操作說明

1. **選擇日期** — 點擊月曆上任意日期
2. **切換月份** — 點擊 ◀ / ▶ 按鈕切換上 / 下個月
3. **新增記錄** — 選好日期後點擊「➕ 新增」，填入資訊後確認
4. **編輯記錄** — 選取一筆記錄後點擊「✏️」（網頁版）或「✏️ 編輯」（桌面版）
5. **刪除記錄** — 選取一筆記錄後點擊「🗑」（網頁版）或「🗑 刪除」（桌面版）

## 資料格式

資料以 JSON 格式儲存於 `transactions.json`，結構如下：

```json
{
  "2025-03-12": [
    {
      "type": "expense",
      "category": "餐飲",
      "amount": 150.0,
      "note": "午餐便當"
    }
  ]
}
```

## 預設分類

| 收入 | 支出 |
|------|------|
| 薪資 | 餐飲 |
| 獎金 | 交通 |
| 投資收益 | 娛樂 |
| 其他收入 | 購物、醫療、教育、住房、其他支出 |
