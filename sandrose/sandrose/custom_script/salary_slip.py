import frappe

def before_save(doc, method):
    if not doc.start_date or not doc.end_date:
        return
    
    # Count Retention Bonus records where Salary Component is "Contract"
    contract_bonus_count = frappe.db.count(
        "Retention Bonus",
        filters={
            "employee": doc.employee,
            "salary_component": "Contract",
            "bonus_payment_date": ["between", [doc.start_date, doc.end_date]]
        }
    )

    # Set the count to the contract_days field
    doc.custom_contract_days = contract_bonus_count

# In your custom app: custom_app/api/employee.py


@frappe.whitelist()
def get_flight_and_gratuity(employee, start_date, end_date):
    if not frappe.has_permission('Employee', 'read'):
        frappe.throw("You do not have permission to access this resource.", frappe.PermissionError)

    vacation_details = frappe.db.sql("""
        SELECT flight_charges, gratuity_amount FROM `tabVacation Details`
        WHERE parent = %s AND parenttype = 'Employee'
        AND date_of_exit BETWEEN %s AND %s
        ORDER BY date_of_exit DESC LIMIT 1
    """, (employee, start_date, end_date), as_dict=True)

    return vacation_details[0] if vacation_details else {"flight_charges": 0, "gratuity_amount": 0}

