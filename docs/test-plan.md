# Test plan

## Scope

Test registration, login, product search, cart, coupon, checkout and orders against `requirements.md`. Use the browser for screen checks, Postman for API calls and SQL for saved data.

Out of scope: performance, real payments, anything on the admin side.

## Run order

Write the cases from the requirements in `test-cases.csv`. Start build 1.0 and run smoke first. If smoke passes, continue with the full functional run and record failures in `defect-log.md`, including steps and expected and actual results.

After logging the defects, start the fixed build with `SHOP_BUILD=1.1`. Retest the failed cases as sanity, then run all cases again for regression. Repeat the UI cases in the second browser and record those results in `cross-browser.md`. The final counts go in `test-summary.md`.

## Suites

Smoke has 9 cases: registration, login, the product list and search, adding to the cart, changing quantity, checkout, order details and calls without a login.

TC-REG-01, TC-LGN-01, TC-LGN-07, TC-SRC-01, TC-SRC-02, TC-CRT-01, TC-CRT-09, TC-CHK-01, TC-ORD-02

Sanity has the 16 cases that failed on build 1.0. Find them in the Suites column; the Defect column links each failure to its report.

Regression uses all 87 cases.

The functional cases cover all modules. Input checks cover registration, search, cart quantity, address and coupon. Boundary checks include name and password length, shipping at 500.00, the discount cap, pincode length and stock. There are 42 negative cases out of 87. API run notes are in `api-testing.md` and database checks are in `sql/validation-queries.sql`.

## When to start and finish

Start when the app runs and data reset works. All smoke cases must pass before the full run. To finish testing, run every case, log every failure and check that no critical or major defect is still open.

## Data

Every case starts from reset data (`POST /api/dev/reset`) except the Postman collection, which resets once at the start and then runs in order. Users and products are in `requirements.md`.

For the database cases a few orders are placed first: a mug, a backpack with the coupon, and two users buying the last 3 Smart Watches. Another registration with "Meera@Example.com" is added at the end.

## Risks and gaps

- Only Chromium and Firefox. No Safari, no Edge, no phone.
- Nothing about speed, load or two people checking out at the same moment.
- The SQL was tried on SQLite, not on MySQL.
