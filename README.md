# Counsellor Desk

A working local frontend and backend prototype for reviewing Excel marks and preparing parent WhatsApp notifications. Requires Python 3.10 or later. No pip packages, Node installation, database, API account or credentials are needed.

## Start

1. Extract the ZIP.
2. Open a terminal in the `counsellor-marks` folder.
3. Run:

   ```sh
   python3 server.py
   ```

   On Windows, use `py server.py` if `python3` is unavailable.
4. Open http://127.0.0.1:8000 in your browser.
5. Stop the server with Ctrl+C.

If port 8000 is in use, on macOS/Linux run `PORT=8001 python3 server.py` and open port 8001. The server binds only to your computer's loopback interface.

## Professor workflow

- Review the names, parent numbers and marks loaded from the included Excel file.
- Set the assessment and sender names. The assessment label is an editable default; it is not present in the workbook.
- Verify the country code. `91` is an explicit India assumption for local 10-digit numbers. Numbers beginning with `+` are treated as international numbers.
- Click **Send WhatsApp** beside a student to review the complete message.
- Choose **Simulate send** for a safe demonstration, or **Open draft in WhatsApp** to open WhatsApp and manually send from the account currently signed in on that device. The sender-name field does not select a WhatsApp account.
- **Send All · Mock** reviews all workbook rows, including rows hidden by search. **Simulate all sends** processes them in one backend request and reports successes/failures. Each prepared WhatsApp link must be opened and sent individually; the prototype never automatically sends messages.
- Simulation status is held in the current browser session and resets on refresh. It is not evidence of delivery. Repeated simulations are harmless and do not call external services.

## Workbook findings

The original `/mnt/data/Book7.xlsx` reference was recovered from the earlier chat attachment. An unchanged copy is included as `data/Book7.xlsx`.

| Name | Maths | UHV | DBMS | COA |
|---|---:|---:|---:|---:|
| harsha | 97 | 76 | 30 | 48 |
| raghu | 56 | 78 | 89 | 89 |
| coordinator | 100 | 100 | 100 | 101 |

All three rows and their parent numbers are preserved. The coordinator row is flagged because its role may be a test record and its COA mark is 101. No maximum marks are specified, so no percentages, grades or pass/fail decisions are invented.

To update records, replace `data/Book7.xlsx` with the same layout and refresh the browser. The reader supports the first worksheet XML part (`sheet1.xml`), with the first populated row containing columns A–F: `Student name`, `Student parent no`, `maths`, `uhv`, `dbms`, `coa`. Case and surrounding spaces in headers are ignored. Blank names are skipped; missing marks show “Not recorded.” Use numeric marks, not formulas (formulas only expose Excel's saved cached results). This is a focused reader for this workbook, not a general Excel import service. Save phone numbers as text to preserve a leading `+` or zero.

## Source structure

```text
server.py             Local HTTP server, validation and API routes
workbook.py           XLSX reader using Python standard library
notifications.py      Message builder, phone normalization, provider boundary
public/index.html     Accessible dashboard and review dialog
public/styles.css     Responsive visual design
public/app.js         Search, preview, WhatsApp links and mock flow
data/Book7.xlsx        Original source workbook
tests/test_app.py      Data fidelity and notification tests
```

## API

- `GET /api/students`: Excel records, source metadata and mock mode.
- `POST /api/preview`: builds one or more messages and WhatsApp links.
- `POST /api/send`: uses `MockProvider` and returns `simulated` or per-record `failed`. Does not send anything externally or persist a delivery log.

Both POST routes accept JSON:

```json
{
  "studentIds": ["row-2", "row-3"],
  "assessment": "Internal Assessment 1",
  "counsellor": "Class Counsellor",
  "country": "91"
}
```

IDs correspond to physical workbook row numbers. Unknown IDs and invalid request settings return HTTP 400. Invalid phone numbers fail per record, so other valid recipients can still be simulated. Warnings require human review but do not silently alter or exclude source rows.

## Connecting WhatsApp Business / Cloud API later

`notifications.py` separates message preparation from delivery. `MockProvider.send(notification)` returns the current result contract. `CloudAPIProvider.send` deliberately raises `NotImplementedError`; no fake integration is presented as working.

For a production implementation, inject a configured provider into `/api/send`, keep credentials exclusively on the server, map marks into the appropriate approved template, and send through the institution's registered WhatsApp Business number. Implement persistent queued jobs, idempotency keys, retry/backoff and delivery webhooks. Distinguish accepted/queued, delivered and failed statuses. Add authenticated counsellor accounts, student ownership checks, parent consent and a protected audit log before hosting real records. Verify Meta's current API and messaging requirements when implementing the integration. Cloud API messaging requires an appropriately configured business sender; it does not automatically send from each professor's personal WhatsApp number.

## Verification

```sh
python3 -m unittest discover -s tests -v
```

Tests cover exact workbook marks (including 101), warnings, message encoding, phone validation, blank versus zero marks and disabled Cloud API behavior. This project is a local prototype with real source records. The included workbook contains parent contact details; distribute the ZIP only to intended project reviewers. It has no login or multi-user persistence and is not a production deployment.
