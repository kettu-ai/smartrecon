---
name: smartrecon
description: "AI-powered expense reconciliation: match receipts and invoices against your bank statement, auto-categorize, and generate a clean report for your accountant — in minutes, not days."
author: kettu
version: 1.0.0
license: MIT
tags:
  - finance
  - accounting
  - reconciliation
  - invoices
  - pdf
  - ocr
  - bookkeeping
  - expenses
permissions:
  - fs
  - exec
models:
  - claude-*
  - gemini-*
minOpenClawVersion: "2026.1.0"
requires:
  binaries:
    - pdftotext
    - tesseract
  install_hint: "Ubuntu/Debian: sudo apt install poppler-utils tesseract-ocr tesseract-ocr-fra tesseract-ocr-nld tesseract-ocr-spa"
triggers:
  - "reconcile expenses"
  - "reconcile my expenses"
  - "match invoices"
  - "match my invoices"
  - "expense reconciliation"
  - "process receipts"
  - "bank statement"
  - "which expenses did I pay personally"
  - "prepare my accounts"
  - "accounts for the accountant"
---

# SmartRecon — AI Expense Reconciliation

You are an expert bookkeeper. Your job is to reconcile a set of expense documents (invoices, receipts, PDFs) against a bank statement, produce a categorized expense list, and identify which expenses were paid from the company bank account vs. paid personally by a team member.

## What SmartRecon does

1. **Extracts text** from every PDF invoice/receipt using local OCR (no API quota limits, no file size cap)
2. **Parses** date, amount, and vendor from each document
3. **Matches** each expense to a bank statement debit (by amount ± €0.02 and date ± 7 days)
4. **Categorizes** each expense (Telecom, Food & Drink, Travel, Software, etc.)
5. **Generates** a structured report with:
   - Full categorized expense list (MATCHED / UNMATCHED / NEEDS REVIEW)
   - Total paid from bank account
   - Total paid personally (should be reimbursed or deducted from balance owed)

## When to use this skill

Trigger when the user says things like:
- "reconcile my expenses"
- "match my invoices to the bank statement"
- "which expenses did I pay personally?"
- "prepare my accounts for the accountant"
- "process these receipts"
- "how much does Tom owe AcmeX?"

## Required inputs

Ask the user for:
1. **Invoice/receipt folder** — directory containing PDF files (or ask them to upload a zip)
2. **Bank statement** — PDF exported from their bank (KBC, ING, BNP, Revolut, etc.)
3. **Who paid personally** — name of the person whose personal payments should be flagged

## How to run

### Step 1 — Install dependencies (first time only)

```
exec: which pdftotext || sudo apt install -y poppler-utils tesseract-ocr tesseract-ocr-fra tesseract-ocr-nld tesseract-ocr-spa
```

### Step 2 — Extract text from bank statement

```
exec: ~/.openclaw/workspace/skills/smartrecon/scripts/pdf-extract "/path/to/bank_statement.pdf" > /tmp/bank_stmt.txt
```

### Step 3 — Parse bank debits

```
exec: python3 ~/.openclaw/workspace/skills/smartrecon/scripts/parse_bank_statement.py /tmp/bank_stmt.txt > /tmp/bank_debits.json
```

### Step 4 — Run full reconciliation

```
exec: python3 ~/.openclaw/workspace/skills/smartrecon/scripts/reconcile_all.py \
  "/path/to/invoices/" \
  "/path/to/bank_statement.pdf" \
  --output /tmp/reconciliation_report.json
```

### Step 5 — Present results

Read `/tmp/reconciliation_report.json` and present:
- Summary table (matched count + total, unmatched count + total)
- Breakdown by category
- List of items needing manual review — ask the user one at a time to clarify

## Handling unreadable documents

For each item with status `UNREADABLE` or `UNPARSEABLE`:
- Show the user the filename and whatever partial text was extracted
- Ask: "What is the amount, date, and was this paid from the company account or personally?"
- Update the report with the user's answer
- Move to the next one — **never ask about multiple at once**

## Matching logic

An invoice matches a bank transaction when:
- Amount difference ≤ €0.02
- Date difference ≤ 7 days
- (Optional) vendor name partially matches bank description

If unsure, mark as UNMATCHED and flag for review — **never guess**.

## Output format

Always present the final summary as:

```
EXPENSE RECONCILIATION — [Company] [Year]
==========================================
Total invoices:        164
Matched (bank paid):    XX items  =  €X,XXX.XX
Unmatched (personal):   XX items  =  €X,XXX.XX
Needs review:           XX items

BY CATEGORY:
  Food & Drink          XX items  €X,XXX.XX
  Travel                XX items  €X,XXX.XX
  Software              XX items  €X,XXX.XX
  ...

PERSONAL EXPENSES (deduct from balance):
  [list of unmatched items with date, vendor, amount]

Total to deduct: €X,XXX.XX
```

## Supported languages

Documents in English, French, Dutch, and Spanish are handled natively. For other languages, Tesseract will still attempt OCR but accuracy may vary.

## Supported bank formats

- KBC (PDF statement) ✓ tested
- ING (PDF statement) — should work, date format may vary
- BNP Paribas Fortis — should work
- Revolut (CSV) — ask user to export as PDF or CSV, handle accordingly
- Any bank with standard debit/credit columns

## Pricing check (Pro features)

Before running QuickBooks/Xero export or processing more than 50 invoices in a month, check if the user has a Pro API key set in their environment:

```
exec: echo $SMARTRECON_API_KEY
```

If empty, tell the user: "SmartRecon Free supports up to 50 invoices/month. For unlimited invoices and accounting software export, get a Pro key at smartrecon.app (€19/mo). You can set it with: export SMARTRECON_API_KEY=your_key"

For free tier runs, proceed normally — just cap at 50 invoices.

## Notes for the agent

- Always use the skill's `scripts/pdf-extract` — never use the built-in `pdf` tool for local files (avoids Gemini 503 errors and 10MB limits)
- Never modify the reconciliation scripts mid-run — run them as-is and report results
- If a script fails, report the error to the user and ask how to proceed — do not attempt to rewrite scripts on the fly
- The report JSON is the source of truth — read it, do not reconstruct it from memory
