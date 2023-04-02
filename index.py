from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2, logging
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__, static_folder='static')
app.secret_key = 'mysecretkey'
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

@app.route('/')
def index():
    return render_template('index.html')

# Hämta alla produkter från databasen
def get_products():
    conn = psycopg2.connect(host="pgserver.mau.se", dbname="an4135", user="an4135", password="w4or30ot")
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# Visa produkterna på products.html
@app.route('/products')
def products():
    products = get_products()
    return render_template('products.html', products=products)

@app.route('/add_customer', methods=['POST', 'GET'])
def add_customer():
    if request.method == 'POST':
        try:
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            password = request.form['password']
            email = request.form['email']
            address = request.form['address']
            city = request.form['city']
            country = request.form['country']
            phone_number = request.form['phone_number']
            
            conn = psycopg2.connect(
                host="pgserver.mau.se",
                database="an4135",
                user="an4135",
                password="w4or30ot"
            )
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO customers (first_name, last_name, password, email, address, city, country, phone_number)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (first_name, last_name, password, email, address, city, country, phone_number))
            conn.commit()
            cur.close()
            conn.close()
            
            return render_template('success.html', message='Customer added successfully!')
        
        except KeyError as e:
            return "Error: Missing field in form data - {}".format(e)

    return render_template('add_customer.html')

@app.route('/customer_orders/<int:customer_id>')
def customer_orders(customer_id):
    # Connect to database
    conn = psycopg2.connect(database='an4135', user='an4135', password='w4or30ot', host='pgserver.mau.se', port='5432')
    cur = conn.cursor()

    # Get orders for the given customer id
    cur.execute("SELECT orders.id, products.name, orders.quantity, orders.price, orders.confirmed FROM orders JOIN products ON orders.product_id = products.id WHERE orders.customer_id = %s", (customer_id,))
    orders = cur.fetchall()

    # Close the database connection
    cur.close()
    conn.close()

    # Render the template with the orders
    return render_template('logged_in.html', orders=orders)

