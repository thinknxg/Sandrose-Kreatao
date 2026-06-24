import frappe
from frappe.utils import nowdate

@frappe.whitelist()
def get_project_salary_data(project_name):
    if not project_name:
        return {}

    filters = {
        "project": project_name,
        "from_date": "2025-01-01",  # You can replace this with dynamic fiscal start if needed
        "to_date": nowdate()
    }

    # --- Fetch Salary & Overtime from Attendance ---
    salary_data = frappe.db.sql("""
        SELECT 
            SUM(custom_salary_amount) AS total_salary,
            SUM(custom_overtime_amount) AS total_overtime
        FROM `tabAttendance`
        WHERE custom_project = %(project)s 
          AND attendance_date BETWEEN %(from_date)s AND %(to_date)s
    """, filters, as_dict=True)[0]

    # --- Fetch Retention Bonus from Retention Bonus DocType ---
    bonus_data = frappe.db.sql("""
        SELECT 
            SUM(bonus_amount) AS total_bonus
        FROM `tabRetention Bonus`
        WHERE custom_project = %(project)s 
          AND salary_component = 'Contract' 
          AND bonus_payment_date BETWEEN %(from_date)s AND %(to_date)s
    """, filters, as_dict=True)[0]

    # Handle nulls and compute total
    total_salary = salary_data.get("total_salary") or 0
    total_overtime = salary_data.get("total_overtime") or 0
    total_bonus = bonus_data.get("total_bonus") or 0

    total_cost = total_salary + total_overtime + total_bonus

    return {
        "total_salary": total_salary,
        "total_overtime": total_overtime,
        "total_bonus": total_bonus,
        "total_cost": total_cost
    }
