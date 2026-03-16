#!/usr/bin/env python3
"""
reconcile_all.py — KETTU SRL 2025 expense reconciliation
Usage: python3 reconcile_all.py <invoices_dir> <bank_statement_pdf> [--output report.json]

For each invoice/receipt PDF:
  1. Extracts text via pdf-extract
  2. Parses date, amount, vendor
  3. Matches against KBC bank statement debits
  4. Categorizes the expense

Outputs:
  - Full categorized expense list (JSON + summary)
  - Total matched (paid by KETTU bank account)
  - Total unmatched (paid by Juan Florez personally)
"""

import os, sys, json, re, subprocess, argparse
from datetime import datetime, timedelta
from pathlib import Path

PDF_EXTRACT = "/home/deploy/bin/pdf-extract"

CATEGORIES = {
    "Telecom":        ["telenet", "proximus", "orange", "voo", "base", "mobile", "internet", "phone"],
    "Insurance":      ["ag insurance", "axa", "ethias", "allianz", "assur", "insurance", "verzeker"],
    "Travel":         ["sncb", "nmbs", "eurostar", "thalys", "tren", "flight", "airline", "airbnb",
                       "booking.com", "hotel", "hostel", "uber", "taxi", "ryanair", "brussels airlines",
                       "iberia", "lufthansa", "transavia", "vueling", "easyjet", "aeromexico"],
    "Food & Drink":   ["restaurant", "cafe", "coffee", "bar ", "drinks", "elia", "alcohol", "food",
                       "supermarkt", "delhaize", "colruyt", "carrefour", "lidl", "aldi", "albert heijn",
                       "spar ", "night shop", "boulangerie", "bakker", "chocolat"],
    "Software & Subscriptions": ["apple", "google", "microsoft", "adobe", "spotify", "netflix",
                                  "amazon", "dropbox", "github", "openai", "anthropic", "claude",
                                  "chatgpt", "notion", "slack", "zoom", "linear"],
    "Office & Supplies": ["brico", "office", "fnac", "ikea", "amazon", "bol.com", "staples",
                           "cleaning", "supplies", "fourniture"],
    "Professional Services": ["accountant", "comptable", "lawyer", "avocat", "notaire", "notary",
                               "consultant", "fiduciaire", "legal", "juridique", "audit"],
    "Utilities":      ["water", "eau", "gas", "electricity", "elec", "energie", "sibelga", "ores",
                       "vivaqua", "fluvius"],
    "Banking & Finance": ["kbc", "bnp", "ing ", "belfius", "argenta", "paypal", "stripe",
                           "commission", "frais bancaire", "bank charge", "swift", "sepa"],
    "Tax & Government": ["spf", "finances", "tva", "vat", "impot", "belasting", "onss", "rsvz",
                          "inasti", "social", "fonds", "pension"],
    "Health":         ["pharmacie", "apotheek", "pharmacy", "medic", "doctor", "dentist", "hopital",
                       "hospital", "kine", "physio", "dafalgan", "health"],
    "Fitness":        ["gym", "sport", "fitness", "yoga", "running", "swimming"],
}

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "janvier": 1, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "decembre": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
}


def extract_pdf(path):
    size_mb = os.path.getsize(path) / 1024 / 1024
    cmd = [PDF_EXTRACT, path]
    if size_mb > 2:
        cmd += ['--pages', '3']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return None, f'OCR timed out after 120s (file size: {size_mb:.1f}MB) — needs manual review'
    if r.returncode != 0:
        return None, r.stderr
    # strip the header line "[Extracted via ... | N words | X.XMB]"
    lines = r.stdout.split('\n')
    if lines and lines[0].startswith('[Extracted via'):
        lines = lines[2:]
    return '\n'.join(lines), None


def parse_date(text):
    """Try to extract a date from invoice text. Returns datetime.date or None."""
    # DD/MM/YYYY or DD-MM-YYYY
    m = re.search(r'\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b', text)
    if m:
        try:
            return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1))).date()
        except ValueError:
            pass

    # YYYY-MM-DD
    m = re.search(r'\b(20\d{2})-(\d{2})-(\d{2})\b', text)
    if m:
        try:
            return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()
        except ValueError:
            pass

    # DD Month YYYY  or  Month DD, YYYY
    m = re.search(r'\b(\d{1,2})\s+([A-Za-z]{3,10})\s+(20\d{2})\b', text)
    if m:
        mon = MONTH_MAP.get(m.group(2).lower())
        if mon:
            try:
                return datetime(int(m.group(3)), mon, int(m.group(1))).date()
            except ValueError:
                pass

    m = re.search(r'\b([A-Za-z]{3,10})\s+(\d{1,2}),?\s+(20\d{2})\b', text)
    if m:
        mon = MONTH_MAP.get(m.group(1).lower())
        if mon:
            try:
                return datetime(int(m.group(3)), mon, int(m.group(2))).date()
            except ValueError:
                pass

    return None