@app.route('/delete_order/<int:order_id>')
def delete_order(order_id):
    # Connect to database
    conn = psycopg2.connect(database='an4135', user='an4135', password='w4or30ot', host='pgserver.mau.se', port='5432')
    cur = conn.cursor()

    # Get the order information
    cur.execute("SELECT product_id, quantity, confirmed FROM orders WHERE id = %s", (order_id,))
    order = cur.fetchone()

    # If the order has not been confirmed, delete it and update the product quantity
    if not order[2]:
        product_id = order[0]
        quantity = order[1]
        cur.execute("DELETE FROM orders WHERE id = %s", (order_id,))
        cur.execute("UPDATE products SET quantity = quantity + %s WHERE id = %s", (quantity, product_id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index'))
    else:
        # If the order has been confirmed, redirect to an error page
        cur.close()
        conn.close()
        return render_template('error.html', message='This order has already been confirmed and cannot be deleted.')


@app.route('/discount_history')
def discount_history():
    conn = psycopg2.connect(
        host="pgserver.mau.se",
        database="an4135",
        user="an4135",
        password="w4or30ot"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT dh.date_applied, p.name, d.discount_code, d.discount_percent, dh.final_price
        FROM discount_history dh
        INNER JOIN products p ON dh.product_id = p.id
        INNER JOIN discounts d ON dh.discount_id = d.id
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('discount_history.html', rows=rows)

@app.route('/customers')
def customers():
    """Displays a list of all customers."""
    customers = get_customers()
    return render_template('customers.html', customers=customers)

# function to retrieve all customers from the database
def get_customers():
    conn = psycopg2.connect(
        host="pgserver.mau.se",
        database="an4135",
        user="an4135",
        password="w4or30ot"
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

@app.route('/add_supplier', methods=['POST'])
def add_supplier():
    name = request.form['supplier_name']
    address = request.form['supplier_address']
    city = request.form['supplier_city']
    country = request.form['supplier_country']
    phone = request.form['supplier_phone']
    
    conn = psycopg2.connect(
        host="pgserver.mau.se",
        database="an4135",
        user="an4135",
        password="w4or30ot"
    )
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO suppliers (supplier_id, supplier_name, supplier_address, supplier_city, supplier_country, supplier_phone)
        VALUES (nextval('suppliers_supplier_id_seq'), %s, %s, %s, %s, %s)
        RETURNING supplier_id;
    """, (name, address, city, country, phone))

    conn.commit()
    cur.close()
    conn.close()
    
    return render_template('success.html', message='Supplier added successfully!')

# function to retrieve new orders from the database
def get_new_orders():
    conn = psycopg2.connect(
        host="pgserver.mau.se",
        database="an4135",
        user="an4135",
        password="w4or30ot"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT order_id, product_id, customer_id, order_date, order_quantity
        FROM orders
        WHERE order_status = 'new'
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def add_order_to_shoppinglist(product_id, customer_id, order_quantity, order_date):
    conn = psycopg2.connect(
        host="pgserver.mau.se",
        database="an4135",
        user="an4135",
        password="w4or30ot"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT price, quantity FROM products WHERE id = %s", (product_id,))
    price, available_quantity = cursor.fetchone()

    if int(order_quantity) > available_quantity:
        cursor.close()
        conn.close()
        raise ValueError(f"Only {available_quantity} units of product ID {product_id} are available")

    total_amount = price * int(order_quantity)
    cursor.execute("INSERT INTO orders (customer_id, order_date, total_amount) VALUES (%s, %s, %s) RETURNING order_id", (customer_id, order_date, total_amount))
    order_id = cursor.fetchone()[0]
    cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)", (order_id, product_id, int(order_quantity), price))
    cursor.execute("UPDATE products SET quantity = quantity - %s WHERE id = %s AND quantity >= %s", (int(order_quantity), product_id, int(order_quantity)))
    if cursor.rowcount == 0:
        cursor.close()
        conn.close()
        raise ValueError(f"Only {available_quantity} units of product ID {product_id} are available")
    conn.commit()
    cursor.close()
    conn.close()

def get_max_ordered_products():
    conn = psycopg2.connect(
        host="pgserver.mau.se",
        database="an4135",
        user="an4135",
        password="w4or30ot"
    )
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT ON (date_trunc('month', order_date), product_id)
            date_trunc('month', order_date) as month,
            product_id,
            count(*) as order_count
        FROM orders
        GROUP BY month, product_id
        ORDER BY month, order_count DESC
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@app.route('/suppliers')
def suppliers():
    """Displays a list of all suppliers."""
    suppliers = get_suppliers()
    return render_template('suppliers.html', suppliers=suppliers)


# function to update the order status to 'confirmed' in the database
def confirm_order(order_id):
    conn = psycopg2.connect(
        host="pgserver.mau.se",
        database="an4135",
        user="an4135",
        password="w4or30ot"
    )
    cur = conn.cursor()
    cur.execute("""
        UPDATE orders
        SET order_status = 'confirmed'
        WHERE order_id = %s
    """, (order_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_suppliers():
    """Retrieves a list of all suppliers from the database."""
    conn = psycopg2.connect(
        host="pgserver.mau.se",
        database="an4135",
        user="an4135",
        password="w4or30ot"
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM suppliers")
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

@app.route('/add_product', methods=['POST'])
def add_product():
    # anslut till databasen
    conn = psycopg2.connect(database='an4135', user='an4135', password='w4or30ot', host='pgserver.mau.se', port='5432')
    cur = conn.cursor()
    
    # hämta data från formuläret
    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    quantity = request.form['quantity']
    supplier_id = request.form['supplier_id']
    
    # lägg till produkten i databasen
    cur.execute("INSERT INTO products (name, description, price, quantity, supplier_id) VALUES (%s, %s, %s, %s, %s)", (name, description, price, quantity, supplier_id))
    # spara ändringarna i databasen och stäng anslutningen
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        login_query = f"SELECT * FROM customers WHERE email='{email}' AND password='{password}'"
        print(login_query)
        conn = psycopg2.connect(
            host="pgserver.mau.se",
            database="an4135",
            user="an4135",
            password="w4or30ot"
        )
        cursor = conn.cursor()
        cursor.execute(login_query)
        row = cursor.fetchone()
        print(row)
        if row:
            flash('You have been logged in!', 'success')
            session['logged_in'] = True
            session['customer_id'] = row[0]
            return redirect(url_for('logged_in'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')
            return render_template('login.html')
    else:
        return render_template('login.html')

'''
@app.route('/logged_in', methods=['GET', 'POST'])
def logged_in():
    if request.method == 'POST':
        product_id = request.form['product_id']
        customer_id = request.form['customer_id']
        order_quantity = request.form['quantity']
        add_order_to_shoppinglist(product_id, customer_id, order_quantity)
    
    conn = psycopg2.connect(
        host="pgserver.mau.se",
        database="an4135",
        user="an4135",
        password="w4or30ot"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('logged_in.html', products=products)
'''
@app.route('/logged_in', methods=['GET', 'POST'])
def logged_in():
    if request.method == 'POST':
        product_id = request.form['product_id']
        customer_id = request.form['customer_id']
        order_quantity = request.form['quantity']
        order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        add_order_to_shoppinglist(product_id, customer_id, order_quantity, order_date)
    
    conn = psycopg2.connect(
        host="pgserver.mau.se",
        database="an4135",
        user="an4135",
        password="w4or30ot"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('logged_in.html', products=products)






if __name__ == '__main__':
    app.run(debug=True)