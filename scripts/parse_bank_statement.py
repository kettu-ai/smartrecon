import re
from datetime import datetime
import sys
import json

def parse_bank_statement(text):
    transactions = []
    lines = text.split('\n')
    current_transaction = {}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = re.search(r'^(?:\d{3}\s+)?(?P<date>\d{2}-\d{2}-\d{4})\s+(?P<description>.*?)(?P<value_date>\d{2}-\d{2})\s+(?P<amount>[\d\s\.,]+)\s+(?P<sign>[+-])$', line)
        if match:
            if current_transaction:
                transactions.append(current_transaction)
            current_transaction = {
                'date': datetime.strptime(match.group('date'), '%d-%m-%Y').date(),
                'description': match.group('description').strip(),
                'amount': float(match.group('amount').replace(' ', '').replace('.', '').replace(',', '.')),
                'type': 'debit' if match.group('sign') == '-' else 'credit'
            }
        else:
            skip_keywords = ["IBAN", "KBC Brussels Business PRO Account", "KETTU BV",
                             "duplicate statement", "Debit advice", "Statement of charges",
                             "no      date", "value date", "Balance on"]
            if current_transaction and not any(kw in line for kw in skip_keywords):
                current_transaction['description'] += " " + line.strip()

    if current_transaction:
        transactions.append(current_transaction)

    return transactions


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 parse_bank_statement.py <path_to_bank_statement_text_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    with open(file_path, 'r') as f:
        bank_statement_text = f.read()

    transactions = parse_bank_statement(bank_statement_text)
    debit_transactions = [t for t in transactions if t['type'] == 'debit']

    for t in debit_transactions:
        t['date'] = t['date'].isoformat()

    print(json.dumps(debit_transactions, indent=2))
