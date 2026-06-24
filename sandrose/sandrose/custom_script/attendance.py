import frappe

@frappe.whitelist()
def update_attendance_fields(attendance, method):
    # Fetch employee details
    employee = attendance.employee

    # Fetch overtime rate from Employee DocType
    overtime_rate = frappe.db.get_value("Employee", employee, "custom_overtime_rate") or 0

    # Calculate Overtime Amount
    overtime_hours = attendance.custom_overtime_hours or 0
    overtime_amount = overtime_hours * overtime_rate

    # Fetch Latest Salary Structure Assignment
    salary_structure = frappe.get_all("Salary Structure Assignment",
        filters={"employee": employee},
        fields=["base"],
        order_by="creation desc",
        limit=1
    )
    
    # Calculate Salary Amount
    salary_amount = (salary_structure[0].base / 30) if salary_structure else 0

    # Update Attendance record
    attendance.custom_overtime_rate = overtime_rate
    attendance.custom_overtime_amount = overtime_amount
    attendance.custom_salary_amount = salary_amount
