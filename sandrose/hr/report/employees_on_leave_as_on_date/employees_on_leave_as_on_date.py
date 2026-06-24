import frappe
from frappe import _
from frappe.utils import getdate, date_diff


def execute(filters=None):
    if not filters:
        filters = {}

    as_on_date = getdate(filters.get("as_on_date") or frappe.utils.today())

    columns = get_columns()
    data = get_data(as_on_date)
    return columns, data


def get_columns():
    return [
        {"label": _("Code"),        "fieldname": "employee",       "fieldtype": "Link", "options": "Employee", "width": 110},
        {"label": _("Name"),        "fieldname": "employee_name",  "fieldtype": "Data", "width": 180},
        {"label": _("Designation"), "fieldname": "designation",    "fieldtype": "Data", "width": 150},
        {"label": _("Department"),  "fieldname": "department",     "fieldtype": "Data", "width": 180},
        {"label": _("Category"),    "fieldname": "employment_type","fieldtype": "Data", "width": 100},
        {"label": _("Leave Type"),  "fieldname": "leave_type",     "fieldtype": "Data", "width": 140},
        {"label": _("Leave From"),  "fieldname": "from_date",      "fieldtype": "Date", "width": 100},
        {"label": _("Leave To"),    "fieldname": "to_date",        "fieldtype": "Date", "width": 100},
        {"label": _("Rejoined"),    "fieldname": "rejoined",       "fieldtype": "Date", "width": 100},
        {"label": _("Allowed"),     "fieldname": "allowed",        "fieldtype": "Int",  "width": 80},
        {"label": _("Excess"),      "fieldname": "excess",         "fieldtype": "Int",  "width": 80},
        {"label": _("Contact"),     "fieldname": "cell_number",    "fieldtype": "Data", "width": 130},
    ]


def get_data(as_on_date):
    leaves = frappe.db.sql("""
        SELECT
            la.employee,
            la.employee_name,
            la.leave_type,
            la.from_date,
            la.to_date,
            la.total_leave_days,
            la.department,
            e.designation,
            e.employment_type,
            e.cell_number,
            e.custom_rejoining
        FROM `tabLeave Application` la
        INNER JOIN `tabEmployee` e ON e.name = la.employee
        WHERE
            la.docstatus = 1
            AND la.status = 'Approved'
            AND la.from_date <= %(as_on_date)s
            AND la.to_date >= %(as_on_date)s
        ORDER BY la.department, la.leave_type, la.employee
    """, {"as_on_date": as_on_date}, as_dict=True)

    data = []
    for row in leaves:
        allowed = get_leave_allocation(row.employee, row.leave_type, as_on_date)

        taken = row.total_leave_days or 0
        excess = int(taken - allowed) if (allowed is not None and taken > allowed) else None

        rejoined = None
        if row.custom_rejoining and getdate(row.to_date) < as_on_date:
            rejoined = row.custom_rejoining

        data.append({
            "employee":        row.employee,
            "employee_name":   row.employee_name,
            "designation":     row.designation,
            "department":      row.department,
            "employment_type": row.employment_type,
            "leave_type":      row.leave_type,
            "from_date":       row.from_date,
            "to_date":         row.to_date,
            "rejoined":        rejoined,
            "allowed":         int(allowed) if allowed is not None else 0,
            "excess":          excess,
            "cell_number":     row.cell_number,
        })

    return data


def get_leave_allocation(employee, leave_type, as_on_date):
    result = frappe.db.sql("""
        SELECT total_leaves_allocated
        FROM `tabLeave Allocation`
        WHERE
            employee   = %(employee)s
            AND leave_type = %(leave_type)s
            AND docstatus  = 1
            AND from_date  <= %(as_on_date)s
            AND to_date    >= %(as_on_date)s
        ORDER BY from_date DESC
        LIMIT 1
    """, {
        "employee":   employee,
        "leave_type": leave_type,
        "as_on_date": as_on_date,
    })

    return result[0][0] if result else None
