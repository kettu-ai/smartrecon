# Contributing to SmartRecon

## Adding bank statement formats

The `scripts/parse_bank_statement.py` parser is tested against KBC Belgium PDF exports. To add support for another bank:

1. Export a sample statement (anonymize amounts/names)
2. Run `python3 scripts/pdf-extract sample.pdf` and check the text layout
3. Adjust the regex in `parse_bank_statement.py` to match the bank's column format
4. Add a test case in `tests/`
5. Submit a PR with the bank name in the title

## Adding expense categories

Edit the `CATEGORIES` dict in `scripts/reconcile_all.py` — add keywords that match your locale or industry.

## Reporting issues

Please include:
- Bank name and country
- Anonymized sample of the PDF text (run `pdf-extract yourfile.pdf | head -30`)
- What SmartRecon parsed vs. what the correct value was
