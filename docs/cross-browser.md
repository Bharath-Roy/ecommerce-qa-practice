# Cross-browser testing

The 24 UI cases from `test-cases.csv` were run on builds 1.0 and 1.1 in Chromium 153 and Firefox 155. These browsers came with Playwright 1.63. Both ran on Linux with a 1200 x 900 window and a data reset before each case.

## Results

Both browsers gave identical results: 22 passed on build 1.0 and all 24 passed on build 1.1. TC-SRC-03 (SHOP-3) and TC-ORD-01 (SHOP-9) failed the same way on 1.0 in both browsers.

| Case | Scenario | Chromium 1.0 | Firefox 1.0 | Chromium 1.1 | Firefox 1.1 |
| --- | --- | --- | --- | --- | --- |
| TC-REG-01 | Register with valid details | Pass | Pass | Pass | Pass |
| TC-REG-02 | Submit the empty form | Pass | Pass | Pass | Pass |
| TC-REG-10 | Confirm password does not match | Pass | Pass | Pass | Pass |
| TC-REG-11 | Email that is already registered | Pass | Pass | Pass | Pass |
| TC-LGN-01 | Login with valid credentials | Pass | Pass | Pass | Pass |
| TC-LGN-02 | Wrong password | Pass | Pass | Pass | Pass |
| TC-LGN-04 | Login with empty fields | Pass | Pass | Pass | Pass |
| TC-LGN-06 | Guest clicks Add to cart | Pass | Pass | Pass | Pass |
| TC-SRC-01 | Product list on opening the shop | Pass | Pass | Pass | Pass |
| TC-SRC-02 | Search by product name | Pass | Pass | Pass | Pass |
| TC-SRC-03 | Search text in capital letters | Fail | Fail | Pass | Pass |
| TC-SRC-05 | Search with no result | Pass | Pass | Pass | Pass |
| TC-SRC-09 | Filter by category | Pass | Pass | Pass | Pass |
| TC-SRC-13 | Out of stock product on the page | Pass | Pass | Pass | Pass |
| TC-SRC-14 | Low stock label and price format | Pass | Pass | Pass | Pass |
| TC-CRT-01 | Add a product to the cart | Pass | Pass | Pass | Pass |
| TC-CRT-09 | Change the quantity in the cart | Pass | Pass | Pass | Pass |
| TC-CRT-11 | Remove a product | Pass | Pass | Pass | Pass |
| TC-CPN-05 | Remove the coupon | Pass | Pass | Pass | Pass |
| TC-CHK-01 | Place an order with cash on delivery | Pass | Pass | Pass | Pass |
| TC-CHK-03 | UPI field and invalid UPI id | Pass | Pass | Pass | Pass |
| TC-CHK-05 | Required address fields | Pass | Pass | Pass | Pass |
| TC-ORD-01 | My orders page shows the amount paid | Fail | Fail | Pass | Pass |
| TC-ORD-06 | User with no orders | Pass | Pass | Pass | Pass |

## Checks and limits

Checked in each browser: the text and numbers on screen, which buttons and messages are visible or disabled, form errors, the header after login and the number format (Rs 4,999.00 with Indian grouping).

Not checked:

- Safari. I tried to add WebKit as a third browser, but it would not start on this machine (missing system libraries), so there is no result for it.
- Edge, Chrome itself, and any phone browser.
- How the page looks. There was no visual comparison and no screenshots, so a layout problem that does not change the text would not have been seen. The stylesheet has one narrow-screen rule that I did not test.
- Older browser versions.

No browser-specific defect was found in these 24 cases.
