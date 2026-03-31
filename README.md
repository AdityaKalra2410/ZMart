# ZMart

ZMart is a supermarket web application built using Flask, MySQL, HTML, CSS, and JavaScript.

It includes:
- customer login and registration
- product listing and product detail page
- cart and checkout flow
- admin product management
- reports page
- AI assistant page

## Tech Stack

- Python Flask
- MySQL
- HTML
- CSS
- JavaScript

## Project Structure

```text
ZMart/
├── app.py
├── config.py
├── db.py
├── requirements.txt
├── templates/
├── static/
└── database/
```

## Database Setup

1. Open MySQL.
2. Run the SQL file:

```sql
SOURCE database/zmart_setup.sql;
```

Or open and execute:

[`database/zmart_setup.sql`](C:\Users\OMEN\Documents\ZMart\database\zmart_setup.sql)

## Install Dependencies

Open terminal in the project folder and run:

```powershell
pip install -r requirements.txt
```

## Configure Database

Update MySQL settings in:

[`config.py`](C:\Users\OMEN\Documents\ZMart\config.py)

Make sure these match your system:
- MySQL host
- MySQL port
- MySQL username
- MySQL password
- database name

## Run the Project

```powershell
python app.py
```

Then open:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

## Main Features

- homepage with search and category browsing
- products page with filters
- product detail page
- register and login
- cart and checkout
- admin product add, edit, and delete
- reports dashboard
- AI shopping assistant

## Demo Accounts

You can create accounts from the register page, or insert admin/customer users directly into the `users` table.

## Notes

- MySQL must be running before starting Flask.
- The project uses your local MySQL database.
- Product images are currently added using image URLs.
