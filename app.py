from functools import wraps
import re

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for

from config import Config
from db import db_cursor

app = Flask(__name__)
app.config.from_object(Config)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if session.get("role") not in allowed_roles:
                flash("You do not have permission to access that page.", "danger")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)

        return wrapped_view

    return decorator


def fetch_products():
    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            SELECT
                p.product_id,
                p.name,
                c.name AS category,
                p.price,
                p.stock_quantity,
                p.image_url,
                p.description
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            ORDER BY p.product_id DESC
            """
        )
        return cursor.fetchall()


def fetch_product_by_id(product_id):
    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            SELECT
                p.product_id,
                p.name,
                c.name AS category,
                p.price,
                p.stock_quantity,
                p.image_url,
                p.description
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            WHERE p.product_id = %s
            """,
            (product_id,),
        )
        return cursor.fetchone()


def fetch_categories():
    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            SELECT category_id, name
            FROM categories
            ORDER BY name
            """
        )
        return cursor.fetchall()


def fetch_cart_items_for_user(user_id):
    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            SELECT c.cart_id, c.product_id, c.quantity, p.name, p.price, p.image_url
            FROM cart c
            JOIN products p ON p.product_id = c.product_id
            WHERE c.user_id = %s
            ORDER BY c.added_at DESC
            """,
            (user_id,),
        )
        return cursor.fetchall()


def fetch_favorite_ids(user_id):
    with db_cursor() as (_, cursor):
        cursor.execute("SELECT product_id FROM favorites WHERE user_id = %s", (user_id,))
        return {row["product_id"] for row in cursor.fetchall()}


