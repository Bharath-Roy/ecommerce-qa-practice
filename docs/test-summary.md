# Test summary

Practice shop, builds 1.0 and 1.1. Run on 2026-10-01.

Build 1.0: 71 passed and 16 failed out of 87 cases. The failures were linked to 10 defects: 1 critical, 5 major and 4 minor. All 87 cases passed on build 1.1 after the fixes.

All 9 smoke cases passed on both builds. On 1.1, sanity passed 16 of 16 cases and regression passed 87 of 87. No defects remain open on 1.1.

## What ran

| Part | How | Cases |
| --- | --- | --- |
| Screens | Chromium and Firefox | 24 |
| API | Postman collection and requests sent one by one | 57 |
| Database | `sql/validation-queries.sql` after a set of orders | 6 |

45 positive cases and 42 negative. By priority: 41 high, 35 medium, 11 low.

Environment: Linux, Python 3.14 for the app, SQLite database, Chromium 153, Firefox 155, newman 6.2.2 for the collection, sqlite3 for the queries.

## Results by module

| Module | Cases | Passed on 1.0 | Passed on 1.1 |
| --- | --- | --- | --- |
| Registration | 13 | 11 | 13 |
| Login | 7 | 7 | 7 |
| Search | 15 | 12 | 15 |
| Cart | 17 | 15 | 17 |
| Coupon | 6 | 5 | 6 |
| Checkout | 16 | 14 | 16 |
| Orders | 7 | 4 | 7 |
| Database | 6 | 3 | 6 |
| Total | 87 | 71 | 87 |

The main problems in orders were the missing shipping amount in the list (SHOP-9) and access to another user's order (SHOP-10).

## Defects

| Severity | Count | IDs |
| --- | --- | --- |
| Critical | 1 | SHOP-10 |
| Major | 5 | SHOP-2, 3, 5, 7, 9 |
| Minor | 4 | SHOP-1, 4, 6, 8 |

Details are in `defect-log.md`. SHOP-1, SHOP-6 and SHOP-8 are boundary errors. The API and SQL checks caught things the screens did not show: access to someone else's order (SHOP-10) and duplicate email rows (SHOP-2).

The Postman collection ran 106 requests with 224 assertions. Build 1.0 had 21 failed assertions across requests linked to the 10 defects; build 1.1 had 0. See `api-testing.md` for the run order.

Chromium 153 and Firefox 155 gave identical results on all 24 UI cases: 22 passed on 1.0, 24 on 1.1. The per-case results are in `cross-browser.md`.

## Not tested

- Safari, Edge and mobile browsers (WebKit would not start here).
- Two customers checking out at exactly the same time. TC-CHK-14 has them buy one after the other.
- Load, speed and security beyond login checks and the ownership checks on orders.
- The SQL was run on SQLite only, not on MySQL.
- How the pages look (no visual comparison).

`jira-import.csv` is prepared for import, but it has not been imported into Jira.
