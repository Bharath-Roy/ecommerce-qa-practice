let token = null;
let cart = null;
const $ = (id) => document.getElementById(id);

function money(value) {
  return "₹" + Number(value).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const res = await fetch(path, { ...options, headers });
  const data = await res.json().catch(() => ({}));
  return { status: res.status, data };
}

function flash(text, ok) {
  const el = $("flash");
  el.textContent = text || "";
  el.className = ok ? "ok" : "field-error";
}

function show(view) {
  document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
  $("view-" + view).classList.remove("hidden");
  flash("");
  if (view === "products") loadProducts();
  if (view === "cart") loadCart();
  if (view === "orders") loadOrders();
  if (view === "checkout") fillCheckout();
}

function loggedIn(user) {
  $("whoami").textContent = user ? "Hi, " + user.name : "";
  $("nav-login").classList.toggle("hidden", !!user);
  $("nav-register").classList.toggle("hidden", !!user);
  $("nav-logout").classList.toggle("hidden", !user);
  $("nav-orders").classList.toggle("hidden", !user);
}

function clearErrors(prefix) {
  document.querySelectorAll(".field-error[id^='" + prefix + "']").forEach((e) => (e.textContent = ""));
}

// ---- products ----
async function loadProducts() {
  const params = new URLSearchParams();
  if ($("search-q").value.trim()) params.set("q", $("search-q").value);
  if ($("search-category").value) params.set("category", $("search-category").value);
  if ($("search-sort").value) params.set("sort", $("search-sort").value);
  const { status, data } = await api("/api/products?" + params.toString());
  const list = $("product-list");
  list.innerHTML = "";
  if (status !== 200) {
    $("product-count").textContent = "";
    $("no-products").classList.add("hidden");
    return flash(data.error || "Could not load products", false);
  }
  $("product-count").textContent = data.count + " product" + (data.count === 1 ? "" : "s");
  $("no-products").classList.toggle("hidden", data.count !== 0);
  for (const p of data.products) {
    const card = document.createElement("div");
    card.className = "card";
    let stock = "In stock";
    let cls = "";
    if (p.stock <= 0) { stock = "Out of stock"; cls = "stock-out"; }
    else if (p.stock <= 5) { stock = "Only " + p.stock + " left"; cls = "stock-low"; }
    card.innerHTML = "<h3></h3><div class='meta'></div><div class='price'></div><div class='stock'></div>";
    card.querySelector("h3").textContent = p.name;
    card.querySelector(".meta").textContent = p.category + " | rating " + p.rating;
    card.querySelector(".price").textContent = money(p.price);
    const stockEl = card.querySelector(".stock");
    stockEl.textContent = stock;
    stockEl.className = "stock " + cls;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "Add to cart";
    btn.setAttribute("aria-label", "Add " + p.name + " to cart");
    btn.disabled = p.stock <= 0;
    btn.addEventListener("click", () => addToCart(p.id));
    card.appendChild(btn);
    list.appendChild(card);
  }
}

async function addToCart(productId) {
  if (!token) {
    show("login");
    return flash("Please login to add items to your cart", false);
  }
  const { status, data } = await api("/api/cart/items", {
    method: "POST", body: JSON.stringify({ product_id: productId, quantity: 1 }),
  });
  if (status === 200) {
    updateCartCount(data);
    flash("Added to cart", true);
  } else {
    flash(data.error || "Could not add to cart", false);
  }
}

// ---- cart ----
function updateCartCount(c) {
  const n = c.items.reduce((sum, i) => sum + i.quantity, 0);
  $("nav-cart").textContent = "Cart (" + n + ")";
}

async function loadCart() {
  $("cart-error").textContent = "";
  if (!token) {
    show("login");
    return flash("Please login to see your cart", false);
  }
  const { data } = await api("/api/cart");
  cart = data;
  updateCartCount(data);
  const body = $("cart-table").querySelector("tbody");
  body.innerHTML = "";
  $("cart-empty").classList.toggle("hidden", data.items.length > 0);
  $("cart-table").classList.toggle("hidden", data.items.length === 0);
  $("to-checkout").classList.toggle("hidden", data.items.length === 0);
  for (const item of data.items) {
    const row = body.insertRow();
    row.insertCell().textContent = item.name;
    row.insertCell().textContent = money(item.price);
    const qtyCell = row.insertCell();
    const input = document.createElement("input");
    input.type = "number";
    input.value = item.quantity;
    input.setAttribute("aria-label", "Quantity of " + item.name);
    const upd = document.createElement("button");
    upd.type = "button";
    upd.textContent = "Update";
    upd.setAttribute("aria-label", "Update " + item.name);
    upd.addEventListener("click", () => updateQty(item.product_id, input.value));
    qtyCell.append(input, " ", upd);
    row.insertCell().textContent = money(item.line_total);
    const del = document.createElement("button");
    del.type = "button";
    del.textContent = "Remove";
    del.setAttribute("aria-label", "Remove " + item.name);
    del.addEventListener("click", () => removeItem(item.product_id));
    row.insertCell().appendChild(del);
  }
  $("sum-subtotal").textContent = money(data.subtotal);
  $("sum-discount").textContent = money(data.discount);
  $("sum-shipping").textContent = money(data.shipping);
  $("sum-total").textContent = money(data.total);
  $("coupon-remove").classList.toggle("hidden", !data.coupon);
}

async function updateQty(productId, value) {
  const qty = Number(value);
  const { status, data } = await api("/api/cart/items/" + productId, {
    method: "PUT", body: JSON.stringify({ quantity: Number.isInteger(qty) ? qty : value }),
  });
  if (status !== 200) {
    $("cart-error").textContent = data.error || "Could not update the cart";
    return;
  }
  await loadCart();
}

