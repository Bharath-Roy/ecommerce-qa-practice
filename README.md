# Practice shop testing

This is a QA practice project for a small online shop. It covers registration, login, search, cart, coupon, checkout and orders, using browser tests, Postman and SQL checks.

Build 1.0 has 10 defects left in on purpose. Build 1.1 fixes them. The test results cover smoke, functional, sanity and regression testing, plus a comparison of Chromium and Firefox. This is personal practice, not client work.

## Run it

Python 3 (tried on 3.14), nothing to install.

```sh
python3 app/shop.py                  # build 1.0, with the defects
SHOP_BUILD=1.1 python3 app/shop.py   # build 1.1, fixed
```

Open http://127.0.0.1:5060. Users: `meera@example.com` / `Meera@123` and `arjun@example.com` / `Arjun@123`. The data is in `.data/shop.db`, and `POST /api/dev/reset` puts the original data back. Port can be changed with `PORT=5061`.

## Test files

Start with `docs/requirements.md` and `docs/test-plan.md`. The 87 cases and their results are in `docs/test-cases.csv`. Failures are recorded in `docs/defect-log.md`, with a CSV copy in `docs/jira-import.csv`.

`docs/test-summary.md` has the results by module. The browser and API run notes are in `docs/cross-browser.md` and `docs/api-testing.md`.

Postman files are in `postman/`, the database checks in `sql/validation-queries.sql`.

## API and database checks

```sh
python3 app/shop.py &
npx newman run postman/practice-shop.postman_collection.json -e postman/practice-shop-local.postman_environment.json
sqlite3 -header .data/shop.db < sql/validation-queries.sql
```

On build 1.0 newman reports 21 failed assertions, and Q2 and Q4 in the SQL file return rows once a few orders and a duplicate registration have been made. On build 1.1 there are no failures and every query is empty except Q6, which only lists orders.

## Results

87 cases. Build 1.0: 71 passed, 16 failed (10 defects: 1 critical, 5 major, 4 minor). Build 1.1: 87 passed. Details are in `docs/test-summary.md`.

## Limits

- Cross-browser means Chromium and Firefox only. WebKit would not start on the machine used, and there are no phone or Edge results.
- The SQL was run on SQLite. It is plain SQL but has not been tried on MySQL.
- The defects are in `docs/jira-import.csv` but have not been imported into Jira.
- No load testing and no test of two customers checking out at the same moment.
