from flask import Flask, render_template, request, redirect, url_for, session,flash,jsonify,send_file
import pandas as pd
import io
import sqlite3
import cloudinary
import cloudinary.uploader
import re
from datetime import datetime, timedelta
import speech_recognition as sr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time




# Configuration       
cloudinary.config( 
    cloud_name = "dwijp5leb", 
    api_key = "864231856938149", 
    api_secret = "H80FxIMM-Sm8qR8msmWV2DXaMbI", # Click 'View API Keys' above to copy your API secret
    secure=True
)

app = Flask(__name__)
app.secret_key = 'secret_key098098'

def get_db_connection():
    try:
        conn = sqlite3.connect('smart_budget.db')
        conn.row_factory = sqlite3.Row  # To get dictionary-like results
        return conn
    except:
        print("DB CONNECTION ERROR")


@app.route('/index',methods=['GET','POST'])
def index():
    if 'user_id' in session:
        return redirect(url_for('home'))
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        username = username.lower()
        
        # Here, you can add the logic to save the user data to your database.
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            user = cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
        except:
            print("No User")

        if user:
            error = "Email is already registered. Please log in."
            return render_template('login.html', error=error)
        try:
            cursor.execute('INSERT INTO users (username,email,password) VALUES (?,?,?)', (username,email, password))
            conn.commit()
        except:
            print("Cant Insert username email and pass")
        finally:
            cursor.close()
            conn.close()

        # For now, let's just print the user data.
        print(f"Username: {username}, Email: {email}, Password: {password}")
        
        success = "Registration SuccessFull Please Log in"
        return render_template('login.html',success=success)
    
    # Render the signup page when accessed via GET
    return render_template('login.html')
    
        
@app.route('/delete_user', methods=['GET','POST'])
def delete_user():
    if 'user_id' in session:
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            existing_image = cursor.execute("SELECT profile_pic FROM users WHERE id = ?", (session['user_id'],)).fetchone()
            if existing_image and existing_image[0] and existing_image[0] != "None":
                public_id = extract_public_id(existing_image[0])
                if public_id:
                    cloudinary.uploader.destroy(public_id)
            
            cursor.execute('DELETE From reports where user_id = ?',(user_id,))
            cursor.execute('DELETE From saving_goal where user_id = ?',(user_id,))
            cursor.execute('DELETE From users where id = ?',(user_id,))
            cursor.execute('DELETE From transactions where user_id = ?',(user_id,))

            conn.commit()
        except sqlite3.Error as e:
            print("DB ERROR -",e)
        finally:
            cursor.close()
            conn.close()
        session.clear()
        return redirect(url_for('index'))
    return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Check if the user exists and the password is correct
        conn = get_db_connection()
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
        cursor.close()
        conn.close()

        if user:
            # Store user information in session
            session['user_id'] = user['id']
            session['username'] = user['username']
            username = session['username']
            if user['first_login'] == 1:
                return render_template('user_data.html',username=username)
            return redirect(url_for('home'))
        
        else:
            error = "Incorrect username or password"
            return render_template('login.html', error=error)

    return render_template('login.html')



@app.route('/user_data', methods=['GET', 'POST'])

