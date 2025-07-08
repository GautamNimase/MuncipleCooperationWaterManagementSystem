import mysql.connector
from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# Connect to MySQL Database
def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Gautam@012',
        database='watersystem'
    )
    return conn

@app.route('/')
def index():
    return render_template('index.html')





# Route for Customer
@app.route('/customer')
def customer():
    return render_template('customer.html')

@app.route('/add_customer', methods=['POST'])
def add_customer():
    conn = get_db_connection()
    cursor = conn.cursor()
    name = request.form['name']
    address = request.form['address']
    phone = request.form['phone']
    email = request.form['email']
    connection_type = request.form['connectionType']
    
    try:
        cursor.execute("INSERT INTO Customer (Name, Address, Phone, Email, ConnectionType) VALUES (%s, %s, %s, %s, %s)",
                        (name, address, phone, email, connection_type))
        flash("Customer Details submitted successfully", "success")
        conn.commit()

    except mysql.connector.Error as err:
        # Check for specific error messages from each trigger
        error_message = str(err)
        if "Invalid email format" in error_message:
            flash('Invalid email format. Please enter a valid email address.', 'error')
        elif "Invalid phone number format" in error_message:
            flash('Invalid phone number format. Phone number should be 10 digits.', 'error')
        else:
            flash('An error occurred. Please try again.', 'error')
        conn.rollback()  # Rollback in case of error
        return redirect(url_for('customer'))
    finally:
        conn.close()

    return redirect('/customer')

# Route to view customer list
@app.route('/view_customers')
def view_customers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Customer")
    customers = cursor.fetchall()
    conn.close()
    return render_template('view_customers.html', customers=customers)

