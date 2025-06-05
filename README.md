# 🧾 Smart Expense Tracker (Voice Input Enabled)

A web-based expense tracking application built with **Flask** that allows users to **log expenses using voice input**, **categorize spending**, **visualize data through charts**, and **generate monthly reports**. Designed for simplicity, accessibility, and intelligent personal finance management.

---

## 🚀 Features

- 🎙️ **Voice Input**: Log expenses by speaking, powered by Python's `SpeechRecognition` library.
- 📊 **Visual Reports**: Pie chart breakdown of expenses by category.
- 📅 **Monthly Report**: Get insights into your spending patterns.
- 📁 **Category-wise Tracking**: Automatically categorize transactions.
- 🧠 **Smart Analysis (Coming Soon)**: Suggestions and alerts based on spending behavior.

---

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript (Bootstrap for styling)
- **Database**: SQLite
- **Libraries**:
  - `SpeechRecognition` – for capturing voice input
  - `Pandas` – for managing expense data
  - `Matplotlib` – for generating charts
  - `Flask` – for routing and backend logic

---

## 📂 Project Structure
SmartBudget/
  SmartExpenseTracker/
  │
  ├── static/ # CSS, JS, assets
  ├── templates/ # HTML templates
  │ ├── index.html
  │ ├── report.html
  │ └── ...
  ├── app.py # Main Flask app
  ├── create_db.py
  ├── smart_budget.db # SQLite database
Readme.md

---