def fetch_favorite_products(user_id):
    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            SELECT
                p.product_id,
                p.name,
                c.name AS category,
                p.price,
                p.stock_quantity,
                p.image_url,
                p.description
            FROM favorites f
            JOIN products p ON p.product_id = f.product_id
            JOIN categories c ON p.category_id = c.category_id
            WHERE f.user_id = %s
            ORDER BY f.favorite_id DESC
            """,
            (user_id,),
        )
        return cursor.fetchall()


def fetch_orders(user_id=None):
    with db_cursor() as (_, cursor):
        if user_id is None:
            cursor.execute(
                """
                SELECT
                    o.order_id,
                    o.user_id,
                    u.name AS customer_name,
                    o.total_amount,
                    o.status,
                    o.delivery_address,
                    o.ordered_at
                FROM orders o
                JOIN users u ON u.user_id = o.user_id
                ORDER BY o.ordered_at DESC, o.order_id DESC
                """
            )
        else:
            cursor.execute(
                """
                SELECT
                    o.order_id,
                    o.user_id,
                    u.name AS customer_name,
                    o.total_amount,
                    o.status,
                    o.delivery_address,
                    o.ordered_at
                FROM orders o
                JOIN users u ON u.user_id = o.user_id
                WHERE o.user_id = %s
                ORDER BY o.ordered_at DESC, o.order_id DESC
                """,
                (user_id,),
            )
        orders = cursor.fetchall()

        if not orders:
            return [], []

        order_lookup = {order["order_id"]: {**order, "line_items": []} for order in orders}
        order_ids = tuple(order_lookup.keys())
        placeholders = ", ".join(["%s"] * len(order_ids))

        cursor.execute(
            f"""
            SELECT
                oi.order_id,
                oi.quantity,
                oi.unit_price,
                p.product_id,
                p.name,
                p.image_url
            FROM order_items oi
            JOIN products p ON p.product_id = oi.product_id
            WHERE oi.order_id IN ({placeholders})
            ORDER BY oi.order_id DESC, oi.item_id ASC
            """,
            order_ids,
        )
        items = cursor.fetchall()

    for item in items:
        order_lookup[item["order_id"]]["line_items"].append(item)

    pending_statuses = {"pending", "confirmed", "shipped"}
    pending_orders = []
    completed_orders = []

    for order in order_lookup.values():
        if order["status"] in pending_statuses:
            pending_orders.append(order)
        else:
            completed_orders.append(order)

    return pending_orders, completed_orders


@app.context_processor
def inject_header_state():
    cart_items = []
    cart_count = 0
    cart_total = 0
    favorite_ids = set()

    user_id = session.get("user_id")
    if user_id and session.get("role") != "manager":
        try:
            cart_items = fetch_cart_items_for_user(user_id)
            cart_count = sum(item["quantity"] for item in cart_items)
            cart_total = sum(item["price"] * item["quantity"] for item in cart_items)
            favorite_ids = fetch_favorite_ids(user_id)
        except Exception:
            cart_items = []
            cart_count = 0
            cart_total = 0
            favorite_ids = set()

    return {
        "header_cart_items": cart_items[:4],
        "header_cart_count": cart_count,
        "header_cart_total": cart_total,
        "favorite_ids": favorite_ids,
    }


@app.route("/")
def home():
    products = []
    categories = []
    db_error = None
    try:
        products = fetch_products()[:6]
        categories = fetch_categories()
    except Exception as exc:
        db_error = str(exc)
    return render_template("index.html", products=products, categories=categories, db_error=db_error)


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        with db_cursor() as (_, cursor):
            cursor.execute(
                """
                SELECT user_id, name, email, role
                FROM users
                WHERE email = %s AND password_hash = %s
                """,
                (email, password),
            )
            user = cursor.fetchone()

        if user:
            session["user_id"] = user["user_id"]
            session["full_name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]
            flash("Welcome back to ZMart.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        phone = request.form.get("phone", "").strip()

        with db_cursor() as (_, cursor):
            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash, phone, role)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (full_name, email, password, phone, "customer"),
            )

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/products")
def products():
    db_error = None
    product_list = []
    categories = []
    selected_category = request.args.get("category", "").strip()
    search = request.args.get("search", "").strip()
    try:
        product_list = fetch_products()
        categories = fetch_categories()
        if selected_category:
            product_list = [product for product in product_list if str(product.get("category")) == selected_category]
        if search:
            product_list = [
                product
                for product in product_list
                if search.lower() in product.get("name", "").lower()
            ]
    except Exception as exc:
        db_error = str(exc)
    return render_template(
        "products.html",
        products=product_list,
        categories=categories,
        selected_category=selected_category,
        search=search,
        db_error=db_error,
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id):
    db_error = None
    product = None
    try:
        product = fetch_product_by_id(product_id)
    except Exception as exc:
        db_error = str(exc)

    if not product and not db_error:
        flash("Product not found.", "warning")
        return redirect(url_for("products"))

    return render_template("product_detail.html", product=product, db_error=db_error)


@app.route("/favorites")
@login_required
def favorites():
    db_error = None
    products = []
    try:
        products = fetch_favorite_products(session["user_id"])
    except Exception as exc:
        db_error = str(exc)
    return render_template("favorites.html", products=products, db_error=db_error)


@app.route("/favorites/toggle/<int:product_id>", methods=["POST"])
@login_required
def toggle_favorite(product_id):
    redirect_to = request.form.get("next") or request.referrer or url_for("products")
    try:
        with db_cursor() as (_, cursor):
            cursor.execute(
                "SELECT favorite_id FROM favorites WHERE user_id = %s AND product_id = %s",
                (session["user_id"], product_id),
            )
            favorite = cursor.fetchone()

            if favorite:
                cursor.execute(
                    "DELETE FROM favorites WHERE favorite_id = %s",
                    (favorite["favorite_id"],),
                )
                is_favorite = False
                flash("Removed from favourites.", "info")
            else:
                cursor.execute(
                    "INSERT INTO favorites (user_id, product_id) VALUES (%s, %s)",
                    (session["user_id"], product_id),
                )
                is_favorite = True
                flash("Added to favourites.", "success")
    except Exception as exc:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "message": str(exc)}), 400
        flash(f"Could not update favourites: {exc}", "danger")
        return redirect(redirect_to)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "is_favorite": is_favorite})

    return redirect(redirect_to)


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    if request.method == "POST":
        product_id = request.form.get("product_id")
        quantity = max(1, int(request.form.get("quantity", "1")))

        with db_cursor() as (_, cursor):
            cursor.execute(
                """
                SELECT product_id, name, stock_quantity
                FROM products
                WHERE product_id = %s
                """,
                (product_id,),
            )
            product = cursor.fetchone()

            if not product:
                flash("Product not found.", "warning")
                return redirect(url_for("products"))

            cursor.execute(
                """
                SELECT cart_id, quantity
                FROM cart
                WHERE user_id = %s AND product_id = %s
                ORDER BY cart_id ASC
                LIMIT 1
                """,
                (session["user_id"], product_id),
            )
            existing_item = cursor.fetchone()

            existing_quantity = existing_item["quantity"] if existing_item else 0
            if existing_quantity + quantity > product["stock_quantity"]:
                flash(
                    f"Only {product['stock_quantity']} units of {product['name']} are available right now.",
                    "warning",
                )
                return redirect(url_for("products"))

            if existing_item:
                cursor.execute(
                    """
                    UPDATE cart
                    SET quantity = %s
                    WHERE cart_id = %s AND user_id = %s
                    """,
                    (existing_quantity + quantity, existing_item["cart_id"], session["user_id"]),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO cart (user_id, product_id, quantity)
                    VALUES (%s, %s, %s)
                    """,
                    (session["user_id"], product_id, quantity),
                )

        flash("Item added to cart.", "success")
        return redirect(url_for("cart"))

    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            SELECT c.cart_id, c.product_id, c.quantity, p.name, p.price
            FROM cart c
            JOIN products p ON p.product_id = c.product_id
            WHERE c.user_id = %s
            """,
            (session["user_id"],),
        )
        cart_items = cursor.fetchall()

    total = sum(item["price"] * item["quantity"] for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total=total)


@app.route("/cart/remove/<int:cart_id>", methods=["POST"])
@login_required
def remove_cart_item(cart_id):
    try:
        with db_cursor() as (_, cursor):
            cursor.execute(
                "DELETE FROM cart WHERE cart_id = %s AND user_id = %s",
                (cart_id, session["user_id"]),
            )
        flash("Item removed from cart.", "info")
    except Exception as exc:
        flash(f"Could not remove item: {exc}", "danger")

    return redirect(url_for("cart"))


@app.route("/cart/update/<int:cart_id>", methods=["POST"])
@login_required
def update_cart_item(cart_id):
    action = request.form.get("action", "").strip()
    redirect_to = request.form.get("next") or request.referrer or url_for("cart")

    try:
        with db_cursor() as (_, cursor):
            cursor.execute(
                """
                SELECT c.quantity, p.stock_quantity, p.name
                FROM cart c
                JOIN products p ON p.product_id = c.product_id
                WHERE c.cart_id = %s AND c.user_id = %s
                """,
                (cart_id, session["user_id"]),
            )
            item = cursor.fetchone()

            if not item:
                flash("Cart item not found.", "warning")
                return redirect(redirect_to)

            quantity = item["quantity"]
            if action == "increase":
                if quantity >= item["stock_quantity"]:
                    flash(
                        f"Only {item['stock_quantity']} units of {item['name']} are available right now.",
                        "warning",
                    )
                    return redirect(redirect_to)
                quantity += 1
                cursor.execute(
                    "UPDATE cart SET quantity = %s WHERE cart_id = %s AND user_id = %s",
                    (quantity, cart_id, session["user_id"]),
                )
            elif action == "decrease":
                quantity -= 1
                if quantity <= 0:
                    cursor.execute(
                        "DELETE FROM cart WHERE cart_id = %s AND user_id = %s",
                        (cart_id, session["user_id"]),
                    )
                else:
                    cursor.execute(
                        "UPDATE cart SET quantity = %s WHERE cart_id = %s AND user_id = %s",
                        (quantity, cart_id, session["user_id"]),
                    )
    except Exception as exc:
        flash(f"Could not update quantity: {exc}", "danger")

    return redirect(redirect_to)


@app.route("/checkout", methods=["POST"])
@login_required
def checkout():
    with db_cursor() as (_, cursor):
        cursor.execute(
            """
            SELECT c.product_id, c.quantity, p.price, p.stock_quantity, p.name
            FROM cart c
            JOIN products p ON p.product_id = c.product_id
            WHERE c.user_id = %s
            """,
            (session["user_id"],),
        )
        cart_items = cursor.fetchall()

        if not cart_items:
            flash("Your cart is empty.", "warning")
            return redirect(url_for("cart"))

        for item in cart_items:
            if item["stock_quantity"] < item["quantity"]:
                flash(
                    f"Only {item['stock_quantity']} units of {item['name']} are available right now. Please update your cart.",
                    "warning",
                )
                return redirect(url_for("cart"))

        order_total = sum(item["price"] * item["quantity"] for item in cart_items)

        cursor.execute(
            """
            INSERT INTO orders (user_id, total_amount, status, delivery_address)
            VALUES (%s, %s, %s, %s)
            """,
            (session["user_id"], order_total, "pending", "Demo address for project"),
        )
        order_id = cursor.lastrowid

        for item in cart_items:
            cursor.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
                """,
                (order_id, item["product_id"], item["quantity"], item["price"]),
            )
            cursor.execute(
                """
                UPDATE products
                SET stock_quantity = stock_quantity - %s
                WHERE product_id = %s
                """,
                (item["quantity"], item["product_id"]),
            )

        cursor.execute("DELETE FROM cart WHERE user_id = %s", (session["user_id"],))

    flash("Order placed successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/orders")
