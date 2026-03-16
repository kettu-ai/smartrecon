# SmartRecon 🧾

**AI-powered expense reconciliation for small businesses.**

Match your invoices and receipts against your bank statement, auto-categorize every expense, and know exactly who paid what — in minutes, not days.

---

## What it does

- **Ingests** any PDF invoice, receipt, or bank statement — scanned or digital
- **Extracts** amounts, dates, and vendors using local OCR (no API limits, no file size cap)
- **Matches** each expense to a bank statement debit
- **Categorizes** automatically: Telecom, Travel, Food & Drink, Software, Office, Insurance, and more
- **Flags** expenses not found in the bank account — these were paid personally and should be reimbursed or deducted from a balance owed
- **Reports** a clean categorized summary ready for your accountant

---

## Why SmartRecon

| | Manual | Typical SaaS ($299+/mo) | SmartRecon |
|--|--------|------------------------|------------|
| Cost | Free (your time) | €299–€599/mo | Free tier + Pro |
| Speed | Hours/days | Minutes | Minutes |
| Privacy | ✓ | ✗ (cloud upload) | ✓ (runs locally) |
| File size limit | — | Usually 10MB | None |
| Works offline | ✓ | ✗ | ✓ |
| Multi-language | Manual | EN only | EN, FR, NL, ES |

---

## Requirements

- OpenClaw 2026.1.0+
- `pdftotext` and `tesseract` installed locally:

```bash
# Ubuntu/Debian
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-fra tesseract-ocr-nld tesseract-ocr-spa

# macOS
brew install poppler tesseract tesseract-lang
```

---

## Installation

```bash
openclaw skill install smartrecon
```

---

## Usage

Just talk to your agent naturally:

> "Reconcile my 2025 AcmeX expenses — the invoices are in ~/Documents/acmex-2025/ and the bank statement is bank_statement.pdf"

> "Which expenses did I pay personally last quarter?"

> "Prepare my accounts for the accountant — match everything to the bank statement"

SmartRecon will:
1. Process all PDFs in the folder
2. Parse the bank statement
3. Match and categorize every expense
4. Ask you one-by-one about anything it couldn't read
5. Deliver a full reconciliation report

---

## Output example

```
EXPENSE RECONCILIATION — ACMEX SRL 2025
=========================================
Total invoices:         164
Matched (bank paid):     49 items  =  €3,842.50
Unmatched (personal):   115 items  =  €4,217.30
Needs review:             0 items

BY CATEGORY:
  Software & Subscriptions   21 items  €1,578.27
  Food & Drink               12 items  €  892.40
  Travel                      8 items  €  643.20
  Telecom                     4 items  €  428.63
  Office & Supplies           4 items  €  300.00

PERSONAL EXPENSES — deduct from balance:
  2025-03-14  Apple TV subscription    €9.99
  2025-04-22  LinkedIn Premium        €39.99
  ...

Total Tom owes AcmeX: €4,217.30
```

---

## Supported banks

Tested: **KBC** (Belgium)

Should work: ING, BNP Paribas Fortis, Belfius, Revolut, N26, any bank that exports a readable PDF statement.

---

## 🎯 Limited Time Offer — Done For You

**We'll reconcile your full year of expenses for you. One flat fee. Delivered in 48h.**

Too busy to set this up yourself? Send us your invoices and bank statement and we'll run the full reconciliation, clean up the edge cases, and hand you a report your accountant can use immediately.

| | |
|--|--|
| **What you send** | A folder of PDF invoices/receipts + your bank statement |
| **What you get** | Full categorized report, matched/unmatched breakdown, total owed per person |
| **Turnaround** | 48 hours |
| **Price** | ~~€299~~ **€149 — first 20 clients only** |

📩 **[Book your slot → hello@smartrecon.io](mailto:hello@smartrecon.io)**

*(Only 20 spots available at this price. Once they're gone, the price goes up.)*

---

## Pricing

| Plan | Price | Includes |
|------|-------|---------|
| **Free** | €0 | 50 invoices/month, basic categorization |
| **Pro** | €19/mo | Unlimited invoices, QuickBooks/Xero export, priority support |
| **Team** | €49/mo | Everything in Pro + multi-company, accountant sharing portal |

Get your API key at **[smartrecon.io](https://smartrecon.io)**

---

## Privacy

All processing happens **locally on your machine**. No documents are uploaded to any external service. OCR runs via Tesseract, not a cloud API.

---

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Issues: [github.com/kettu-ai/smartrecon/issues](https://github.com/kettu-ai/smartrecon/issues)

---

## License

MIT
