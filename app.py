from functools import wraps

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


@app.context_processor
def inject_header_state():
    cart_items = []
    cart_count = 0
    cart_total = 0
    favorite_ids = set()

    user_id = session.get("user_id")
    if user_id:
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
        quantity = int(request.form.get("quantity", "1"))

        with db_cursor() as (_, cursor):
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
                "SELECT quantity FROM cart WHERE cart_id = %s AND user_id = %s",
                (cart_id, session["user_id"]),
            )
            item = cursor.fetchone()

            if not item:
                flash("Cart item not found.", "warning")
                return redirect(redirect_to)

            quantity = item["quantity"]
            if action == "increase":
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
            SELECT c.product_id, c.quantity, p.price
            FROM cart c
            JOIN products p ON p.product_id = c.product_id
            WHERE c.user_id = %s
            """,
            (session["user_id"],),
        )
        cart_items = cursor.fetchall()

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

        cursor.execute("DELETE FROM cart WHERE user_id = %s", (session["user_id"],))

    flash("Order placed successfully.", "success")
    return redirect(url_for("dashboard"))


@app.route("/admin", methods=["GET", "POST"])
@login_required
@role_required("admin", "editor")
def admin():
    categories = []
    if request.method == "POST":
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
    except Exception as exc:
        db_error = str(exc)
    return render_template("admin.html", products=product_list, categories=categories, db_error=db_error)


@app.route("/admin/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
@role_required("admin", "editor")
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
@role_required("admin", "editor")
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
@role_required("admin", "editor", "viewer")
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
    suggestion = None
    if request.method == "POST":
        suggestion = generate_shopping_tip(request.form.get("prompt", "").lower())
    return render_template("ai_assistant.html", suggestion=suggestion)


@app.route("/api/ai-assistant", methods=["POST"])
def ai_api():
    prompt = request.json.get("prompt", "")
    return jsonify({"response": generate_shopping_tip(prompt.lower())})


def generate_shopping_tip(prompt):
    if "budget" in prompt:
        return "For a budget-friendly basket, try rice, milk, eggs, bread, bananas, and seasonal vegetables."
    if "protein" in prompt:
        return "High-protein picks: paneer, eggs, curd, peanuts, lentils, and soya chunks."
    if "party" in prompt:
        return "For a party, stock soft drinks, chips, dips, paper cups, ice cream, and easy-to-serve snacks."
    if "healthy" in prompt:
        return "Healthy shopping list: oats, fruits, green vegetables, brown bread, sprouts, and yogurt."
    return "Try searching by need, such as budget groceries, healthy items, protein-rich foods, or party supplies."


if __name__ == "__main__":
    app.run(debug=True)
