# 💰 SplitEasy - Offline Bill Splitter

A simple, elegant web application to split bills and expenses among friends and groups. Built with Flask, SQLite, and pure HTML/CSS.

## 🚀 Features

- **User Management**: Add and manage group members
- **Expense Tracking**: Record expenses with payer and participants
- **Smart Calculations**: Automatically calculate who owes whom
- **Optimized Settlements**: Minimize number of transactions needed
- **Offline First**: Runs completely offline on localhost
- **Clean UI**: Modern, responsive design

## 📋 Requirements

- Python 3.7 or higher
- Flask

## 🛠️ Installation & Setup

1. **Navigate to project directory**
   ```bash
   cd "PPFD Project SplitEasy"
   ```

2. **Install Flask**
   ```bash
   pip install flask
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open in browser**
   ```
   http://127.0.0.1:5000
   ```

## 📁 Project Structure

```
PPFD Project SplitEasy/
│
├── app.py                  # Main Flask application
├── splitease.db           # SQLite database (auto-created)
├── templates/             # HTML templates
│   ├── base.html         # Base template
│   ├── index.html        # Home page
│   ├── add_user.html     # Add user page
│   ├── add_expense.html  # Add expense page
│   ├── view_expenses.html # View expenses page
│   └── calculate.html    # Settlement results page
└── static/
    └── css/
        └── style.css     # Stylesheet
```

## 🎯 How to Use

1. **Add Users**: Start by adding people to your group
2. **Add Expenses**: Record who paid and who should split the cost
3. **View Expenses**: See all recorded expenses in a table
4. **Calculate**: Get optimized settlement instructions
5. **Reset**: Clear all data when done

## 🧮 Settlement Algorithm

The app uses a greedy algorithm to minimize transactions:
1. Calculate net balance for each person (paid - share)
2. Separate into creditors (positive) and debtors (negative)
3. Match largest creditor with largest debtor
4. Settle and repeat until balanced

## 💡 Example

**Scenario:**
- Alice paid ₹300 (split among Alice, Bob, Charlie)
- Bob paid ₹150 (split among Alice, Bob)

**Result:**
- Alice's share: ₹175 (paid ₹300) → Should receive ₹125
- Bob's share: ₹175 (paid ₹150) → Owes ₹25
- Charlie's share: ₹100 (paid ₹0) → Owes ₹100

**Settlement:**
- Charlie pays Alice ₹100
- Bob pays Alice ₹25

## 🔒 Database Schema

**users**
- id (PRIMARY KEY)
- name (UNIQUE)

**expenses**
- id (PRIMARY KEY)
- amount (REAL)
- paid_by (FOREIGN KEY → users.id)
- description (TEXT)

**expense_participants**
- id (PRIMARY KEY)
- expense_id (FOREIGN KEY → expenses.id)
- user_id (FOREIGN KEY → users.id)

## 🎨 Technologies Used

- **Backend**: Python, Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Jinja2
- **Design**: Modern gradient UI with responsive layout

## 📝 Notes

- All data is stored locally in SQLite
- No internet connection required
- No JavaScript dependencies
- Perfect for college projects and small groups

## 👨‍💻 Author

Built as a college project demonstrating Flask, database operations, and algorithmic problem-solving.

---

**Enjoy splitting bills the easy way! 💰✨**
