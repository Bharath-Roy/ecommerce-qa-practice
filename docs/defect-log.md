# Defect log

Build 1.0 has these 10 seeded defects. All are closed after retesting on build 1.1, where the full regression run also passed.

| ID | Summary | Severity | Priority | Found by | Status |
| --- | --- | --- | --- | --- | --- |
| SHOP-1 | Password with exactly 8 characters is rejected | Minor | Medium | TC-REG-07 | Closed |
| SHOP-2 | Same email in a different case registers a second account | Major | High | TC-REG-12, TC-DB-04 | Closed |
| SHOP-3 | Search only matches when the case is the same | Major | High | TC-SRC-03, TC-SRC-04 | Closed |
| SHOP-4 | Searching for % or _ returns every product | Minor | Low | TC-SRC-07 | Closed |
| SHOP-5 | More than the stock can be bought, stock goes negative | Major | High | TC-CRT-10, TC-CHK-14, TC-DB-02 | Closed |
| SHOP-6 | Shipping charged on a cart of exactly 500.00 | Minor | Medium | TC-CRT-14 | Closed |
| SHOP-7 | Coupon discount is not capped at 150.00 | Major | High | TC-CPN-02 | Closed |
| SHOP-8 | Pincode with 7 digits is accepted | Minor | Medium | TC-CHK-07 | Closed |
| SHOP-9 | My orders shows the total without shipping | Major | Medium | TC-ORD-01, TC-ORD-07, TC-DB-06 | Closed |
| SHOP-10 | Any logged in user can open someone else's order | Critical | High | TC-ORD-04 | Closed |

The UI run reproduced SHOP-3 and SHOP-9 in both Chromium and Firefox. The reports below describe build 1.0.

## SHOP-1 Password with exactly 8 characters is rejected

Open Register or send POST /api/register with valid details and password `Abcd@123`. It has 8 characters and includes an upper case letter, a lower case letter, a digit and a special character.

Expected: 201, account created. Actual: 400 WEAK_PASSWORD, even though the message says "8 or more characters". A 9 character password works and 7 is rejected correctly. The problem is at exactly 8.

## SHOP-2 Same email in a different case registers a second account

Register `Meera@Example.com` with otherwise valid details. The seed account `meera@example.com` already exists, so this should return 409 EMAIL_EXISTS. Instead, it returns 201 and creates a second account.

Q4 returns one row for meera@example.com with `accounts = 2`. Login with the new password fails (401). The original password works with either spelling of the email, leaving the second account unusable.

## SHOP-3 Search only matches when the case is the same

Search for `SHOES`. Expected Running Shoes; the page shows "No products found".

Also try `/api/products?q=pack`. It should return Laptop Backpack and Notebook Pack of 5, but only Laptop Backpack is returned. Searching for `kurta` gives no results either. The match depends on the capital letters in the product name.

## SHOP-4 Searching for % or _ returns every product

Search for `%`, then `_`. Neither character occurs in a product name, so both searches should be empty. Both return all 12 products.

The query uses the search text as a LIKE pattern without escaping these characters. The separate SQL-like input check, `' OR 1=1 --` (TC-SRC-08), passes.

## SHOP-5 More than the stock can be bought, stock goes negative

There are two ways to reproduce this. Start each from reset data:

1. Add 1 Smart Watch, which has stock 3. Change the cart quantity to 5. The update succeeds instead of returning 409 INSUFFICIENT_STOCK.
2. Meera and Arjun each add 3 Smart Watches. Place Meera's order, then Arjun's. Arjun's order should be refused because Meera bought the remaining stock. Both orders succeed and Q2 shows Smart Watch stock at -3.

These orders are placed one after the other, not at the same time. Stock is checked when adding to the cart, but not on a quantity update or at checkout in 1.0.

## SHOP-6 Shipping charged on a cart of exactly 500.00

Add 1 Steel Water Bottle (500.00) and check the cart:

- Expected: shipping 0.00, total 500.00.
- Actual: shipping 49.00, total 549.00.

Shipping is correctly free at 1299.00 and charged at 199.00. The free-shipping rule misses exactly 500.00.

## SHOP-7 Coupon discount is not capped at 150.00

Add Running Shoes (2499.00), then apply WELCOME10. The discount is 249.90 and the total is 2249.10. With the cap applied, these should be 150.00 and 2349.00.

The app takes the full 10 percent even above a cart value of 1500.00. At 50000.00 that would mean a 5000.00 discount. The Backpack check at 1299.00 gives the correct discount of 129.90 because it is below the cap.

## SHOP-8 Pincode with 7 digits is accepted

Put a product in the cart and go to checkout. Enter `5000011` as the pincode and fill the other fields correctly.

Expected the error "Pincode must be 6 digits and cannot start with 0". Instead, checkout returns 201 and saves the 7 digit pincode with the order. The field has no length limit on the page either. Pincodes with 5 digits, a leading 0 or letters are rejected correctly.

## SHOP-9 My orders shows the total without shipping

Order 1 Ceramic Coffee Mug: 199.00 plus 49.00 shipping. The confirmation shows 248.00, but My orders shows 199.00 for the same order.

The list should show 248.00. Order details at GET /api/orders/{no} and the stored total from Q6 both have that amount. Shipping is missing only from the list total.

## SHOP-10 Any logged in user can open someone else's order

1. Log in as Meera, place an order and note its number.
2. Log in as Arjun. Send GET /api/orders/{that order number} using Arjun's token.

Expected: 404 ORDER_NOT_FOUND. Actual: 200, including Meera's items, name, address and phone number.

Order numbers are sequential (ORD100001, ORD100002), so another customer can guess them. The order list already filters by user; the detail endpoint is missing the ownership check.
