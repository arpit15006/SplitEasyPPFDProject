from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from collections import defaultdict
import os

app = Flask(__name__)
app.secret_key = 'spliteasysecretkey'

# Detect if we are on Vercel or in a read-only environment to use /tmp
if os.environ.get('VERCEL') or os.environ.get('VERCEL_URL') or not os.access('.', os.W_OK):
    DATABASE = '/tmp/splitease.db'
else:
    DATABASE = 'splitease.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        paid_by INTEGER NOT NULL,
        description TEXT,
        FOREIGN KEY (paid_by) REFERENCES users(id)
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS expense_participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expense_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        FOREIGN KEY (expense_id) REFERENCES expenses(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    conn.commit()
    conn.close()

# Ensure the database tables exist (Vercel cold start)
init_db()

def calculate_settlements():
    conn = get_db()
    
    users = conn.execute('SELECT * FROM users').fetchall()
    if not users:
        return []
    
    balances = {user['id']: {'name': user['name'], 'paid': 0, 'share': 0} for user in users}
    
    expenses = conn.execute('SELECT * FROM expenses').fetchall()
    
    for expense in expenses:
        balances[expense['paid_by']]['paid'] += expense['amount']
        
        participants = conn.execute(
            'SELECT user_id FROM expense_participants WHERE expense_id = ?',
            (expense['id'],)
        ).fetchall()
        
        if participants:
            share_per_person = expense['amount'] / len(participants)
            for p in participants:
                balances[p['user_id']]['share'] += share_per_person
    
    conn.close()
    
    net_balances = {}
    for user_id, data in balances.items():
        net = data['paid'] - data['share']
        if abs(net) > 0.01:
            net_balances[user_id] = {'name': data['name'], 'balance': net}
    
    creditors = [(uid, data) for uid, data in net_balances.items() if data['balance'] > 0]
    debtors = [(uid, data) for uid, data in net_balances.items() if data['balance'] < 0]
    
    creditors.sort(key=lambda x: x[1]['balance'], reverse=True)
    debtors.sort(key=lambda x: x[1]['balance'])
    
    settlements = []
    i, j = 0, 0
    
    while i < len(creditors) and j < len(debtors):
        creditor_id, creditor_data = creditors[i]
        debtor_id, debtor_data = debtors[j]
        
        amount = min(creditor_data['balance'], -debtor_data['balance'])
        
        settlements.append({
            'from': debtor_data['name'],
            'to': creditor_data['name'],
            'amount': round(amount, 2)
        })
        
        creditor_data['balance'] -= amount
        debtor_data['balance'] += amount
        
        if creditor_data['balance'] < 0.01:
            i += 1
        if abs(debtor_data['balance']) < 0.01:
            j += 1
    
    return settlements

@app.route('/')
def index():
    conn = get_db()
    user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    expense_count = conn.execute('SELECT COUNT(*) as count FROM expenses').fetchone()['count']
    conn.close()
    return render_template('index.html', user_count=user_count, expense_count=expense_count)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Name cannot be empty', 'error')
            return redirect(url_for('add_user'))
        
        conn = get_db()
        try:
            conn.execute('INSERT INTO users (name) VALUES (?)', (name,))
            conn.commit()
            flash(f'User "{name}" added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash(f'User "{name}" already exists', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('add_user'))
    
    conn = get_db()
    users = conn.execute('SELECT * FROM users ORDER BY name').fetchall()
    conn.close()
    return render_template('add_user.html', users=users)

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    conn = get_db()
    users = conn.execute('SELECT * FROM users ORDER BY name').fetchall()
    
    if request.method == 'POST':
        if not users:
            flash('Please add users first', 'error')
            conn.close()
            return redirect(url_for('add_user'))
        
        amount = request.form.get('amount')
        paid_by = request.form.get('paid_by')
        description = request.form.get('description', '').strip()
        participants = request.form.getlist('participants')
        
        if not amount or not paid_by or not participants:
            flash('Please fill all required fields', 'error')
            conn.close()
            return redirect(url_for('add_expense'))
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash('Please enter a valid positive amount', 'error')
            conn.close()
            return redirect(url_for('add_expense'))
        
        cursor = conn.execute(
            'INSERT INTO expenses (amount, paid_by, description) VALUES (?, ?, ?)',
            (amount, paid_by, description)
        )
        expense_id = cursor.lastrowid
        
        for participant_id in participants:
            conn.execute(
                'INSERT INTO expense_participants (expense_id, user_id) VALUES (?, ?)',
                (expense_id, participant_id)
            )
        
        conn.commit()
        conn.close()
        flash('Expense added successfully!', 'success')
        return redirect(url_for('view_expenses'))
    
    conn.close()
    return render_template('add_expense.html', users=users)

@app.route('/view_expenses')
def view_expenses():
    conn = get_db()
    expenses = conn.execute('''
        SELECT e.id, e.amount, e.description, u.name as payer
        FROM expenses e
        JOIN users u ON e.paid_by = u.id
        ORDER BY e.id DESC
    ''').fetchall()
    
    expense_list = []
    for expense in expenses:
        participants = conn.execute('''
            SELECT u.name FROM users u
            JOIN expense_participants ep ON u.id = ep.user_id
            WHERE ep.expense_id = ?
        ''', (expense['id'],)).fetchall()
        
        expense_list.append({
            'id': expense['id'],
            'amount': expense['amount'],
            'description': expense['description'],
            'payer': expense['payer'],
            'participants': ', '.join([p['name'] for p in participants])
        })
    
    conn.close()
    return render_template('view_expenses.html', expenses=expense_list)

@app.route('/calculate')
def calculate():
    conn = get_db()
    user_count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    expense_count = conn.execute('SELECT COUNT(*) as count FROM expenses').fetchone()['count']
    conn.close()
    
    if user_count == 0:
        flash('Please add users first', 'error')
        return redirect(url_for('add_user'))
    
    if expense_count == 0:
        flash('No expenses to calculate', 'error')
        return redirect(url_for('add_expense'))
    
    settlements = calculate_settlements()
    return render_template('calculate.html', settlements=settlements)

@app.route('/delete_expense/<int:expense_id>')
def delete_expense(expense_id):
    conn = get_db()
    conn.execute('DELETE FROM expense_participants WHERE expense_id = ?', (expense_id,))
    conn.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    conn.commit()
    conn.close()
    flash('Expense deleted successfully', 'success')
    return redirect(url_for('view_expenses'))

@app.route('/reset_all')
def reset_all():
    conn = get_db()
    conn.execute('DELETE FROM expense_participants')
    conn.execute('DELETE FROM expenses')
    conn.execute('DELETE FROM users')
    conn.commit()
    conn.close()
    flash('All data has been reset', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
