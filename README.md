# Medicine Distribution Management System

#### Video Demo: https://youtu.be/bdrybQTbuQI

## 1. Introduction

Medicine Distribution Management System is a web application. It helps an administrator manage beneficiaries, medicines, medicine inventory, monthly medicine distribution, and track stock.

Before this system, the process was done by hand. This was slow and hard to organize. This application solves that problem.

## 2. Main Features

The application provides several features for managing the complete medicine-distribution workflow:

1. **Administrator Login**

   * The system starts with a login page for the administrator.
   * After a successful login, the administrator can access the management pages.

2. **Dashboard**

   * Displays the total number of beneficiaries.
   * Displays how many people received their medicine this month.
   * Displays the total medicine stock.
   * Shows medicines whose stock is lower than the required monthly amount.

3. **Medicine Management**

   * Add new medicines.
   * View all medicines and their current stock.
   * Increase or decrease stock quantities.
   * View the required monthly quantity for each medicine.
   * Delete medicines that not assigned to any beneficiary.

4. **Beneficiary Management**

   * Add a new beneficiary.
   * Store the beneficiary's name, phone number, and National ID.
   * Assign multiple medicines to a beneficiary.
   * Specify the required monthly quantity for each medicine.
   * View all registered beneficiaries.
   * View detailed information about a beneficiary.
   * Delete a beneficiary when necessary.

5. **Medicine Distribution**

   * Mark a beneficiary as having received their medicine for the current month.
   * Prevent the same beneficiary from being marked as received more than once during the same month.
   * Check whether enough stock is available before completing the distribution.
   * Automatically decrease the medicine stock after a successful distribution.
   * Save the distribution date and the medicines that were distributed.

6. **Distribution History**

   * View the medicines assigned to each beneficiary.
   * View previous distribution operations.
   * See the medicines and quantities distributed on each recorded date.

## 3. How It Works

The workflow is simple:

1. The administrator logs in.
2. They add medicines and set the stock.
3. They add beneficiaries and select the medicines they need every month.
4. The system stores the relationship between each beneficiary and their required medicines.
5. Each month, the administrator marks when a person receives their medicine by using the **Complete** action.
6. If everything is valid, the stock is reduced and the distribution is recorded.
7. The administrator can check the history at any time.

## 4. Database Design

The project uses **SQLite** as its database. The database has five tables:

* `beneficiaries` Beneficiary names, phone numbers, and IDs.
* `medicines` Medicine names and stock amounts.
* `beneficiary_medicines` Links beneficiaries to their medicines and quantities
* `dispenses` Each distribution operation and its date
* `dispense_items` The medicines and amounts in each operation

One beneficiary can have many medicines. One distribution operation can include many medicines.
The tables keep this information organized and connected.

## 5. Project Structure

The project is mainly divided into the application logic, database logic, HTML templates, and CSS.

### `app.py`

This is the main file. It handles all routes and actions.

### `database.py`

This file connects to the database. It also creates the tables when the program starts.

### `templates/layout.html`

Shared layout with the navigation bar.

### `templates/login.html`

The login page.

### `templates/home.html`

The dashboard.

### `templates/medicine.html`

Medicine management.

### `templates/add_beneficiary.html`

Form to add a new beneficiary.

### `templates/beneficiaries.html`

Table for all beneficiaries.

### `templates/view_beneficiaries.html`

Detail page for each beneficiary.

### `static/css/style.css`

It includes the dark theme, card design, and form styles.

## 6. Technologies Used

The project was built using:

* **Backend**: Python, Flask
* **Database**: SQL, SQLite
* **Frontend**: HTML, CSS, JS, Bootstrap

## 7. Validation and Data Integrity

The system checks three fields before saving a new beneficiary.

Name: It must be at least 3 characters. It can use English or Arabic letters only.
Phone number: It must be an Egyptian number. It must start with 010, 011, 012, or 015. It must be 11 digits.
National ID: It must be 14 digits. It must start with 2 or 3. It must also contain a valid Egyptian governorate code. The system checks this in two places: in the browser before the form is sent, and on the server after it arrives.

## 8. Design Decisions

The system uses a separate `beneficiary_medicines` table. This lets one beneficiary have many medicines. It keeps the database clean.

The `dispenses` table stores the operation. `dispense_items` stores the medicines and quantities in that operation.

SQLite was chosen because it is simple and lightweight.

Bootstrap was chosen because it has ready-made components. This saves time and makes the interface look clean.

## 9. Future Improvements

The current version implements the main workflow of the system, but there are several areas that could be improved in future versions.

Some possible improvements include:

1. A more advanced login system.
2. Search and filter options for long tables.
3. More detailed reports and statistics.
4. Better error messages and input checks.
5. Support for a larger database as the project grows.

These features can be added in future versions.

## 10. Conclusion

This project was built as part of CS50x. It covers the full workflow: adding medicines, managing beneficiaries, recording distribution, and tracking stock.

This system is based on a real need. A local non-profit pharmacy does this work by hand every month. This project was built with that pharmacy in mind. The goal is to develop it further and offer it to them for free.

This is still a demo. It is not a complete product yet. But the core workflow is real, and the problem it solves is real.