def user_data():
    if 'user_id' in session:
        full_name = request.form.get('full_name')  # Use get() to avoid errors
        ph_num = request.form.get('ph_num')
        dob = request.form.get('DOB')
        current_balance = request.form.get('current_balance')
        full_name = full_name.upper()
        # Check if form data is received
        print(f"Received data: {full_name}, {ph_num}, {dob}, {current_balance}")

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''UPDATE users 
                              SET full_name = ?, ph_num = ?, DOB = ?, current_balance = ? 
                              WHERE id = ?''', 
                           (full_name, ph_num, dob, current_balance, session['user_id']))

            cursor.execute('''INSERT INTO reports (user_id, total_income, total_expense,    total_balance) 
                  VALUES (?, 0, 0, ?)
                  ON CONFLICT(user_id) DO UPDATE SET total_balance = ?''', 
                 (session['user_id'], current_balance, current_balance))
            
            user = cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

            if user['first_login'] == 1:
                try:
                    cursor.execute('UPDATE users SET first_login = 0 WHERE id = ?', (user['id'],))
                    conn.commit()
                except:
                    print("DB could not update first_login")

            conn.commit()
        except sqlite3.Error as e:
            print(f"Error updating data: {e}")
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('home')) # Redirect to home page

    return redirect(url_for('login'))  # If user is not logged in

@app.route('/logout')
def logout():
    # Clear the session data (logs out the user)
    session.clear()

    # Redirect the user to the login page
    return redirect(url_for('index'))


@app.route("/")
def home():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row  # Enable column name access
    cursor = conn.cursor()

    report = None  # Default value
    try:
        report = cursor.execute('SELECT * FROM reports WHERE user_id = ?', (user_id,)).fetchone()
        user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        saving = cursor.execute('SELECT * FROM saving_goal WHERE user_id = ?', (user_id,)).fetchone()
    except Exception as e:
        print("Fetching error for home page:", e)
    finally:
        cursor.close()
        conn.close()
    if user:
        current_balance = user['current_balance']
        
        if report:
            total_income = report['total_income']
            total_expense = report['total_expense']    
        else:
            total_income = 0
            total_expense = 0
        print("if block", current_balance)
        if saving:
            goal_amount,t_months,remaining_months,remaining_years,end_date,total_saved,remaining_amount=saving_data()
        else:
            goal_amount=0
            t_months = 0
            end_date = 0
            remaining_months = 0
            remaining_years = 0
            remaining_amount=0
            total_saved=0
    else:
        current_balance = 0
        total_income = 0
        total_expense = 0
        goal_amount=0
        t_months = 0
        end_date = 0
        remaining_months = 0
        remaining_years = 0
        remaining_amount = 0
        total_saved = 0

    
    return render_template('home.html', active_page='home',balance=current_balance, income=total_income, expense=total_expense,t_months=t_months,remaining_months=remaining_months,remaining_years=remaining_years,goal_amount=goal_amount,end_date=end_date,total_saved=total_saved,remaining_amount=remaining_amount)


    


@app.route("/expenses",methods=['GET','POST'])
def expenses():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch recent 5 transactions
    cursor.execute('''
        SELECT t.type, t.amount, c.name AS category_name, t.description 
        FROM transactions t 
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = ? 
        ORDER BY t.id DESC 
        LIMIT 5
    ''', (session['user_id'],))
    recent_transactions = cursor.fetchall()

    # Count total transactions
    cursor.execute('SELECT COUNT(*) FROM transactions WHERE user_id = ?', (session['user_id'],))
    total_transactions = cursor.fetchone()[0]


    cursor.close()
    conn.close()

    return render_template('expenses.html', recent_transactions=recent_transactions, total_transactions=total_transactions)

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    user_id = session['user_id']
    data = fetch_data(f"""
        SELECT categories.name, SUM(transactions.amount) 
        FROM transactions 
        JOIN categories ON transactions.category_id = categories.id
        WHERE transactions.type = 'Expense' AND transactions.user_id = {user_id}
        GROUP BY transactions.category_id
    """)
    
    if data:
        expense_dict = {category: amount for category, amount in data}
        summary = generate_budget_summary(expense_dict)
    else:
        summary = None

    return render_template('reports.html',time=time.time,summary=summary)

def generate_budget_summary(expense_dict):
    """Generates a financial summary and budget suggestions"""
    
    total_expense = sum(expense_dict.values())
    highest_category = max(expense_dict, key=expense_dict.get)
    lowest_category = min(expense_dict, key=expense_dict.get)

    summary = f"📊 **Expense Summary**\n"
    summary += f"- Total Monthly Expense: ₹{total_expense:.2f}\n"
    summary += f"- Highest Spending: {highest_category.capitalize()} (₹{expense_dict[highest_category]:.2f})\n"
    summary += f"- Lowest Spending: {lowest_category.capitalize()} (₹{expense_dict[lowest_category]:.2f})\n"

    # Budget Suggestions
    suggestions = "\n💡 **Budget Planning Suggestions**\n"

    if expense_dict.get("miscellaneous", 0) > 10000:
        suggestions += "- Consider reducing **miscellaneous expenses** to save more.\n"

    if expense_dict.get("food", 0) > 8000:
        suggestions += "- Try meal planning and home cooking to cut down on food expenses.\n"

    if expense_dict.get("transport", 0) < 500:
        suggestions += "- Your transport expenses are quite low. Consider if public transport can help you save even more.\n"

    if expense_dict.get("education", 0) > 10000:
        suggestions += "- Education costs are high. Look for scholarships or online learning alternatives.\n"

    if expense_dict.get("personal care", 0) > 3000:
        suggestions += "- Consider reducing spending on luxury personal care items.\n"

    if expense_dict.get("health", 0) < 2000:
        suggestions += "- Ensure you allocate enough budget for health and medical emergencies.\n"

    return summary + suggestions

def fetch_data(query):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data



@app.route('/generate_report/<chart>')
def generate_report(chart):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    if chart == 'bar':
        data = fetch_data(f"""
            SELECT strftime('%Y-%m', created_at) AS month, 
                   SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) AS income,
                   SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) AS expense
            FROM transactions WHERE user_id = {user_id}
            GROUP BY month 
            ORDER BY month
        """)

        df = pd.DataFrame(data, columns=['Month', 'Income', 'Expense'])
        df.fillna(0, inplace=True)
        df['Income'] = pd.to_numeric(df['Income'], errors='coerce').fillna(0)
        df['Expense'] = pd.to_numeric(df['Expense'], errors='coerce').fillna(0)
        df['Month'] = df['Month'].astype(str)

        plt.figure(figsize=(12, 6))
        plt.bar(df['Month'], df['Income'], label='Income', color='g')
        plt.bar(df['Month'], df['Expense'], label='Expense', color='r', alpha=0.7, bottom=df['Income'])
        plt.xlabel('Month')
        plt.ylabel('Amount')
        plt.title('Income vs Expense Per Month',fontsize=16, fontweight='bold', color='darkblue')
        plt.xticks(rotation=45)
        plt.legend()

        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plt.close()

        return send_file(img, mimetype='image/png')


    elif chart == 'pie': # Generate pie chart when requested
        data = fetch_data(f"""
            SELECT categories.name, SUM(transactions.amount) 
            FROM transactions 
            JOIN categories ON transactions.category_id = categories.id
            WHERE transactions.type = 'Expense' AND transactions.user_id = {user_id}
            GROUP BY transactions.category_id
        """)
        df = pd.DataFrame(data, columns=['Category', 'Total Expense'])

        plt.figure(figsize=(6,6))
        colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99','#c2c2f0']
        plt.pie(df['Total Expense'], labels=df['Category'], colors=colors, autopct='%1.1f%%', startangle=140)
        plt.title('Expense Distribution',fontsize=16, fontweight='bold', color='darkblue')

        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plt.close()
        
        return send_file(img, mimetype='image/png')
    
    elif chart == 'incomevsexpense':
        data = fetch_data(f"""
            SELECT strftime('%Y-%m', created_at) AS month, 
                SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) AS income,
                SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) AS expense
            FROM transactions WHERE user_id = {user_id}
            GROUP BY month 
            ORDER BY month
        """)

        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['Month', 'Income', 'Expense'])

        # Plot bar chart
        plt.figure(figsize=(8, 5))
        bar_width = 0.4  # Adjust bar width for better spacing
        x_indexes = range(len(df['Month']))

        plt.bar(x_indexes, df['Income'], width=bar_width, label='Income', color='#4CAF50')  # Green for Income
        plt.bar([x + bar_width for x in x_indexes], df['Expense'], width=bar_width, label='Expense', color='#F44336', alpha=0.7)  # Red for Expense

        plt.xlabel('Month', fontsize=12, fontweight='bold')
        plt.ylabel('Amount', fontsize=12, fontweight='bold')
        plt.title('Income vs Expense Over Time', fontsize=16, fontweight='bold', color='darkblue')

        plt.xticks([x + bar_width / 2 for x in x_indexes], df['Month'], rotation=45)  # Adjust x-axis labels
        plt.legend()

        # Save and return image
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plt.close()

        return send_file(img, mimetype='image/png')

    elif chart == 'line':
        data = fetch_data(f"""
            SELECT strftime('%Y-%m-%d', created_at) AS date, 
                SUM(CASE WHEN type = 'Income' THEN amount ELSE 0 END) AS income,
                SUM(CASE WHEN type = 'Expense' THEN amount ELSE 0 END) AS expense
            FROM transactions  
            WHERE date IS NOT NULL AND user_id = {user_id}
            GROUP BY date
            ORDER BY date
        """)

        # Convert to DataFrame
        df = pd.DataFrame(data, columns=['Date', 'Income', 'Expense'])

        # Ensure no None values in Date
        df = df.dropna(subset=['Date'])

        # Convert Date to string (if necessary)
        df['Date'] = df['Date'].astype(str)

        # Plot Line Chart
        plt.figure(figsize=(8, 5))
        plt.plot(df['Date'], df['Income'], label='Income', marker='o', color='g', linestyle='-')
        plt.plot(df['Date'], df['Expense'], label='Expense', marker='o', color='r', linestyle='-')

        plt.xlabel('Date', fontsize=12, fontweight='bold')
        plt.ylabel('Amount', fontsize=12, fontweight='bold')
        plt.title('Income vs Expense Over Time', fontsize=14, fontweight='bold', color='darkblue')
        plt.xticks(rotation=45)  # Rotate dates for readability
        plt.legend()
        plt.grid(True)

        # Save image to BytesIO
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plt.close()

        return send_file(img, mimetype='image/png')

    elif chart == 'histogram':
        data = fetch_data(f"""
            SELECT amount FROM transactions WHERE type = 'Expense' AND user_id = {user_id}
        """)

        df = pd.DataFrame(data, columns=['Amount'])
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')


        df = df.dropna()
        plt.figure(figsize=(8, 5))
        plt.hist(df['Amount'], bins=10, color='blue', edgecolor='black', alpha=0.7)

        plt.xlabel('Expense Amount', fontsize=12, fontweight='bold')
        plt.ylabel('Frequency', fontsize=12, fontweight='bold')
        plt.title('Distribution of Expenses', fontsize=14, fontweight='bold', color='darkblue')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plt.close()

        return send_file(img, mimetype='image/png')
    
    elif chart == 'tree':
        data = fetch_data(f"""
            SELECT categories.name, SUM(transactions.amount) 
            FROM transactions 
            JOIN categories ON transactions.category_id = categories.id
            WHERE transactions.type = 'Expense' AND transactions.user_id = {user_id}
            GROUP BY transactions.category_id
        """)

        df = pd.DataFrame(data, columns=['Category', 'Total Expense'])

        # Plot bar chart
        plt.figure(figsize=(8, 5))
        plt.bar(df['Category'], df['Total Expense'], color='skyblue')
        plt.xlabel('Categories', fontsize=12)
        plt.ylabel('Total Expense', fontsize=12)
        plt.title('Expense Distribution by Category', fontsize=14)
        plt.xticks(rotation=45)

        # Save image and return
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plt.close()

        return send_file(img, mimetype='image/png')
    


@app.route("/accounts")
def accounts():
    username = session.get('username')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        user = cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    except sqlite3.Error as e:
        print("Acc Error -> ",e)
    finally:
        cursor.close()
        conn.close()

    if user:
        full_name = user['full_name']
        ph_num = user['ph_num']
        dob = user['DOB']
        email = user['email']
        if user['profile_pic'] != 'None':
            profile_pic = user['profile_pic']
        else:
            profile_pic = "https://res.cloudinary.com/dwijp5leb/image/upload/w_1000,c_fill,ar_1:1,g_auto,r_max,bo_5px_solid_red,b_rgb:262c35/v1738924958/Login_n0dsaq.png"

    print(profile_pic)
    return render_template("accounts.html",active_page='accounts',username=username,full_name=full_name,ph_num=ph_num,dob=dob,email=email,profile_pic=profile_pic)



@app.route("/upload", methods=['GET', 'POST'])
def upload():
    print("Upload Button Clicked")
    if 'user_id' not in session:
        return render_template('index.html')  # Redirect to login if session is missing

    file = request.files.get('file')

    if not file or file.filename == '':
        return "No file selected. Please select an image to upload.", 400  # Error message

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT profile_pic FROM users WHERE id = ?", (session['user_id'],))
        existing_image = cursor.fetchone()
        if existing_image and existing_image[0] and existing_image[0] != "None":
                public_id = extract_public_id(existing_image[0])
                if public_id:
                    cloudinary.uploader.destroy(public_id)

        # Upload file to Cloudinary
        upload_result = cloudinary.uploader.upload(file)
        image_url = upload_result.get('secure_url')
        print(image_url)
        if not image_url:
            return "Image upload failed!", 500

        # Save image URL to database
        
        cursor.execute("UPDATE users SET profile_pic = ? WHERE id = ?", (image_url, session['user_id']))
        conn.commit()

    except sqlite3.Error as e:
        print("Database Error: ", e)
        return "Database Error", 500

    except Exception as e:
        print("Unexpected Error: ", e)
        return "Something went wrong!", 500

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("accounts"))

def extract_public_id(image_url):
    match = re.search(r'/v\d+/(.*)\.\w+$', image_url)
    return match.group(1) if match else None

@app.route("/update",methods=['GET','POST'])
def update():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    button = request.args.get('btn')

    conn = get_db_connection()
    cursor = conn.cursor()
    if button == 'name':
        new_name = request.form.get('new_name')
        try:
            cursor.execute('UPDATE users SET full_name = ? WHERE id = ?',(new_name,session['user_id']))
            conn.commit()
        except sqlite3.Error as e:
            print("DB Error:",e)
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('accounts'))
    elif button == 'dob':
        new_dob = request.form.get('new_dob')
        try:
            cursor.execute('UPDATE users SET DOB = ? WHERE id = ?',(new_dob,session['user_id']))
            conn.commit()
        except sqlite3.Error as e:
            print("DB Error:",e)
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('accounts'))
    elif button == 'email':
        new_email = request.form.get('new_email')
        try:
            cursor.execute('UPDATE users SET email = ? WHERE id = ?',(new_email,session['user_id']))
            conn.commit()
        except sqlite3.Error as e:
            print("DB Error:",e)
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('accounts'))
    elif button == 'contact':
        new_contact = request.form.get('new_contact')
        try:
            cursor.execute('UPDATE users SET ph_num = ? WHERE id = ?',(new_contact,session['user_id']))
            conn.commit()
        except sqlite3.Error as e:
            print("DB Error:",e)
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('accounts'))
    elif button == 'balance':
        new_balance = request.form.get('new_balance')
        try:
            cursor.execute('UPDATE users SET current_balance = ? WHERE id = ?',(new_balance,session['user_id']))
            conn.commit()
        except sqlite3.Error as e:
            print("DB Error:",e)
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('accounts'))
    elif button == 'password':
        new_password = request.form.get('new_password')
        try:
            cursor.execute('UPDATE users SET password = ? WHERE id = ?',(new_password,session['user_id']))
            conn.commit()
        except sqlite3.Error as e:
            print("DB Error:",e)
        finally:
            cursor.close()
            conn.close()
        return redirect(url_for('accounts'))
    return redirect(url_for('accounts'))


        
@app.route("/savings_planner", methods=["GET", "POST"])
def savings_planner():
    result = None
    color=None
    goal = None

    if request.method == "POST":
        try:
            income = float(request.form.get("income"))
            duration_type = request.form.get("duration_type")
            duration = int(request.form.get("duration"))
            savings_goal = float(request.form.get("savings_goal"))
            
            # Calculate maximum spending limit per month/year
            if duration_type == "months":
                max_spent = (income*duration - savings_goal) / duration
                duration_label = "per month"
            else:
                total_months = duration * 12
                max_spent = (income*total_months - savings_goal)/duration
                max_spent_month = (income*total_months - savings_goal)/ total_months
                duration_label = "per year"
            if request.form.get('action')=='cal':
                if max_spent > 0:
                    if duration_type =="months":
                        result = f"To reach your goal, you should not spend more than ₹{max_spent:.2f} {duration_label}"
                    else:
                        result = f"To reach your goal, you should not spend more than ₹{max_spent:.2f} {duration_label} and {max_spent_month:.2f} per month."
                    color = "green"
                else:
                    result = f"Oops! Your savings goal is higher than your total earnings. Try adjusting your goal or duration."
                    color = "red"

        except ValueError:
            result = "Please enter valid numbers."
            color = "red"
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    report = None  # Default value
    try:
        saving = cursor.execute('SELECT * FROM saving_goal WHERE user_id = ?', (user_id,)).fetchone()
        report = cursor.execute('SELECT * FROM reports WHERE user_id = ?', (user_id,)).fetchone()
        user = cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if request.form.get('action') == 'set':
            cursor.execute('''INSERT INTO saving_goal (user_id,income,duration,duration_type,saving_goal) 
                  VALUES (?,?,?,?,?)
                  ON CONFLICT(user_id) DO UPDATE SET income = ?,duration = ?,duration_type = ?,saving_goal = ?''', 
                 (user_id, income, duration,duration_type,savings_goal,income, duration,duration_type,savings_goal))
            conn.commit()
            goal = f"Saving Rs {savings_goal} in {duration} {duration_type} Activated !"
    except Exception as e:
        print("Fetching error for home page:", e)
    finally:
        cursor.close()
        conn.close()
    if user:
        current_balance = user['current_balance']
        if saving:
            goal_amount,t_months,remaining_months,remaining_years,end_date,total_saved,remaining_amount=saving_data()
        else:
            goal_amount = 0
            t_months = 0
            remaining_months = 0
            remaining_years = 0
            end_date = 0
            total_saved = 0
            remaining_amount = 0

        if report:
            total_income = report['total_income']
            total_expense = report['total_expense']    
        else:
            total_income = 0
            total_expense = 0
        print("if block", current_balance)
    else:
        current_balance = 0
        total_income = 0
        total_expense = 0
        goal_amount = 0
        t_months = 0
        remaining_months = 0
        remaining_years = 0
        end_date = 0
        total_saved = 0
        remaining_amount = 0
    
    return render_template('home.html', active_page='home', balance=current_balance, income=total_income, expense=total_expense,result=result,color=color,goal=goal,t_months=t_months,remaining_months=remaining_months,remaining_years=remaining_years,goal_amount=goal_amount,end_date=end_date,total_saved=total_saved,remaining_amount=remaining_amount)
    

def saving_data():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        saving = cursor.execute('SELECT * FROM saving_goal WHERE user_id = ?', (session['user_id'],)).fetchone()
        total_saved = cursor.execute('SELECT SUM(amount) FROM transactions WHERE user_id = ? AND type = "deposit"', (session['user_id'],)).fetchone()[0]
        if total_saved is None:
            total_saved = 0
    except sqlite3.Error as e:
        print("Fetching Users Saving goal failed :",e)
    finally:
        cursor.close()
        conn.close()
    goal_amount = saving['saving_goal']
    total_duration = saving['duration']
    d_type = saving['duration_type']
    start_date = saving['start_date']
    start_date = datetime.strptime(start_date[:10], "%Y-%m-%d")
    if d_type == 'months':
        t_months = total_duration
    else:
        t_months = total_duration * 12
    end_date = start_date + timedelta(days=t_months * 30)
    today = datetime.today()
    remaining_months = (end_date.year - today.year) * 12 + (end_date.month - today.month)
    remaining_years = remaining_months // 12
    remaining_months %= 12
    remaining_amount = goal_amount - total_saved
    return goal_amount,t_months,remaining_months,remaining_years,end_date,total_saved,remaining_amount


@app.route('/remove_saving')
def remove_saving():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE From saving_goal WHERE user_id = ? ',(session['user_id'],))
        conn.commit()
    except sqlite3.Error as e:
        print("Deletion of Savings failed : ",e)
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('home'))


@app.route('/add_expense_voice',methods=['GET','POST'])
def add_expense_voice():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for expense details...")
        flash("Listining...")
        
        try:
            audio = recognizer.listen(source, timeout=8)
        except Exception as e:
            print("TimeOut")
            return redirect(url_for('expenses'))
    
    try:
        text = recognizer.recognize_google(audio)  # Convert speech to text
        print("Recognized:", text)

        # Extract details
        amount, transaction_type, description, category = extract_expense_details(text)

        # Handle missing values
        if amount is None:
            amount = 0
        if transaction_type is None:
            transaction_type = "Unknown"
        if not description:
            description = "No description"

        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Get category ID
            category_id = cursor.execute('SELECT id FROM categories WHERE name = ?', (category,)).fetchone()
            category_id = category_id['id'] if category_id else 1

            cursor.execute('INSERT INTO transactions (user_id, type, amount, category_id, description) VALUES (?, ?, ?, ?, ?)', 
                           (session['user_id'], transaction_type, amount, category_id, description))
            
            net_balance = cursor.execute('SELECT current_balance FROM users WHERE id = ?',(session['user_id'],)).fetchone()[0]
            report = cursor.execute('SELECT * FROM reports WHERE user_id = ?', (session['user_id'],)).fetchone()

            total_income=0
            total_expense=0
            if report:
                total_income = report['total_income']
                total_expense = report['total_expense']
            if transaction_type == 'Expense':
                total_expense = total_expense + amount    
                if amount > net_balance:
                    net_balance = 0
                net_balance = net_balance - amount 
            elif transaction_type == 'Income':
                total_income = total_income + amount
                net_balance = net_balance + amount
            
            elif transaction_type == 'Unknown':
                net_balance = net_balance

            try:
                cursor.execute('UPDATE users SET current_balance = ? WHERE id = ?',(net_balance,session['user_id']))
                cursor.execute('UPDATE reports SET total_income = ?,total_expense = ? WHERE user_id = ?',(total_income,total_expense,session['user_id']))
            except sqlite3.Error as e:
                print('Failed updating amounts',e)
            
            conn.commit()
            return jsonify({"success": True, "recognized_text": text})
        except sqlite3.Error as e:
            print("Voice Expense Log failed:", e)
            return jsonify({"success": False, "error": "Voice not clear !"})
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        print("Error:", e)
        return jsonify({"success": False, "error": "Could not recognize speech."})

def extract_expense_details(text):
    CATEGORIES = {
        "food": ["food", "dining", "restaurant", "groceries", "snacks", "lunch", "dinner", "breakfast"],
        "transport": ["taxi", "bus", "train", "metro", "cab", "fuel", "petrol", "diesel", "rickshaw"],
        "bills": ["electricity", "water bill", "internet", "wifi", "phone bill", "gas bill"],
        "shopping": ["shopping", "clothes", "electronics", "gadgets", "furniture", "accessories"],
        "entertainment": ["movies", "netflix", "spotify", "gaming", "concert", "subscription"],
        "health": ["doctor", "medicine", "hospital", "pharmacy", "insurance"],
        "education": ["tuition", "books", "course", "college fees", "school fees"],
        "personal care": ["salon", "beauty", "skincare", "gym", "spa"],
        "travel": ["flight", "hotel", "vacation", "trip", "tour"],
        "home": ["rent", "house maintenance", "repairs"],
        "gifts": ["gift", "donation", "charity"],
        "investment": ["stocks", "mutual fund", "fixed deposit", "investment"],
        "miscellaneous": ["other", "miscellaneous", "random"]
    }
    if not text:
        return None, None, None, None

    text = text.lower()
    words = text.split()
    amount = None
    transaction_type = None
    description = []
    category = "miscellaneous"

    # Identify amount (first number in speech)
    for word in words:
        if word.isdigit():
            amount = int(word)
            break

    # Identify type (income or expense)
    if "income" in words or "got" in words or "received" in words or "credited" in words or "earned" in words or "someone sent me" in words or "made" in words or "payment received" in words or "added" in words or "bonus" in words or "salary" in words :
        transaction_type = "Income"
    elif "expense" in words or "paid" in words or "spent" in words or "bought" in words or "purchased" in words or "gave" in words or "charged" in words or "transferred" in words or "donated" in words :
        transaction_type = "Expense"

    # Identify category
    for cat, keywords in CATEGORIES.items():
        if any(keyword in words for keyword in keywords):
            category = cat
            break

    # Filter out unnecessary words for description
    description_words = [w for w in words if w not in [str(amount), "income", "expense", category, "paid", "rupees", "rs","of","as","a"]]
    description = " ".join(description_words)

    print(f"amount: {amount}\ntransaction_type: {transaction_type}\ncategory: {category}\ndescription: {description}")
    return float(amount), transaction_type, description, category


@app.route('/all_transactions',methods=['GET','POST'])
def all_transactions():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch recent 5 transactions
    cursor.execute('''
        SELECT t.type, t.amount, c.name AS category_name, t.description 
        FROM transactions t 
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.user_id = ?
    ''', (session['user_id'],))
    recent_transactions = cursor.fetchall()


    cursor.close()
    conn.close()
    btn = 'see_less'
    return render_template('expenses.html', recent_transactions=recent_transactions,btn=btn)
 

if __name__ == "__main__":
    app.run(debug=True)
