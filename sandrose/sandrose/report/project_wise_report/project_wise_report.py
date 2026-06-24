
import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    # Ensure filters have default values
    filters.setdefault("project", "")
    filters.setdefault("from_date", "2025-01-01")  # Safe default
    filters.setdefault("to_date", "2025-12-31")  # Safe default
    filters.setdefault("grade", "")


    # Prepare SQL conditions dynamically
    conditions = "att.custom_project = %(project)s AND att.attendance_date BETWEEN %(from_date)s AND %(to_date)s"

    if filters.get("grade"):
        conditions += " AND emp.grade = %(grade)s"

    # Fetch Salary & Overtime Amount from Attendance
    salary_data = frappe.db.sql(f"""
        SELECT 
            att.custom_project,
            emp.grade,                   
            SUM(att.custom_salary_amount) AS total_salary,
            SUM(att.custom_overtime_amount) AS total_overtime
        FROM `tabAttendance` att
        LEFT JOIN `tabEmployee` emp ON emp.name = att.employee
        WHERE {conditions}
        GROUP BY att.custom_project, emp.grade
    """, filters, as_dict=True)


    # Fetch Retention Bonus Amount from Retention Bonus DocType
    bonus_conditions = "rb.custom_project = %(project)s AND rb.salary_component = 'Contract' AND rb.bonus_payment_date BETWEEN %(from_date)s AND %(to_date)s"

    if filters.get("grade"):
        bonus_conditions += " AND emp.grade = %(grade)s"

    bonus_data = frappe.db.sql(f"""
        SELECT 
            rb.custom_project,
            emp.grade,                 
            SUM(rb.bonus_amount) AS total_bonus
        FROM `tabRetention Bonus` rb
        LEFT JOIN `tabEmployee` emp ON emp.name = rb.employee
        WHERE {bonus_conditions}
        GROUP BY rb.custom_project, emp.grade
    """, filters, as_dict=True)

    # Merge Data
    report_data = {}
    
    for row in salary_data:
        pj = (row["custom_project"], row["grade"])
        report_data[pj] = {
            "project": row["custom_project"],
            "grade": row["grade"],
            "total_salary": row["total_salary"] or 0,
            "total_overtime": row["total_overtime"] or 0,
            "total_bonus": 0  # Default
        }

    for row in bonus_data:
        pj = (row["custom_project"], row["grade"])
        if pj in report_data:
            report_data[pj]["total_bonus"] = row["total_bonus"] or 0
        else:
            report_data[pj] = {
                "project": [row["custom_project"]],
                "grade": row["grade"],
                "total_salary": 0,
                "total_overtime": 0,
                "total_bonus": row["total_bonus"] or 0
            }

    # Add Grand Total column row-wise
    total_salary_sum = 0
    total_overtime_sum = 0
    total_bonus_sum = 0
    grand_total_sum = 0

    data = []

    for row in report_data.values():

        # Grand total calculation per row
        row["grand_total"] = (
            (row["total_salary"] or 0) +
            (row["total_overtime"] or 0) +
            (row["total_bonus"] or 0)
        )

        total_salary_sum += row["total_salary"]
        total_overtime_sum += row["total_overtime"]
        total_bonus_sum += row["total_bonus"]
        grand_total_sum += row["grand_total"]

        data.append(row)

    # FINAL SUMMARY TOTAL ROW
    summary_row = {
        "project": "TOTAL",
        "grade": "",
        "total_salary": total_salary_sum,
        "total_overtime": total_overtime_sum,
        "total_bonus": total_bonus_sum,
        "grand_total": grand_total_sum
    }
    data.append(summary_row)


    # >>> ADDED — FINAL GRAND TOTAL ONLY ROW
    # grand_total_only_row = {
    #     "project": "GRAND TOTAL",
    #     "grade": "",
    #     "total_salary": "",
    #     "total_overtime": "",
    #     "total_bonus": "",
    #     "grand_total": grand_total_sum
    # }

    # data.append(grand_total_only_row)

    # Convert to List for Report Output
    columns = [
        {"label": "Project", "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 200},
        {"label": "Grade", "fieldname": "grade", "fieldtype": "Link", "options": "Employee Grade", "width": 150},
        {"label": "Total Salary", "fieldname": "total_salary", "fieldtype": "Currency", "width": 150},
        {"label": "Total Overtime", "fieldname": "total_overtime", "fieldtype": "Currency", "width": 150},
        {"label": "Total Bonus (Contract)", "fieldname": "total_bonus", "fieldtype": "Currency", "width": 150},
        {"label": "Grand Total", "fieldname": "grand_total", "fieldtype": "Currency", "width": 160},
    ]

    # data = list(report_data.values())

    return columns, data

