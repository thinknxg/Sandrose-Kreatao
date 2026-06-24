import frappe
@frappe.whitelist()
def get_flight_and_gratuity(employee, start_date, end_date):
    if not frappe.has_permission('Employee', 'read'):
        frappe.throw("You do not have permission to access this resource.", frappe.PermissionError)

    # Get the most recent vacation within the salary period
    vacation_details = frappe.db.sql("""
        SELECT flight_charges, gratuity_amount
        FROM `tabVacation Details`
        WHERE parent = %s
        AND parenttype = 'Employee'
        AND date_of_exit BETWEEN %s AND %s
        ORDER BY date_of_exit DESC
        LIMIT 1
    """, (employee, start_date, end_date), as_dict=True)

    return vacation_details[0] if vacation_details else {
        "flight_charges": 0,
        "gratuity_amount": 0
    }