async function removeItem(productId) {
  await api("/api/cart/items/" + productId, { method: "DELETE" });
  await loadCart();
}

$("coupon-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const { status, data } = await api("/api/cart/coupon", {
    method: "POST", body: JSON.stringify({ code: $("coupon-code").value }),
  });
  await loadCart();
  if (status !== 200) $("cart-error").textContent = data.error || "Could not apply the coupon";
  else flash("Coupon applied", true);
});

$("coupon-remove").addEventListener("click", async () => {
  await api("/api/cart/coupon", { method: "DELETE" });
  await loadCart();
});

$("to-checkout").addEventListener("click", () => show("checkout"));

// ---- checkout ----
function fillCheckout() {
  if (!token) {
    show("login");
    return flash("Please login to checkout", false);
  }
  clearErrors("err-co-");
  $("checkout-error").textContent = "";
  $("co-total").textContent = cart ? money(cart.total) : "";
  $("upi-row").classList.toggle("hidden", $("co-payment").value !== "UPI");
}

$("co-payment").addEventListener("change", () => {
  $("upi-row").classList.toggle("hidden", $("co-payment").value !== "UPI");
});

$("checkout-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearErrors("err-co-");
  $("checkout-error").textContent = "";
  const body = {
    name: $("co-name").value, line1: $("co-line1").value, city: $("co-city").value,
    pincode: $("co-pincode").value, phone: $("co-phone").value, payment_method: $("co-payment").value,
  };
  if (body.payment_method === "UPI") body.upi_id = $("co-upi").value;
  const { status, data } = await api("/api/checkout", { method: "POST", body: JSON.stringify(body) });
  if (status === 201) {
    $("confirm-text").textContent = "Thank you. Your order number is " + data.order_no + ". Total paid: " + money(data.total);
    cart = null;
    $("nav-cart").textContent = "Cart (0)";
    ["co-name", "co-line1", "co-city", "co-pincode", "co-phone", "co-upi"].forEach((id) => ($(id).value = ""));
    show("confirm");
  } else if (data.field && $("err-co-" + data.field)) {
    $("err-co-" + data.field).textContent = data.error;
  } else {
    $("checkout-error").textContent = data.error || "Could not place the order";
  }
});

// ---- orders ----
async function loadOrders() {
  if (!token) {
    show("login");
    return flash("Please login to see your orders", false);
  }
  const { data } = await api("/api/orders");
  const body = $("orders-table").querySelector("tbody");
  body.innerHTML = "";
  $("order-detail").classList.add("hidden");
  $("orders-empty").classList.toggle("hidden", data.orders.length > 0);
  $("orders-table").classList.toggle("hidden", data.orders.length === 0);
  for (const o of data.orders) {
    const row = body.insertRow();
    [o.order_no, o.placed_at, o.item_count, money(o.total), o.status].forEach((v) => {
      row.insertCell().textContent = v;
    });
    const view = document.createElement("button");
    view.type = "button";
    view.textContent = "View";
    view.setAttribute("aria-label", "View order " + o.order_no);
    view.addEventListener("click", () => showOrder(o.order_no));
    row.insertCell().appendChild(view);
  }
}

async function showOrder(orderNo) {
  const { status, data } = await api("/api/orders/" + orderNo);
  const box = $("order-detail");
  box.classList.remove("hidden");
  if (status !== 200) {
    box.textContent = data.error || "Could not load the order";
    return;
  }
  const lines = data.items.map((i) => i.product + " x " + i.quantity + " at " + money(i.price)).join("; ");
  box.textContent = data.order_no + ": " + lines + ". Subtotal " + money(data.subtotal) + ", discount " +
    money(data.discount) + ", shipping " + money(data.shipping) + ", total " + money(data.total) +
    ". Ship to " + data.address.name + ", " + data.address.line1 + ", " + data.address.city + " " +
    data.address.pincode + ". Paid by " + data.payment_method + ".";
}

// ---- login and register ----
$("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("login-error").textContent = "";
  const { status, data } = await api("/api/login", {
    method: "POST", body: JSON.stringify({ email: $("login-email").value, password: $("login-password").value }),
  });
  if (status !== 200) {
    $("login-error").textContent = data.error || "Login failed";
    return;
  }
  token = data.token;
  loggedIn(data.user);
  $("login-password").value = "";
  const c = await api("/api/cart");
  updateCartCount(c.data);
  show("products");
  flash("Logged in", true);
});

$("register-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  clearErrors("err-");
  const { status, data } = await api("/api/register", {
    method: "POST",
    body: JSON.stringify({
      name: $("reg-name").value, email: $("reg-email").value, phone: $("reg-phone").value,
      password: $("reg-password").value, confirm_password: $("reg-confirm").value,
    }),
  });
  if (status === 201) {
    ["reg-name", "reg-email", "reg-phone", "reg-password", "reg-confirm"].forEach((id) => ($(id).value = ""));
    show("login");
    flash("Account created. Please login.", true);
  } else if (data.field && $("err-" + data.field)) {
    $("err-" + data.field).textContent = data.error;
  } else {
    flash(data.error || "Could not register", false);
  }
});

$("search-form").addEventListener("submit", (e) => {
  e.preventDefault();
  loadProducts();
});

$("nav-logout").addEventListener("click", () => location.reload());
document.querySelectorAll("[data-view]").forEach((el) => {
  el.addEventListener("click", (e) => {
    e.preventDefault();
    show(el.dataset.view);
  });
});

loadProducts();