@login_required
def orders():
    db_error = None
    pending_orders = []
    completed_orders = []
    is_manager_view = session.get("role") == "manager"

    try:
        pending_orders, completed_orders = fetch_orders(None if is_manager_view else session["user_id"])
    except Exception as exc:
        db_error = str(exc)

    return render_template(
        "orders.html",
        pending_orders=pending_orders,
        completed_orders=completed_orders,
        db_error=db_error,
        is_manager_view=is_manager_view,
    )


@app.route("/orders/<int:order_id>/mark-delivered", methods=["POST"])
@login_required
@role_required("admin", "manager")
def mark_order_delivered(order_id):
    try:
        with db_cursor() as (_, cursor):
            cursor.execute(
                """
                UPDATE orders
                SET status = 'delivered'
                WHERE order_id = %s
                """,
                (order_id,),
            )
        flash("Order marked as delivered.", "success")
    except Exception as exc:
        flash(f"Could not update order status: {exc}", "danger")

    return redirect(url_for("orders"))


@app.route("/admin", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager")
def admin():
    categories = []
    inventory_summary = {
        "product_count": 0,
        "total_stock_units": 0,
        "low_stock_count": 0,
        "category_count": 0,
    }
    is_manager = session.get("role") == "manager"

    if request.method == "POST":
        if is_manager:
            flash("Managers have view-only access.", "warning")
            return redirect(url_for("admin"))

        form = request.form
        with db_cursor() as (_, cursor):
            cursor.execute(
                """
                INSERT INTO products (category_id, name, description, price, stock_quantity, image_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    form.get("category"),
                    form.get("name"),
                    form.get("description"),
                    form.get("price"),
                    form.get("stock"),
                    form.get("image_url"),
                ),
            )

        flash("Product created successfully.", "success")
        return redirect(url_for("admin"))

    product_list = []
    db_error = None
    try:
        product_list = fetch_products()
        categories = fetch_categories()
        inventory_summary["product_count"] = len(product_list)
        inventory_summary["category_count"] = len(categories)
        inventory_summary["total_stock_units"] = sum(product["stock_quantity"] for product in product_list)
        inventory_summary["low_stock_count"] = sum(
            1 for product in product_list if product["stock_quantity"] <= 10
        )
    except Exception as exc:
        db_error = str(exc)
    return render_template(
        "admin.html",
        products=product_list,
        categories=categories,
        inventory_summary=inventory_summary,
        db_error=db_error,
        is_manager=is_manager,
    )


@app.route("/admin/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_product(product_id):
    db_error = None

    if request.method == "POST":
        form = request.form
        with db_cursor() as (_, cursor):
            cursor.execute(
                """
                UPDATE products
                SET category_id = %s,
                    name = %s,
                    description = %s,
                    price = %s,
                    stock_quantity = %s,
                    image_url = %s
                WHERE product_id = %s
                """,
                (
                    form.get("category"),
                    form.get("name"),
                    form.get("description"),
                    form.get("price"),
                    form.get("stock"),
                    form.get("image_url"),
                    product_id,
                ),
            )

        flash("Product updated successfully.", "success")
        return redirect(url_for("admin"))

    try:
        categories = fetch_categories()
        with db_cursor() as (_, cursor):
            cursor.execute(
                """
                SELECT product_id, category_id, name, description, price, stock_quantity, image_url
                FROM products
                WHERE product_id = %s
                """,
                (product_id,),
            )
            product = cursor.fetchone()
    except Exception as exc:
        categories = []
        product = None
        db_error = str(exc)

    return render_template("edit_product.html", product=product, categories=categories, db_error=db_error)


@app.route("/admin/delete/<int:product_id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_product(product_id):
    try:
        with db_cursor() as (_, cursor):
            cursor.execute("DELETE FROM cart WHERE product_id = %s", (product_id,))
            cursor.execute("DELETE FROM reviews WHERE product_id = %s", (product_id,))
            cursor.execute("DELETE FROM order_items WHERE product_id = %s", (product_id,))
            cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        flash("Product deleted successfully.", "success")
    except Exception as exc:
        flash(f"Could not delete product: {exc}", "danger")

    return redirect(url_for("admin"))


@app.route("/reports")
@login_required
@role_required("admin", "manager")
def reports():
    summary = {"user_count": 0, "product_count": 0, "order_count": 0, "sales_total": 0}
    db_error = None

    try:
        with db_cursor() as (_, cursor):
            cursor.execute("SELECT COUNT(*) AS count FROM users")
            summary["user_count"] = cursor.fetchone()["count"]
            cursor.execute("SELECT COUNT(*) AS count FROM products")
            summary["product_count"] = cursor.fetchone()["count"]
            cursor.execute("SELECT COUNT(*) AS count FROM orders")
            summary["order_count"] = cursor.fetchone()["count"]
            cursor.execute("SELECT COALESCE(SUM(total_amount), 0) AS total FROM orders")
            summary["sales_total"] = cursor.fetchone()["total"]
    except Exception as exc:
        db_error = str(exc)

    return render_template("reports.html", summary=summary, db_error=db_error)


@app.route("/ai-assistant", methods=["GET", "POST"])
def ai_assistant():
    assistant_result = None
    if request.method == "POST":
        assistant_result = generate_shopping_tip(request.form.get("prompt", ""))
    return render_template("ai_assistant.html", assistant_result=assistant_result)


@app.route("/api/ai-assistant", methods=["POST"])
def ai_api():
    prompt = request.json.get("prompt", "")
    return jsonify(generate_shopping_tip(prompt))


def generate_shopping_tip(prompt):
    original_prompt = (prompt or "").strip()
    normalized_prompt = original_prompt.lower()

    try:
        products = fetch_products()
    except Exception:
        products = []

    if not original_prompt:
        return {
            "success": True,
            "reply": "Ask me for ideas like a healthy basket, budget groceries under Rs. 500, party snacks, breakfast items, or cleaning supplies.",
            "recommendations": [],
        }

    budget_match = re.search(r"(?:under|below|within|budget)\s*(?:rs\.?|₹)?\s*(\d+)", normalized_prompt)
    budget = int(budget_match.group(1)) if budget_match else None

    keyword_groups = {
        "healthy": ["fruit", "fruits", "vegetable", "vegetables", "oats", "yogurt", "milk", "juice"],
        "protein": ["egg", "eggs", "paneer", "milk", "curd", "lentil", "nuts", "banana"],
        "party": ["chips", "snacks", "juice", "cola", "drink", "biscuits"],
        "breakfast": ["milk", "bread", "oats", "cornflakes", "banana", "juice", "biscuit"],
        "cleaning": ["soap", "surf", "vim", "clean", "detergent", "bar"],
    }
    category_preferences = {
        "healthy": ["fruits", "beverages"],
        "protein": ["fruits", "beverages", "snacks"],
        "party": ["snacks", "beverages"],
        "breakfast": ["beverages", "fruits", "snacks"],
        "cleaning": ["cleaning"],
    }

    detected_intent = None
    for intent, words in keyword_groups.items():
        if any(word in normalized_prompt for word in words):
            detected_intent = intent
            break

    matched_keywords = []
    for words in keyword_groups.values():
        if any(word in normalized_prompt for word in words):
            matched_keywords.extend(words)

    direct_terms = [term for term in re.findall(r"[a-zA-Z]+", normalized_prompt) if len(term) > 2]
    search_terms = list(dict.fromkeys(matched_keywords + direct_terms))

    scored_products = []
    for product in products:
        haystack = " ".join(
            [
                str(product.get("name", "")),
                str(product.get("category", "")),
                str(product.get("description", "")),
            ]
        ).lower()

        score = 0
        for term in search_terms:
            if term in haystack:
                score += 2

        if budget is not None and product.get("price", 0) <= budget:
            score += 1

        if score > 0:
            scored_products.append((score, product))

    if budget is not None and not scored_products:
        budget_products = [product for product in products if product.get("price", 0) <= budget]
        budget_products = sorted(budget_products, key=lambda item: (item["price"], -item["stock_quantity"]))[:5]
        total = sum(item["price"] for item in budget_products)
        return {
            "success": True,
            "reply": f"For a budget under Rs. {budget}, here are some affordable products currently available in ZMart.",
            "recommendations": [
                {
                    "product_id": item["product_id"],
                    "name": item["name"],
                    "category": item["category"],
                    "price": item["price"],
                    "stock_quantity": item["stock_quantity"],
                }
                for item in budget_products
            ],
            "summary": f"Suggested basket total: Rs. {total:.2f}",
        }

    if scored_products:
        ranked = [product for _, product in sorted(scored_products, key=lambda entry: (-entry[0], entry[1]["price"]))[:5]]
        summary = None
        if budget is not None:
            total = sum(item["price"] for item in ranked)
            summary = f"Suggested basket total: Rs. {total:.2f}"

        return {
            "success": True,
            "reply": build_assistant_reply(normalized_prompt, budget, ranked),
            "recommendations": [
                {
                    "product_id": item["product_id"],
                    "name": item["name"],
                    "category": item["category"],
                    "price": item["price"],
                    "stock_quantity": item["stock_quantity"],
                }
                for item in ranked
            ],
            "summary": summary,
        }

    fallback_products = []
    if detected_intent and detected_intent in category_preferences:
        preferred_categories = category_preferences[detected_intent]
        fallback_products = [
            product for product in products
            if str(product.get("category", "")).lower() in preferred_categories
        ][:5]

    if not fallback_products:
        fallback_products = sorted(products, key=lambda item: (-item["stock_quantity"], item["price"]))[:5]

    return {
        "success": True,
        "reply": build_fallback_reply(detected_intent),
        "recommendations": [
            {
                "product_id": item["product_id"],
                "name": item["name"],
                "category": item["category"],
                "price": item["price"],
                "stock_quantity": item["stock_quantity"],
            }
            for item in fallback_products
        ],
    }


def build_assistant_reply(normalized_prompt, budget, ranked_products):
    if "healthy" in normalized_prompt:
        return "Here are some healthier grocery picks from the current inventory that fit your request."
    if "protein" in normalized_prompt:
        return "These products are the strongest protein-oriented matches I found in the current inventory."
    if "party" in normalized_prompt:
        return "These products should work well for a party-style basket based on your request."
    if "breakfast" in normalized_prompt:
        return "Here are some breakfast-friendly picks from the current stock."
    if "clean" in normalized_prompt or "soap" in normalized_prompt or "detergent" in normalized_prompt:
        return "These are the closest cleaning and household matches available right now."
    if budget is not None:
        return f"Here are some relevant products I found for a budget around Rs. {budget}."
    return "Here are the closest product matches from the current ZMart inventory."


def build_fallback_reply(detected_intent):
    if detected_intent == "healthy":
        return "Based on the current inventory, these are the healthier options I can suggest right now."
    if detected_intent == "protein":
        return "Based on the current inventory, these are the closest protein-friendly options available right now."
    if detected_intent == "party":
        return "These are the closest party-friendly snacks and drinks available right now."
    if detected_intent == "breakfast":
        return "These are the closest breakfast-friendly items currently available in ZMart."
    if detected_intent == "cleaning":
        return "These are the cleaning and household items currently available in the store."
    return "Here are some useful products from the current inventory that you can explore right now."


if __name__ == "__main__":
    app.run(debug=True)