# Route to delete a customer
@app.route('/delete_customer/<int:customer_id>')
def delete_customer(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Customer WHERE CustomerID = %s", (customer_id,))
    conn.commit()
    conn.close()
    flash("Customer deleted successfully", "success")
    return redirect(url_for('view_customers'))

# Route to update a customer
@app.route('/update_customer/<int:customer_id>', methods=['GET', 'POST'])
def update_customer(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Retrieve updated data from the form
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        email = request.form['email']
        connection_type = request.form['connection_type']
        
        # Update the customer data in the database
        cursor.execute("""
            UPDATE Customer 
            SET Name = %s, Address = %s, Phone = %s, Email = %s, ConnectionType = %s 
            WHERE CustomerID = %s
        """, (name, address, phone, email, connection_type, customer_id))
        
        conn.commit()
        flash("Customer updated successfully", "success")
        return redirect(url_for('view_customers'))
    
    # Fetch the existing data for the selected customer
    cursor.execute("SELECT * FROM Customer WHERE CustomerID = %s", (customer_id,))
    customer = cursor.fetchone()
    conn.close()
    return render_template('update_customer.html', customer=customer)

# Route to view customer backup
@app.route('/customer_backup')
def customer_backup():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM CustomerBackup")
    customers_backup = cursor.fetchall()
    conn.close()
    return render_template('customer_backup.html', customers_backup=customers_backup)

# Route to fetch customer details using the function
@app.route('/get_customer_details', methods=['POST'])
def get_customer_details():
    customer_id = request.form['customer_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Call the MySQL function
        cursor.execute("SELECT GetCustomerDetails(%s)", (customer_id,))
        result = cursor.fetchone()
        customer_details = result[0] if result else "Customer not found"
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('view_customers'))
    finally:
        conn.close()

    # Pass the fetched details to the frontend
    return render_template('view_customers.html', customers=get_all_customers(), customer_details=customer_details)

def get_all_customers():
    """Helper function to fetch all customers"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Customer")
    customers = cursor.fetchall()
    conn.close()
    return customers




# Repeat similar blocks for Billing, Meter Reading, Water Connection, Employee, Water Source
@app.route('/billing')
def billing():
    return render_template('billing.html')

import datetime  # Add this import

import mysql.connector
# Route for Adding Billing Entry
from flask import Flask, flash, redirect, render_template, request


# Route for Adding Billing Entry
@app.route('/add_billing', methods=['POST'])
def add_billing():
    conn = get_db_connection()
    cursor = conn.cursor()

    bill_date = request.form['billDate']
    amount = request.form['amount']
    payment_status = request.form['paymentStatus']
    customer_id = request.form['customerID']
    connection_id = request.form['connectionID']

    try:
        # Insert billing record; trigger will be invoked here
        cursor.execute(
            "INSERT INTO Billing (BillDate, Amount, PaymentStatus, CustomerID, ConnectionID) VALUES (%s, %s, %s, %s, %s)",
            (bill_date, amount, payment_status, customer_id, connection_id)
        )

        # Check if the bill date is older than two months and set a warning message
        cursor.execute("SELECT Amount, BillDate FROM Billing ORDER BY BillID DESC LIMIT 1")
        updated_amount, latest_bill_date = cursor.fetchone()

        # Display a message if a late fee was applied
        if float(updated_amount) > float(amount):
            flash("A 5% late fee has been applied to your bill due to overdue status.", "warning")

        # Display a warning if the bill date is older than two months
        if latest_bill_date < (datetime.date.today() - datetime.timedelta(days=60)):
            flash("Warning: If the bill is not paid, your water connection may be cut off.", "warning")

        flash("Billing Details submitted successfully", "success")
        conn.commit()

        return redirect('/billing')  # Redirect to billing page

    except mysql.connector.Error as err:
        # Catch SQL errors triggered by the trigger and display them on the front end
        if err.errno == 1644:  # Custom error for bills over three months old
            flash(str(err), 'error')  # Flash error message from the trigger
        else:
            flash('An error occurred while adding the billing entry.', 'error')

        conn.rollback()  # Rollback in case of error
        return redirect('/billing')  # Stay on the same page if error occurs

    finally:
        conn.close()  # Close connection after commit/rollback



@app.route('/billing_records')
def billing_records():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Billing")
    billing_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('billing_records.html', billing_data=billing_data)


@app.route('/update_billing/<int:bill_id>', methods=['GET', 'POST'])
def update_billing(bill_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        bill_date = request.form['billDate']
        amount = request.form['amount']
        payment_status = request.form['paymentStatus']
        customer_id = request.form['customerID']
        connection_id = request.form['connectionID']

        try:
            cursor.execute("""
                UPDATE Billing 
                SET BillDate = %s, Amount = %s, PaymentStatus = %s, CustomerID = %s, ConnectionID = %s 
                WHERE BillID = %s
            """, (bill_date, amount, payment_status, customer_id, connection_id, bill_id))
            conn.commit()
            flash("Billing record updated successfully.", "success")
        except mysql.connector.Error as err:
            flash("Error occurred while updating the billing record.", "error")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

        return redirect('/billing_records')

    # If GET request, fetch the existing billing record
    cursor.execute("SELECT * FROM Billing WHERE BillID = %s", (bill_id,))
    billing = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('update_billing.html', billing=billing)


@app.route('/delete_billing/<int:bill_id>', methods=['POST'])
def delete_billing(bill_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM Billing WHERE BillID = %s", (bill_id,))
        conn.commit()
        flash("Billing record deleted successfully.", "success")
    except mysql.connector.Error as err:
        flash("Error occurred while deleting the billing record.", "error")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return redirect('/billing_records')


@app.route('/billing_backup')
def billing_backup():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM BillingBackup")  # Adjust this query based on your backup table structure
    billing_backup_data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('billing_backup.html', billing_backup_data=billing_backup_data)

@app.route('/calculate_bill', methods=['GET', 'POST'])
def calculate_bill():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch input values
        customer_id = request.form['customerID']
        start_date = request.form['startDate']
        end_date = request.form['endDate']
        
        try:
            # Query to calculate total bill
            query = """
            SELECT COALESCE(SUM(Amount), 0)
            FROM Billing
            WHERE CustomerID = %s AND BillDate BETWEEN %s AND %s AND PaymentStatus = 'Paid'
            """
            cursor.execute(query, (customer_id, start_date, end_date))
            total_amount = cursor.fetchone()[0]
            
            # Flash success message
            flash(f'Total billed amount for Customer ID {customer_id} between {start_date} and {end_date} is {total_amount:.2f}', 'success')
        except mysql.connector.Error as err:
            flash('Error occurred while calculating the total billed amount.', 'error')
        finally:
            cursor.close()
            conn.close()
        
        # Redirect to the billing records page
        return redirect('/billing_records')

    # Render the calculate bill page
    return render_template('calculate_bill.html')







@app.route('/meter_reading')
def meter_reading():
    return render_template('meter_reading.html')

@app.route('/add_meter_reading', methods=['POST'])
def add_meter_reading():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    reading_date = request.form['readingDate']
    units_consumed = request.form['unitsConsumed']
    connection_id = request.form['connectionID']
    
    try:
        # Insert meter reading
        cursor.execute("INSERT INTO MeterReading (ReadingDate, UnitsConsumed, ConnectionID) VALUES (%s, %s, %s)", 
                        (reading_date, units_consumed, connection_id))
        conn.commit()
        
        if 1000 < int(units_consumed) <= 1500:
            message = 'Warning: You have consumed more than 1000 units of water.'
        elif 1500 < int(units_consumed) <= 2000:
            message = 'Warning: You have consumed more than 1500 units. If your consumption exceeds 2000 units, the water supply will be stopped.'
        else:
            message = 'Meter reading submitted successfully.'
        
        flash(message)  # Flash message for successful submission
        flash(" Meter reading submitted successfully", "success")
        conn.close()
        return redirect(url_for('meter_reading'))
    
    except mysql.connector.Error as err:
        if err.errno == 1644:
            message = 'Water supply stopped: Your consumption has exceeded 2000 units.'
        else:
            message = 'Error: ' + str(err)
        
        conn.rollback()
        flash(message)
        conn.close()
        return redirect(url_for('meter_reading'))


# Route for displaying the meter reading list
@app.route('/meter_readings')
def meter_readings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM MeterReading")
    readings = cursor.fetchall()
    conn.close()
    return render_template('meter_readings_list.html', readings=readings)






# Route for the Water Connection form page
@app.route('/water_connection')
def water_connection():
    return render_template('water_connection.html')

# Route to add a new water connection (POST)
@app.route('/add_water_connection', methods=['POST'])
def add_water_connection():
    conn = get_db_connection()  # Get the database connection
    cursor = conn.cursor()
    customer_id = request.form['customerID']
    connection_date = request.form['connectionDate']
    meter_number = request.form['meterNumber']
    status = request.form['status']

    try:
        # Insert data into the WaterConnection table
        cursor.execute(
            "INSERT INTO WaterConnection (CustomerID, ConnectionDate, MeterNumber, Status) VALUES (%s, %s, %s, %s)",
            (customer_id, connection_date, meter_number, status)
        )
        conn.commit()  # Commit the transaction
        flash('Water connection added successfully!', 'success')  # Flash success message

    except mysql.connector.Error as err:
        # Catch any errors during the insert operation
        flash(f'Error: {str(err)}', 'error')  # Flash error message
        conn.rollback()  # Rollback transaction on error

    finally:
        conn.close()  # Close the database connection

    return redirect(url_for('water_connection'))  # Redirect back to the form page


@app.route('/water_connection_list')
def water_connection_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM WaterConnection")
    water_connections = cursor.fetchall()
    conn.close()
    return render_template('water_connection_list.html', water_connections=water_connections)

@app.route('/delete_connection/<int:connection_id>')
def delete_connection(connection_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM WaterConnection WHERE ConnectionID = %s", (connection_id,))
        conn.commit()
        flash('Water connection deleted successfully', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {str(err)}", 'error')
        conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('water_connection_list'))

@app.route('/update_connection/<int:connection_id>', methods=['GET', 'POST'])
def update_connection(connection_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        connection_date = request.form['connectionDate']
        meter_number = request.form['meterNumber']
        status = request.form['status']
        try:
            cursor.execute("""
                UPDATE WaterConnection 
                SET ConnectionDate = %s, MeterNumber = %s, Status = %s 
                WHERE ConnectionID = %s
            """, (connection_date, meter_number, status, connection_id))
            conn.commit()
            flash('Water connection updated successfully', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {str(err)}", 'error')
            conn.rollback()
        finally:
            conn.close()
        return redirect(url_for('water_connection_list'))

    cursor.execute("SELECT * FROM WaterConnection WHERE ConnectionID = %s", (connection_id,))
    connection = cursor.fetchone()
    conn.close()
    return render_template('update_connection.html', connection=connection)


# Sample route to render deleted connections
@app.route('/deleted_connections')
def deleted_connections():
    # Fetch deleted connections data from the database
    deleted_connections = [
        # Example data
        (101, 202, "2024-10-10", "12345678", "Inactive"),
        (102, 203, "2024-09-12", "87654321", "Inactive")
    ]
    return render_template('deleted_connection.html', deleted_connections=deleted_connections)

# Route to get the active connections count for a specific customer
@app.route('/active_connections_count/<int:customer_id>')
def active_connections_count(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # SQL query to count active connections for a specific customer
    cursor.execute("""
        SELECT COUNT(*)
        FROM WaterConnection
        WHERE CustomerID = %s AND Status = 'Active'
    """, (customer_id,))
    
    active_count = cursor.fetchone()[0]
    conn.close()
    
    return str(active_count)





@app.route('/employee')
def employee():
    return render_template('employee.html')

@app.route('/add_employee', methods=['POST'])
def add_employee():
    conn = get_db_connection()
    cursor = conn.cursor()
    name = request.form['name']
    role = request.form['role']
    phone = request.form['phone']
    assigned_area = request.form['assignedArea']
    
    cursor.execute("INSERT INTO Employee (Name, Role, Phone, AssignedArea) VALUES (%s, %s, %s, %s)",
                    (name, role, phone, assigned_area))
    conn.commit()
    conn.close()

    flash('Employee details submitted successfully!', 'success')  # Flash success message
    return redirect('/employee')  # Redirect back to the employee page


@app.route('/employee_list')
def employee_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # Enable named access to columns
    cursor.execute("SELECT * FROM Employee")
    employees = cursor.fetchall()
    conn.close()
    return render_template('employee_list.html', employees=employees)


# Delete employee route
@app.route('/delete_employee/<int:employee_id>', methods=['POST'])
def delete_employee(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Employee WHERE EmployeeID = %s", (employee_id,))
        conn.commit()
        flash('Employee deleted successfully and backup created!', 'success')
    except mysql.connector.Error as err:
        flash(f"Error: {str(err)}", 'error')
        conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('employee_list'))


# Update employee route
@app.route('/update_employee/<int:employee_id>', methods=['GET', 'POST'])
def update_employee(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        role = request.form['role']
        phone = request.form['phone']
        assigned_area = request.form['assignedArea']

        try:
            cursor.execute("""
                UPDATE Employee 
                SET Name = %s, Role = %s, Phone = %s, AssignedArea = %s 
                WHERE EmployeeID = %s
            """, (name, role, phone, assigned_area, employee_id))
            conn.commit()
            flash('Employee updated successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {str(err)}", 'error')
            conn.rollback()
        finally:
            conn.close()
        return redirect(url_for('employee_list'))

    cursor.execute("SELECT * FROM Employee WHERE EmployeeID = %s", (employee_id,))
    employee = cursor.fetchone()
    conn.close()
    return render_template('update_employee.html', employee=employee)


@app.route('/employee_backup')
def employee_backup():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM EmployeeBackup")  # Adjust the query if necessary
        backups = cursor.fetchall()
        cursor.close()
        db.close()
        return render_template('employee_backup.html', backups=backups)
    except Exception as e:
        print(f"Error: {e}")
        flash("An error occurred while fetching employee backups.")
        return redirect('/employee_list')






@app.route('/water_source')
def water_source():
    return render_template('water_source.html')

@app.route('/add_water_source', methods=['POST'])
def add_water_source():
    conn = get_db_connection()
    cursor = conn.cursor()
    source_name = request.form['sourceName']
    source_type = request.form['sourceType']
    capacity = request.form['capacity']
    location = request.form['location']
    
    try:
        cursor.execute("INSERT INTO WaterSource (SourceName, SourceType, Capacity, Location) VALUES (%s, %s, %s, %s)",
                        (source_name, source_type, capacity, location))
        conn.commit()
        flash('Water Source details submitted successfully!', 'success')

        return redirect('/water_source')
    except mysql.connector.Error as e:
        if e.sqlstate == '45000':
            flash(e.msg)
        else:
            flash("An error occurred while adding the water source.")
    finally:
        conn.close()
    
    return redirect('/water_source')


@app.route('/water_source_list')
def water_source_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM WaterSource")
    water_sources = cursor.fetchall()
    
    conn.close()
    return render_template('water_source_list.html', water_sources=water_sources)


@app.route('/water_source_audit')
def water_source_audit():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM WaterSourceAudit")  # Assuming the audit table has all necessary columns
    audits = cursor.fetchall()
    conn.close()
    return render_template('water_source_audit.html', audits=audits)


# Route to display water source alerts triggered by low capacity
@app.route('/water_source_alerts')
def display_trigger_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SourceID, Capacity, AlertMessage FROM WaterSourceAlerts")
    alerts = cursor.fetchall()
    conn.close()
    return render_template('water_source_alerts.html', alerts=alerts)


@app.route('/update_water_source/<int:source_id>', methods=['GET'])
def update_water_source_form(source_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM WaterSource WHERE SourceID = %s", (source_id,))
    source = cursor.fetchone()
    conn.close()
    return render_template('update_water_source.html', source=source)

@app.route('/update_water_source/<int:source_id>', methods=['POST'])
def update_water_source(source_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    source_name = request.form['sourceName']
    source_type = request.form['sourceType']
    capacity = request.form['capacity']
    location = request.form['location']
    
    # Fetch the old source type for auditing
    cursor.execute("SELECT SourceType FROM WaterSource WHERE SourceID = %s", (source_id,))
    old_source_type = cursor.fetchone()[0]

    try:
        cursor.execute("""
            UPDATE WaterSource 
            SET SourceName = %s, SourceType = %s, Capacity = %s, Location = %s 
            WHERE SourceID = %s
        """, (source_name, source_type, capacity, location, source_id))

        conn.commit()
        
        # Check if SourceType is being updated and log it
        if old_source_type != source_type:
            cursor.execute("""
                INSERT INTO WaterSourceAudit (SourceID, OldSourceType, NewSourceType, ChangedBy)
                VALUES (%s, %s, %s, USER())
            """, (source_id, old_source_type, source_type))

        conn.commit()
        flash('Water Source details updated successfully!', 'success')
    except mysql.connector.Error as e:
        flash("An error occurred while updating the water source.")
    finally:
        conn.close()
    
    return redirect('/water_source_list')





# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)
