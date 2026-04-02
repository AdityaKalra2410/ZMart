# ZMart

<p align="center">
  A modern supermarket web application built with Flask, MySQL, HTML, CSS, and JavaScript.
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python">
  <img alt="Flask" src="https://img.shields.io/badge/Flask-Backend-black?style=for-the-badge&logo=flask">
  <img alt="MySQL" src="https://img.shields.io/badge/MySQL-Database-orange?style=for-the-badge&logo=mysql">
  <img alt="HTML" src="https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JS-green?style=for-the-badge">
</p>

---

## About The Project

ZMart is an online supermarket management website.  
It allows users to register, log in, browse products, add items to cart, save favourites, and place orders.  
On the admin side, products can be added, edited, and deleted through a connected Flask + MySQL backend.

The project focuses on:
- frontend and backend integration
- proper relational database design
- role-based admin/customer flows
- dynamic product and cart management
- modern supermarket-style UI interactions

---

## Features

- User registration and login
- Product listing with search and category filtering
- Product detail page
- Add to cart and checkout flow
- Quantity increase/decrease in cart
- Remove items from cart
- Favourites system
- Mini cart drawer
- Admin product add, edit, and delete
- Reports dashboard
- AI assistant page
- Responsive homepage banners and offer sections

---

## Tech Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python
- Flask

### Database
- MySQL

### Other Tools
- Git
- GitHub

---

## Project Structure

```text
ZMart/
|-- app.py
|-- config.py
|-- db.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- templates/
|   |-- base.html
|   |-- index.html
|   |-- login.html
|   |-- register.html
|   |-- products.html
|   |-- product_detail.html
|   |-- cart.html
|   |-- favorites.html
|   |-- admin.html
|   |-- edit_product.html
|   |-- dashboard.html
|   |-- reports.html
|   |-- ai_assistant.html
|-- static/
|   |-- css/
|   |   |-- style.css
|   |-- js/
|       |-- app.js
|-- database/
|   |-- zmart_setup.sql
|   |-- grants_reference.sql
```

---

## Database Design

The main tables used in the project are:

- `users`
- `categories`
- `products`
- `cart`
- `orders`
- `order_items`
- `reviews`
- `favorites`

These tables are connected using primary keys and foreign keys to support proper DBMS relationships.

Database setup file:
- [`database/zmart_setup.sql`](database/zmart_setup.sql)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/AdityaKalra2410/ZMart.git
cd ZMart
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup the database

Open MySQL and run:

```sql
SOURCE database/zmart_setup.sql;
```

### 4. Configure database credentials

Update the values in [`config.py`](config.py):

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

### 5. Run the project

```bash
python app.py
```

Open in browser:

```text
http://127.0.0.1:5000
```

---

## Main Pages

- **Home Page**  
  Promotional banner, category cards, top offers, and featured products

- **Login / Register**  
  Customer authentication interface

- **Products Page**  
  Product cards, search, category filters, favourites, and add-to-cart actions

- **Product Detail Page**  
  Full product information with quantity selection

- **Cart Page**  
  Quantity update, remove item, and checkout

- **Favourites Page**  
  Saved products section

- **Admin Panel**  
  Add, edit, and delete products

- **Reports Page**  
  User, product, order, and sales summary

- **AI Assistant Page**  
  Shopping suggestion interface

---

## Frontend Highlights

The frontend was designed to resemble a modern online grocery platform and includes:

- sticky search bar
- promotional banner slider
- category cards
- offer cards
- product hover effects
- favourites toggle
- mini cart drawer
- floating AI assistant button

---

## Backend Highlights

The Flask backend handles:

- route management
- form submission
- login and session handling
- MySQL connectivity
- product CRUD operations
- cart and checkout flow
- favourites integration

---

## Future Improvements

- product image upload from local system
- order history page
- improved admin analytics
- payment gateway integration
- live search suggestions

---

## Team Members

- Aditya Kalra - 2024A7PS0536G
- Anuj P. Sarda - 2024A7PS0528G
- Jyot Kavi - 2024A7PS0594G
- Ved Aniruddha Joshi - 2024A7PS0542G
- Mayank Ajay Bhojwani - 2024A7PS0639G
- Sidhant Bhutani - 2024A7PS0535G

---

## Repository Link

Project Repository: [ZMart on GitHub](https://github.com/AdityaKalra2410/ZMart)
