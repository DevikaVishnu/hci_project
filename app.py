"""
Visio Dashboard
A simplified Enterprise Resource Planning (ERP) system for educational purposes.
Inspired by ERPNext - https://github.com/frappe/erpnext

Features:
- User Authentication (Login/Logout/Register)
- Dashboard with KPIs and charts
- Sales Management (Customers, Orders, Invoices)
- Inventory Management (Products, Stock)
- HR Management (Employees, Attendance)
- Basic Accounting (Transactions, Reports)

Built with Flask + SQLite + Flask-Login for simplicity.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'visio-secret-key-2025-very-secure'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///visio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


# =============================================================================
# DATABASE MODELS
# =============================================================================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_initials(self):
        names = self.full_name.split()
        if len(names) >= 2:
            return f"{names[0][0]}{names[1][0]}".upper()
        return self.full_name[:2].upper()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    orders = db.relationship('Order', backref='customer', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50))
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, default=0)
    stock_quantity = db.Column(db.Integer, default=0)
    min_stock_level = db.Column(db.Integer, default=10)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'sku': self.sku, 'price': self.price, 'stock_quantity': self.stock_quantity}


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    total_amount = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(50))
    position = db.Column(db.String(50))
    salary = db.Column(db.Float, default=0)
    hire_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attendances = db.relationship('Attendance', backref='employee', lazy=True)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    status = db.Column(db.String(20), default='present')


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(50))
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    reference = db.Column(db.String(100))
    date = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def generate_order_number():
    return f"ORD-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"


def generate_employee_id():
    return f"EMP-{random.randint(10000, 99999)}"


def get_dashboard_stats():
    return {
        'total_orders': Order.query.count(),
        'total_revenue': db.session.query(db.func.sum(Order.total_amount)).filter(Order.status != 'cancelled').scalar() or 0,
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'total_customers': Customer.query.count(),
        'total_products': Product.query.count(),
        'low_stock_count': Product.query.filter(Product.stock_quantity <= Product.min_stock_level).count(),
        'total_employees': Employee.query.filter_by(status='active').count(),
        'total_income': db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.transaction_type == 'income').scalar() or 0,
        'total_expense': db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.transaction_type == 'expense').scalar() or 0,
        'net_profit': (db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.transaction_type == 'income').scalar() or 0) - (db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.transaction_type == 'expense').scalar() or 0)
    }


def get_sales_chart_data():
    data = []
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        daily_sales = db.session.query(db.func.sum(Order.total_amount)).filter(db.func.date(Order.created_at) == date, Order.status != 'cancelled').scalar() or 0
        data.append({'date': date.strftime('%b %d'), 'sales': round(daily_sales, 2)})
    return data


def get_order_status_data():
    return [{'status': s.capitalize(), 'count': Order.query.filter_by(status=s).count()} for s in ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']]


def get_top_products():
    results = db.session.query(Product.name, db.func.sum(OrderItem.quantity).label('total_sold')).join(OrderItem).group_by(Product.id).order_by(db.func.sum(OrderItem.quantity).desc()).limit(5).all()
    return [{'name': r[0], 'sold': r[1] or 0} for r in results]


def get_revenue_by_category():
    results = db.session.query(Product.category, db.func.sum(OrderItem.quantity * OrderItem.unit_price).label('revenue')).join(OrderItem).join(Order).filter(Order.status != 'cancelled').group_by(Product.category).all()
    return [{'category': r[0] or 'Uncategorized', 'revenue': round(r[1] or 0, 2)} for r in results]


def get_monthly_revenue():
    data = []
    for i in range(5, -1, -1):
        date = datetime.now().date() - timedelta(days=i*30)
        month_start = date.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1) if i > 0 else datetime.now().date() + timedelta(days=1)
        monthly_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(Order.created_at >= month_start, Order.created_at < next_month, Order.status != 'cancelled').scalar() or 0
        data.append({'month': month_start.strftime('%b'), 'revenue': round(monthly_revenue, 2)})
    return data


def get_expense_by_category():
    results = db.session.query(Transaction.category, db.func.sum(Transaction.amount).label('total')).filter(Transaction.transaction_type == 'expense').group_by(Transaction.category).all()
    return [{'category': r[0] or 'Other', 'amount': round(r[1] or 0, 2)} for r in results]


def get_employee_by_department():
    results = db.session.query(Employee.department, db.func.count(Employee.id).label('count')).filter(Employee.status == 'active').group_by(Employee.department).all()
    return [{'department': r[0] or 'Unassigned', 'count': r[1]} for r in results]


def get_income_vs_expense():
    data = []
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        daily_income = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.date == date, Transaction.transaction_type == 'income').scalar() or 0
        daily_expense = db.session.query(db.func.sum(Transaction.amount)).filter(Transaction.date == date, Transaction.transaction_type == 'expense').scalar() or 0
        data.append({'date': date.strftime('%b %d'), 'income': round(daily_income, 2), 'expense': round(daily_expense, 2)})
    return data


# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact administrator.', 'error')
                return render_template('login.html')
            
            login_user(user, remember=remember)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        
        if not email or not password or not full_name:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'error')
            return render_template('register.html')
        
        user = User(email=email, full_name=full_name)
        user.set_password(password)
        if User.query.count() == 0:
            user.role = 'admin'
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        new_password = request.form.get('new_password', '')
        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters.', 'error')
                return render_template('profile.html')
            current_user.set_password(new_password)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    return render_template('profile.html')


@app.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=all_users)


@app.route('/users/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash(f'User {user.full_name} has been {"activated" if user.is_active else "deactivated"}.', 'success')
    return redirect(url_for('users'))


@app.route('/users/role/<int:id>', methods=['POST'])
@login_required
@admin_required
def change_role(id):
    user = User.query.get_or_404(id)
    new_role = request.form.get('role', 'user')
    if new_role in ['admin', 'manager', 'user']:
        user.role = new_role
        db.session.commit()
        flash(f'User role updated to {new_role}.', 'success')
    return redirect(url_for('users'))


# =============================================================================
# DASHBOARD ROUTE
# =============================================================================

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html',
        stats=get_dashboard_stats(),
        sales_data=get_sales_chart_data(),
        order_status_data=get_order_status_data(),
        top_products=get_top_products(),
        recent_orders=Order.query.order_by(Order.created_at.desc()).limit(5).all(),
        low_stock_products=Product.query.filter(Product.stock_quantity <= Product.min_stock_level).limit(5).all(),
        revenue_by_category=get_revenue_by_category(),
        monthly_revenue=get_monthly_revenue(),
        expense_by_category=get_expense_by_category(),
        employee_by_dept=get_employee_by_department(),
        income_vs_expense=get_income_vs_expense())


# =============================================================================
# CRUD ROUTES (Customers, Products, Orders, Employees, etc.)
# =============================================================================

@app.route('/customers')
@login_required
def customers():
    return render_template('customers.html', customers=Customer.query.order_by(Customer.created_at.desc()).all())

@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        db.session.add(Customer(name=request.form['name'], email=request.form['email'], phone=request.form.get('phone'), address=request.form.get('address'), created_by=current_user.id))
        db.session.commit()
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=None)

@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    customer = Customer.query.get_or_404(id)
    if request.method == 'POST':
        customer.name, customer.email, customer.phone, customer.address = request.form['name'], request.form['email'], request.form.get('phone'), request.form.get('address')
        db.session.commit()
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customers'))
    return render_template('customer_form.html', customer=customer)

@app.route('/customers/delete/<int:id>', methods=['POST'])
@login_required
def delete_customer(id):
    db.session.delete(Customer.query.get_or_404(id))
    db.session.commit()
    flash('Customer deleted successfully!', 'success')
    return redirect(url_for('customers'))

@app.route('/products')
@login_required
def products():
    return render_template('products.html', products=Product.query.order_by(Product.created_at.desc()).all())

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        db.session.add(Product(name=request.form['name'], sku=request.form['sku'], category=request.form.get('category'), price=float(request.form['price']), cost=float(request.form.get('cost', 0)), stock_quantity=int(request.form.get('stock_quantity', 0)), min_stock_level=int(request.form.get('min_stock_level', 10)), description=request.form.get('description')))
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', product=None)

@app.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name, product.sku, product.category = request.form['name'], request.form['sku'], request.form.get('category')
        product.price, product.cost = float(request.form['price']), float(request.form.get('cost', 0))
        product.stock_quantity, product.min_stock_level = int(request.form.get('stock_quantity', 0)), int(request.form.get('min_stock_level', 10))
        product.description = request.form.get('description')
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))
    return render_template('product_form.html', product=product)

@app.route('/products/delete/<int:id>', methods=['POST'])
@login_required
def delete_product(id):
    db.session.delete(Product.query.get_or_404(id))
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products'))

@app.route('/products/adjust-stock/<int:id>', methods=['POST'])
@login_required
def adjust_stock(id):
    product = Product.query.get_or_404(id)
    product.stock_quantity = max(0, product.stock_quantity + int(request.form.get('adjustment', 0)))
    db.session.commit()
    flash('Stock adjusted.', 'success')
    return redirect(url_for('products'))

@app.route('/orders')
@login_required
def orders():
    return render_template('orders.html', orders=Order.query.order_by(Order.created_at.desc()).all())

@app.route('/orders/add', methods=['GET', 'POST'])
@login_required
def add_order():
    if request.method == 'POST':
        order = Order(order_number=generate_order_number(), customer_id=int(request.form['customer_id']), status='pending', created_by=current_user.id)
        db.session.add(order)
        db.session.flush()
        total = 0
        for pid, qty in zip(request.form.getlist('product_id[]'), request.form.getlist('quantity[]')):
            if pid and qty:
                product = Product.query.get(int(pid))
                if product:
                    db.session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=int(qty), unit_price=product.price))
                    total += product.price * int(qty)
                    product.stock_quantity = max(0, product.stock_quantity - int(qty))
        order.total_amount = total
        db.session.add(Transaction(transaction_type='income', category='Sales', amount=total, description=f'Order {order.order_number}', reference=order.order_number, date=datetime.now().date(), created_by=current_user.id))
        db.session.commit()
        flash('Order created successfully!', 'success')
        return redirect(url_for('orders'))
    return render_template('order_form.html', order=None, customers=Customer.query.all(), products=Product.query.filter(Product.stock_quantity > 0).all())

@app.route('/orders/view/<int:id>')
@login_required
def view_order(id):
    return render_template('order_view.html', order=Order.query.get_or_404(id))

@app.route('/orders/update-status/<int:id>', methods=['POST'])
@login_required
def update_order_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form.get('status')
    if new_status in ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']:
        order.status = new_status
        db.session.commit()
        flash(f'Order status updated to {new_status}.', 'success')
    return redirect(url_for('orders'))

@app.route('/orders/delete/<int:id>', methods=['POST'])
@login_required
def delete_order(id):
    db.session.delete(Order.query.get_or_404(id))
    db.session.commit()
    flash('Order deleted successfully!', 'success')
    return redirect(url_for('orders'))

@app.route('/employees')
@login_required
def employees():
    return render_template('employees.html', employees=Employee.query.order_by(Employee.created_at.desc()).all())

@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date() if request.form.get('hire_date') else None
        db.session.add(Employee(employee_id=generate_employee_id(), name=request.form['name'], email=request.form['email'], department=request.form.get('department'), position=request.form.get('position'), salary=float(request.form.get('salary', 0)), hire_date=hire_date, status='active'))
        db.session.commit()
        flash('Employee added successfully!', 'success')
        return redirect(url_for('employees'))
    return render_template('employee_form.html', employee=None)

@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)
    if request.method == 'POST':
        employee.name, employee.email = request.form['name'], request.form['email']
        employee.department, employee.position = request.form.get('department'), request.form.get('position')
        employee.salary, employee.status = float(request.form.get('salary', 0)), request.form.get('status', 'active')
        if request.form.get('hire_date'):
            employee.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date()
        db.session.commit()
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('employees'))
    return render_template('employee_form.html', employee=employee)

@app.route('/employees/delete/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    db.session.delete(Employee.query.get_or_404(id))
    db.session.commit()
    flash('Employee deleted successfully!', 'success')
    return redirect(url_for('employees'))

@app.route('/attendance')
@login_required
def attendance():
    today = datetime.now().date()
    return render_template('attendance.html', attendances=Attendance.query.filter_by(date=today).all(), employees=Employee.query.filter_by(status='active').all(), today=today)

@app.route('/attendance/mark', methods=['POST'])
@login_required
def mark_attendance():
    employee_id, date = int(request.form['employee_id']), datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    status = request.form.get('status', 'present')
    existing = Attendance.query.filter_by(employee_id=employee_id, date=date).first()
    if existing:
        existing.status = status
        if request.form.get('check_in'): existing.check_in = datetime.strptime(request.form['check_in'], '%H:%M').time()
        if request.form.get('check_out'): existing.check_out = datetime.strptime(request.form['check_out'], '%H:%M').time()
    else:
        att = Attendance(employee_id=employee_id, date=date, status=status)
        if request.form.get('check_in'): att.check_in = datetime.strptime(request.form['check_in'], '%H:%M').time()
        if request.form.get('check_out'): att.check_out = datetime.strptime(request.form['check_out'], '%H:%M').time()
        db.session.add(att)
    db.session.commit()
    flash('Attendance marked successfully!', 'success')
    return redirect(url_for('attendance'))

@app.route('/transactions')
@login_required
def transactions():
    txns = Transaction.query.order_by(Transaction.date.desc()).all()
    return render_template('transactions.html', transactions=txns, total_income=sum(t.amount for t in txns if t.transaction_type == 'income'), total_expense=sum(t.amount for t in txns if t.transaction_type == 'expense'))

@app.route('/transactions/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        db.session.add(Transaction(transaction_type=request.form['transaction_type'], category=request.form.get('category'), amount=float(request.form['amount']), description=request.form.get('description'), reference=request.form.get('reference'), date=datetime.strptime(request.form['date'], '%Y-%m-%d').date() if request.form.get('date') else datetime.now().date(), created_by=current_user.id))
        db.session.commit()
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('transactions'))
    return render_template('transaction_form.html', transaction=None)

@app.route('/transactions/delete/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    db.session.delete(Transaction.query.get_or_404(id))
    db.session.commit()
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('transactions'))

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/reports/sales')
@login_required
def sales_report():
    start_date, end_date = request.args.get('start_date'), request.args.get('end_date')
    query = Order.query.filter(Order.status != 'cancelled')
    if start_date: query = query.filter(Order.created_at >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date: query = query.filter(Order.created_at <= datetime.strptime(end_date, '%Y-%m-%d'))
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template('report_sales.html', orders=orders, total_sales=sum(o.total_amount for o in orders), start_date=start_date, end_date=end_date)

@app.route('/reports/inventory')
@login_required
def inventory_report():
    products = Product.query.all()
    return render_template('report_inventory.html', products=products, total_value=sum(p.price * p.stock_quantity for p in products), low_stock=[p for p in products if p.stock_quantity <= p.min_stock_level], out_of_stock=[p for p in products if p.stock_quantity == 0])

@app.route('/reports/financial')
@login_required
def financial_report():
    txns = Transaction.query.order_by(Transaction.date.desc()).all()
    income_by_cat, expense_by_cat = {}, {}
    for t in txns:
        if t.transaction_type == 'income': income_by_cat[t.category] = income_by_cat.get(t.category, 0) + t.amount
        else: expense_by_cat[t.category] = expense_by_cat.get(t.category, 0) + t.amount
    return render_template('report_financial.html', income_by_category=income_by_cat, expense_by_category=expense_by_cat, total_income=sum(income_by_cat.values()), total_expense=sum(expense_by_cat.values()))

@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    return jsonify(get_dashboard_stats())

@app.route('/api/products/search')
@login_required
def api_search_products():
    return jsonify([p.to_dict() for p in Product.query.filter(Product.name.ilike(f'%{request.args.get("q", "")}%')).limit(10).all()])


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_sample_data():
    if Customer.query.first(): return
    
    for c in [{'name': 'Acme Corporation', 'email': 'contact@acme.com', 'phone': '555-0101', 'address': '123 Business Ave'},
              {'name': 'TechStart Inc', 'email': 'hello@techstart.io', 'phone': '555-0102', 'address': '456 Innovation Blvd'},
              {'name': 'Global Traders', 'email': 'info@globaltraders.com', 'phone': '555-0103', 'address': '789 Commerce St'},
              {'name': 'Local Shop', 'email': 'shop@local.com', 'phone': '555-0104', 'address': '321 Main Street'},
              {'name': 'Digital Solutions', 'email': 'support@digitalsolutions.net', 'phone': '555-0105', 'address': '654 Tech Park'}]:
        db.session.add(Customer(**c))
    
    for p in [{'name': 'Laptop Pro 15', 'sku': 'LP-001', 'category': 'Electronics', 'price': 1299.99, 'cost': 900, 'stock_quantity': 50, 'min_stock_level': 10},
              {'name': 'Wireless Mouse', 'sku': 'WM-002', 'category': 'Accessories', 'price': 29.99, 'cost': 15, 'stock_quantity': 200, 'min_stock_level': 50},
              {'name': 'USB-C Hub', 'sku': 'UC-003', 'category': 'Accessories', 'price': 59.99, 'cost': 30, 'stock_quantity': 100, 'min_stock_level': 20},
              {'name': 'Monitor 27"', 'sku': 'MN-004', 'category': 'Electronics', 'price': 349.99, 'cost': 200, 'stock_quantity': 30, 'min_stock_level': 10},
              {'name': 'Keyboard Mechanical', 'sku': 'KM-005', 'category': 'Accessories', 'price': 89.99, 'cost': 50, 'stock_quantity': 75, 'min_stock_level': 15},
              {'name': 'Webcam HD', 'sku': 'WC-006', 'category': 'Electronics', 'price': 79.99, 'cost': 40, 'stock_quantity': 60, 'min_stock_level': 15},
              {'name': 'Desk Lamp LED', 'sku': 'DL-007', 'category': 'Office', 'price': 45.99, 'cost': 20, 'stock_quantity': 8, 'min_stock_level': 10},
              {'name': 'Notebook Pack', 'sku': 'NP-008', 'category': 'Office', 'price': 12.99, 'cost': 5, 'stock_quantity': 5, 'min_stock_level': 20}]:
        db.session.add(Product(**p))
    
    for e in [{'name': 'John Smith', 'email': 'john.smith@company.com', 'department': 'Sales', 'position': 'Manager', 'salary': 75000},
              {'name': 'Sarah Johnson', 'email': 'sarah.j@company.com', 'department': 'Engineering', 'position': 'Senior', 'salary': 85000},
              {'name': 'Mike Wilson', 'email': 'mike.w@company.com', 'department': 'HR', 'position': 'Manager', 'salary': 65000},
              {'name': 'Emily Brown', 'email': 'emily.b@company.com', 'department': 'Finance', 'position': 'Director', 'salary': 95000},
              {'name': 'David Lee', 'email': 'david.l@company.com', 'department': 'Marketing', 'position': 'Senior', 'salary': 70000}]:
        db.session.add(Employee(employee_id=generate_employee_id(), hire_date=datetime.now().date() - timedelta(days=random.randint(30, 365)), **e))
    
    db.session.commit()
    
    customers, products = Customer.query.all(), Product.query.all()
    for i in range(15):
        customer = random.choice(customers)
        order_date = datetime.now() - timedelta(days=random.randint(0, 30))
        order = Order(order_number=f"ORD-{order_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}", customer_id=customer.id, status=random.choice(['pending', 'confirmed', 'shipped', 'delivered']), created_at=order_date)
        db.session.add(order)
        db.session.flush()
        total = 0
        for _ in range(random.randint(1, 4)):
            product = random.choice(products)
            qty = random.randint(1, 5)
            db.session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=qty, unit_price=product.price))
            total += product.price * qty
        order.total_amount = total
        db.session.add(Transaction(transaction_type='income', category='Sales', amount=total, description=f'Order {order.order_number}', reference=order.order_number, date=order.created_at.date()))
    
    for cat in ['Rent', 'Utilities', 'Salaries', 'Marketing', 'Supplies', 'Equipment', 'Software']:
        db.session.add(Transaction(transaction_type='expense', category=cat, amount=random.randint(200, 3000), description='Business expense', date=datetime.now().date() - timedelta(days=random.randint(0, 30))))
    
    db.session.commit()
    print("Sample data initialized!")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        init_sample_data()
    app.run(debug=True, host='0.0.0.0', port=5000)
