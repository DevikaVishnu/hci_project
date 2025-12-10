# Visio ERP Dashboard

An Enterprise Resource Planning (ERP) for small-and-medium-sized businesses to enable better managerial decisions.

## Features

### 🔐 User Authentication
- **Login/Logout** - Secure session-based authentication
- **Registration** - Self-service account creation
- **Password Hashing** - Werkzeug security
- **Remember Me** - Persistent sessions
- **Role-Based Access** - Admin, Manager, User roles
- **User Management** - Admin can manage all users

### Dashboard
- Sales Overview, Order Status, Revenue by Category
- Income vs Expenses, Monthly Revenue, Expense Breakdown
- Team by Department

### Other Modules
- Customer Management
- Inventory & Products
- Order Management
- HR & Attendance
- Accounting & Reports

## Quick Start

```bash
cd visio
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
# Open http://localhost:5000
```