def parse_amount(text):
    """Extract the most likely total/amount from invoice text. Returns float or None."""

    def to_float(raw):
        # Normalize European (1.234,56) and US (1,234.56) number formats
        raw = raw.replace(' ', '')
        # If both . and , present: whichever comes last is the decimal separator
        if '.' in raw and ',' in raw:
            if raw.rfind('.') > raw.rfind(','):
                raw = raw.replace(',', '')           # US format: 1,234.56
            else:
                raw = raw.replace('.', '').replace(',', '.')  # EU format: 1.234,56
        elif ',' in raw:
            # Comma only — decimal if exactly 2 digits follow
            if re.search(r',\d{2}$', raw):
                raw = raw.replace(',', '.')
            else:
                raw = raw.replace(',', '')
        try:
            v = float(raw)
            return v if 0.01 < v < 10000 else None  # cap at 10k; anomalies above are ref numbers
        except ValueError:
            return None

    # Priority 1: labeled total (Total, Amount due, Fare, etc.) with EUR/€ nearby
    for label in [r'total\s+(?:ttc|inkl\.?\s*mwst\.?|incl\.?\s*(?:vat|btw))?',
                  r'amount\s+due', r'montant\s+(?:ttc|total)', r'totaal\s+(?:incl|bedrag)?',
                  r'to\s+pay', r'a\s+payer', r'te\s+betalen',
                  r'fare\s+(?:total|paid|amount)', r'subtotal',
                  r'grand\s+total', r'net\s+total']:
        m = re.search(label + r'[\s:]*([€$]?\s*[\d\s\.,]{2,12})\s*(?:EUR|€|eur)?',
                      text, re.IGNORECASE)
        if m:
            v = to_float(re.sub(r'[€$]', '', m.group(1)))
            if v:
                return v

    # Priority 2: any number immediately followed by EUR/€ (strict adjacency, max 1 space)
    candidates = []
    for m in re.finditer(r'([\d][\d\s\.,]{0,10}[\d])\s{0,2}(?:EUR|€)(?!\w)', text, re.IGNORECASE):
        v = to_float(m.group(1))
        if v:
            candidates.append(v)

    if candidates:
        # Prefer the most common value (often repeated as subtotal/total), else median
        from collections import Counter
        freq = Counter(candidates)
        most_common_val, most_common_count = freq.most_common(1)[0]
        if most_common_count > 1:
            return most_common_val
        # Otherwise take median (avoids outlier reference numbers)
        candidates.sort()
        return candidates[len(candidates) // 2]

    return None


def categorize(text, filename):
    text_lower = (text + ' ' + filename).lower()
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in text_lower:
                return cat
    return "Other"


def find_match(invoice_date, invoice_amount, bank_debits, tolerance_days=7, tolerance_eur=0.02):
    if not invoice_date or not invoice_amount:
        return None
    best = None
    for t in bank_debits:
        bank_date = datetime.strptime(t['date'], '%Y-%m-%d').date()
        if abs((bank_date - invoice_date).days) <= tolerance_days:
            if abs(t['amount'] - invoice_amount) <= tolerance_eur:
                if best is None or abs((bank_date - invoice_date).days) < abs(
                        (datetime.strptime(best['date'], '%Y-%m-%d').date() - invoice_date).days):
                    best = t
    return best


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('invoices_dir')
    parser.add_argument('bank_statement_pdf')
    parser.add_argument('--output', default='reconciliation_report.json')
    args = parser.parse_args()

    invoices_dir = Path(args.invoices_dir)
    pdf_files = sorted(invoices_dir.glob('*.pdf'))
    print(f"Found {len(pdf_files)} invoice PDFs", flush=True)

    # Parse bank statement
    print("Parsing bank statement...", flush=True)
    bank_script = Path(__file__).parent / 'parse_bank_statement.py'
    bank_text, err = extract_pdf(args.bank_statement_pdf)
    if err:
        print(f"ERROR reading bank statement: {err}", file=sys.stderr)
        sys.exit(1)

    bank_txt_path = '/tmp/bank_stmt.txt'
    with open(bank_txt_path, 'w') as f:
        f.write(bank_text)

    r = subprocess.run(['python3', str(bank_script), bank_txt_path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ERROR parsing bank statement: {r.stderr}", file=sys.stderr)
        sys.exit(1)

    bank_debits = json.loads(r.stdout)
    print(f"Bank statement: {len(bank_debits)} debit transactions parsed", flush=True)

    # Track used bank transactions (avoid double-matching)
    used_bank_ids = set()

    results = []
    unreadable = []

    for i, pdf_path in enumerate(pdf_files):
        filename = pdf_path.name
        print(f"[{i+1}/{len(pdf_files)}] {filename}", flush=True)

        text, err = extract_pdf(str(pdf_path))
        if err or not text or len(text.strip()) < 20:
            unreadable.append({'file': filename, 'reason': err or 'too little text extracted'})
            results.append({
                'file': filename,
                'status': 'UNREADABLE',
                'category': 'Unknown',
                'date': None,
                'amount': None,
                'vendor': None,
                'matched_bank_entry': None,
                'paid_by': 'UNKNOWN — needs manual review',
                'notes': err or 'Very little text extracted — possibly a scanned image or blank page'
            })
            continue

        invoice_date = parse_date(text)
        invoice_amount = parse_amount(text)
        category = categorize(text, filename)

        # Vendor: first non-empty line that looks like a company name
        vendor = None
        for line in text.split('\n'):
            line = line.strip()
            if 3 < len(line) < 60 and not re.match(r'^[\d\s\.,€%/-]+$', line):
                vendor = line
                break

        match = None
        if invoice_amount:
            for idx, t in enumerate(bank_debits):
                if idx in used_bank_ids:
                    continue
                bank_date = datetime.strptime(t['date'], '%Y-%m-%d').date()
                date_ok = (not invoice_date) or abs((bank_date - invoice_date).days) <= 7
                amount_ok = abs(t['amount'] - invoice_amount) <= 0.02
                if date_ok and amount_ok:
                    match = t
                    used_bank_ids.add(idx)
                    break

        if match:
            status = 'MATCHED'
            paid_by = 'KETTU BV bank account'
        elif invoice_amount is None:
            status = 'UNPARSEABLE'
            paid_by = 'UNKNOWN — needs manual review'
        else:
            status = 'UNMATCHED'
            paid_by = 'Juan Florez (personal) — deduct from balance owed'

        results.append({
            'file': filename,
            'status': status,
            'category': category,
            'date': invoice_date.isoformat() if invoice_date else None,
            'amount': invoice_amount,
            'vendor': vendor,
            'matched_bank_entry': match,
            'paid_by': paid_by,
            'notes': None
        })

    # Summaries
    matched = [r for r in results if r['status'] == 'MATCHED']
    unmatched = [r for r in results if r['status'] == 'UNMATCHED']
    unparseable = [r for r in results if r['status'] in ('UNPARSEABLE', 'UNREADABLE')]

    total_matched = sum(r['amount'] for r in matched if r['amount'])
    total_unmatched = sum(r['amount'] for r in unmatched if r['amount'])

    # Category breakdown
    by_category = {}
    for r in results:
        if r['amount']:
            cat = r['category']
            by_category.setdefault(cat, {'count': 0, 'total': 0.0, 'items': []})
            by_category[cat]['count'] += 1
            by_category[cat]['total'] += r['amount']
            by_category[cat]['items'].append({'file': r['file'], 'amount': r['amount'],
                                               'date': r['date'], 'status': r['status']})

    report = {
        'summary': {
            'total_invoices': len(pdf_files),
            'matched_count': len(matched),
            'unmatched_count': len(unmatched),
            'unparseable_count': len(unparseable),
            'total_matched_eur': round(total_matched, 2),
            'total_unmatched_eur': round(total_unmatched, 2),
            'note_unmatched': 'These were paid by Juan Florez personally and should be deducted from balance Juan owes KETTU',
        },
        'by_category': {k: {'count': v['count'], 'total': round(v['total'], 2)} for k, v in sorted(by_category.items(), key=lambda x: -x[1]['total'])},
        'expenses': results,
        'needs_manual_review': [
            {'file': r['file'], 'reason': r.get('notes', ''), 'amount': r['amount']}
            for r in unparseable
        ],
    }

    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    # Print human-readable summary
    print("\n" + "="*60)
    print("KETTU SRL 2025 — EXPENSE RECONCILIATION SUMMARY")
    print("="*60)
    print(f"Total invoices processed:  {len(pdf_files)}")
    print(f"Matched to bank account:   {len(matched)} items  =  €{total_matched:,.2f}")
    print(f"Unmatched (Juan paid):     {len(unmatched)} items  =  €{total_unmatched:,.2f}")
    print(f"Needs manual review:       {len(unparseable)} items")
    print()
    print("EXPENSES BY CATEGORY:")
    for cat, vals in sorted(by_category.items(), key=lambda x: -x[1]['total']):
        print(f"  {cat:<30} {vals['count']:>3} items   €{vals['total']:>10,.2f}")
    print()
    print(f"Full report saved to: {args.output}")
    if unparseable:
        print(f"\nFILES NEEDING MANUAL REVIEW ({len(unparseable)}):")
        for u in unparseable:
            print(f"  - {u['file']}: {u.get('notes') or ''}")


if __name__ == '__main__':
    main()
