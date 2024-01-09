# Requirements

What the practice shop is supposed to do. I wrote the test cases from this list, so when a rule changes the cases have to change too.

## Registration

- Fields: full name, email, phone, password, confirm password. All required.
- Name: 2 to 50 characters, letters and spaces only.
- Email: valid format, up to 100 characters. One account per email, and upper/lower case does not matter ("Meera@Example.com" is the same email as "meera@example.com").
- Phone: 10 digits, starting with 6, 7, 8 or 9.
- Password: at least 8 characters, with an upper case letter, a lower case letter, a digit and a special character. Must match the confirm field.
- Spaces at the start and end of name, email and phone are ignored.
- Errors show under the field they belong to.

## Login

- Email and password. Email is not case sensitive, password is.
- Wrong email and wrong password give the same message ("Invalid email or password") so nobody can find out which emails are registered.
- After login the header shows the user's name, with a Logout button.
- Cart, checkout and orders need a login. A guest who clicks Add to cart is sent to the login page.

## Products and search

- 12 products in four categories (Fashion, Electronics, Home, Sports), each with price, stock and rating.
- Search looks for the text anywhere in the product name. It ignores upper/lower case and leading/trailing spaces. Up to 50 characters.
- Characters like % and _ are ordinary characters in the search, not special ones.
- Category filter, and sorting by price (low to high, high to low) or rating. Search, category and sort can be combined.
- No match shows "No products found".
- Stock 0 shows "Out of stock" and the Add to cart button is disabled. Stock of 5 or less shows "Only N left".

## Cart

- 1 to 10 of one product, and never more than the stock.
- Adding a product that is already in the cart adds to its quantity (the 10 limit and the stock limit still apply).
- Quantity can be changed in the cart and a product can be removed.
- Shipping is 49.00. It is free when the cart value is 500.00 or more.
- Coupon WELCOME10 gives 10 percent off, maximum 150.00, only when the cart value is 1000.00 or more. If the cart drops below 1000.00 later the coupon is removed. The code is not case sensitive.
- The cart belongs to the user and is still there after logging out and in again.
- Total = subtotal - discount + shipping.

## Checkout

- Address: name, address line, city, pincode, phone. All required.
- Pincode is exactly 6 digits and does not start with 0. Phone follows the same rule as registration.
- Payment: Cash on Delivery or UPI. UPI needs a UPI id like name@bank. Cash on Delivery is not allowed when the total is more than 50000.00.
- Quantities are checked against stock again at checkout. If someone else bought the stock first the order is refused.
- On success: order number (ORD100001, ORD100002 and so on), stock goes down, cart and coupon are cleared. The confirmation shows the order number and the total paid.
- Empty cart cannot be checked out.

## Orders

- "My orders" lists the user's orders, newest first, with order number, date, number of items, total paid and status.
- Order details show items, prices, address, payment method and totals.
- A user can only see their own orders.

## Not covered

No real payments, no returns or cancellations, no password reset, no email or OTP, no admin side, no product images, no wishlist.

## Test data

| Email | Password | Name |
| --- | --- | --- |
| meera@example.com | Meera@123 | Meera Nair |
| arjun@example.com | Arjun@123 | Arjun Das |

Products with stock worth remembering: Smart Watch has 3, Desk Lamp has 0, Steel Water Bottle costs exactly 500.00, Ceramic Coffee Mug costs 199.00. `POST /api/dev/reset` brings back the original users and stock.
