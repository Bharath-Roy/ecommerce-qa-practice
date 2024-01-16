# API testing notes

Base URL `http://127.0.0.1:5060`, JSON in and out. Everything under cart, checkout and orders needs `Authorization: Bearer <token>` from the login call.

| Method | Path | Does |
| --- | --- | --- |
| POST | /api/register | create an account (201) |
| POST | /api/login | token and user name (200) |
| GET | /api/products?q=&category=&sort= | list, search, filter, sort |
| GET | /api/products/{id} | one product |
| GET | /api/cart | cart with subtotal, discount, shipping, total |
| POST | /api/cart/items | add `{product_id, quantity}` |
| PUT | /api/cart/items/{product_id} | change the quantity |
| DELETE | /api/cart/items/{product_id} | remove a product |
| POST | /api/cart/coupon | apply `{code}` |
| DELETE | /api/cart/coupon | remove the coupon |
| POST | /api/checkout | place the order (201) |
| GET | /api/orders | my orders, newest first |
| GET | /api/orders/{order_no} | one order |
| POST | /api/dev/reset | reset the data |
| GET | /api/health | status and build |

Amounts are strings with 2 decimals ("1299.00"), quantities are whole numbers.

Errors look like `{"error": "text", "code": "WEAK_PASSWORD", "field": "password"}`. Input errors include `field` so the page can put the message beside that input. Tests check status and `code`; some also check `field` or the message.

| Status | Used for |
| --- | --- |
| 400 | invalid input: INVALID_NAME, INVALID_EMAIL, INVALID_PHONE, WEAK_PASSWORD, PASSWORD_MISMATCH, REQUIRED_FIELD, INVALID_QUANTITY, QUANTITY_LIMIT, INVALID_COUPON, COUPON_MIN_SUBTOTAL, EMPTY_CART, INVALID_PINCODE, INVALID_PAYMENT, INVALID_UPI, COD_NOT_AVAILABLE, INVALID_CATEGORY, INVALID_SORT, INVALID_QUERY, BAD_JSON |
| 401 | no token, bad token, wrong email or password |
| 404 | product, cart item or order not found (also an order that belongs to someone else) |
| 409 | EMAIL_EXISTS, OUT_OF_STOCK, INSUFFICIENT_STOCK |
| 500 | anything unexpected, body is just `{"error": "Internal server error"}` |

## Running the collection

1. Start the app: `python3 app/shop.py`
2. In Postman import `postman/practice-shop.postman_collection.json` and `postman/practice-shop-local.postman_environment.json`.
3. Pick the "Practice Shop local" environment and run the whole collection in order.

Without Postman: `npx newman run postman/practice-shop.postman_collection.json -e postman/practice-shop-local.postman_environment.json`

Folder 00 resets the data and saves tokens for Meera and Arjun. Run the folders in order: cart contents and stock carry over between requests. The first two order numbers are saved in collection variables for the orders folder.

Requests that expose defects are near the end of each folder. The SHOP-5 checkout sequence is after the other stock-dependent orders, so negative stock does not affect those checks.

## Against the two builds

```sh
python3 app/shop.py                  # build 1.0
SHOP_BUILD=1.1 python3 app/shop.py   # build 1.1
```

The collection has 106 requests and 224 assertions. Build 1.0 has 21 failed assertions; build 1.1 has 0.

The failures are in TC-REG-07, TC-REG-12, TC-SRC-03, TC-SRC-04, TC-SRC-07 (two requests), TC-CRT-10, TC-CRT-14, TC-CPN-02, TC-CHK-07, TC-CHK-14 (two requests), TC-ORD-04 and TC-ORD-07.
