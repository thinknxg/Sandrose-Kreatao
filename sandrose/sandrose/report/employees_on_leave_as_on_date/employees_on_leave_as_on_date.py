import frappe
from frappe import _
from frappe.utils import getdate, date_diff


def execute(filters=None):
    if not filters:
        filters = {}

    as_on_date = getdate(filters.get("as_on_date") or frappe.utils.today())
    company = filters.get("company")

    columns = get_columns()
    data = get_data(as_on_date, company)
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


def get_data(as_on_date, company=None):
    conditions = ""
    emp_conditions = ""
    params = {"as_on_date": as_on_date}

    if company:
        conditions = "AND e.company = %(company)s"
        emp_conditions = "AND e.company = %(company)s"
        params["company"] = company

    # --- Part 1: Leave Application based rows ---
    all_leaves = frappe.db.sql("""
        SELECT
            la.name,
            la.employee,
            la.employee_name,
            la.leave_type,
            la.from_date,
            la.to_date,
            la.total_leave_days,
            la.custom_actual_rejoin_date,
            e.grade,
            e.designation,
            e.employment_type,
            e.cell_number
        FROM `tabLeave Application` la
        INNER JOIN `tabEmployee` e ON e.name = la.employee
        WHERE
            la.docstatus = 1
            AND la.status = 'Approved'
            AND la.from_date <= %(as_on_date)s
            {conditions}
        ORDER BY la.employee, la.from_date DESC
    """.format(conditions=conditions), params, as_dict=True)

    # Keep only each employee's most recent leave application
    latest_per_employee = {}
    for row in all_leaves:
        if row.employee not in latest_per_employee:
            latest_per_employee[row.employee] = row

    # Only include if not yet rejoined
    relevant_leaves = []
    leave_app_employees = set()
    for row in latest_per_employee.values():
        rejoin_date = row.custom_actual_rejoin_date
        if not rejoin_date or getdate(rejoin_date) > as_on_date:
            # Check for leave extensions - use latest extended_to_date if exists
            extension = frappe.db.sql(
                "SELECT extended_to_date FROM `tabLeave Extension` WHERE parent = %s ORDER BY extended_to_date DESC LIMIT 1",
                (row.name,), as_dict=True
            )
            if extension and extension[0].extended_to_date:
                row.to_date = extension[0].extended_to_date
            relevant_leaves.append(row)
            leave_app_employees.add(row.employee)

    # --- Part 2: Employees with status "Annual Leave" (no Leave Application) ---
    annual_leave_emps = frappe.db.sql("""
        SELECT
            e.name as employee,
            e.employee_name,
            e.grade,
            e.designation,
            e.employment_type,
            e.cell_number,
            e.custom_expected_rejoin_date
        FROM `tabEmployee` e
        WHERE
            e.status = 'Annual Leave'
            {emp_conditions}
    """.format(emp_conditions=emp_conditions), params, as_dict=True)

    for emp in annual_leave_emps:
        if emp.employee in leave_app_employees:
            continue

        # Get latest vacation details entry with date_of_exit set and no re-entry
        vacation = frappe.db.sql("""
            SELECT date_of_exit, date_of_re_entry
            FROM `tabVacation Details`
            WHERE parent = %(employee)s
              AND date_of_exit IS NOT NULL
              AND date_of_exit <= %(as_on_date)s
              AND (date_of_re_entry IS NULL OR date_of_re_entry = '')
            ORDER BY date_of_exit DESC
            LIMIT 1
        """, {"employee": emp.employee, "as_on_date": as_on_date}, as_dict=True)

        from_date = vacation[0].date_of_exit if vacation else None
        expected_rejoin = emp.custom_expected_rejoin_date

        # Allowed = planned days (date_of_exit to expected_rejoin_date)
        if from_date and expected_rejoin:
            allowed = int(date_diff(expected_rejoin, from_date))
        else:
            allowed = 0

        # Excess = days past expected rejoin date
        if expected_rejoin and getdate(expected_rejoin) < as_on_date:
            excess = int(date_diff(as_on_date, expected_rejoin))
        else:
            excess = None

        relevant_leaves.append(frappe._dict({
            "employee":                  emp.employee,
            "employee_name":             emp.employee_name,
            "leave_type":                "Annual Leave",
            "from_date":                 from_date,
            "to_date":                   expected_rejoin,
            "total_leave_days":          allowed,
            "custom_actual_rejoin_date": None,
            "grade":                     emp.grade,
            "designation":               emp.designation,
            "employment_type":           emp.employment_type,
            "cell_number":               emp.cell_number,
            "_allowed":                  allowed,
            "_excess":                   excess,
            "_is_annual_leave":          True,
        }))

    relevant_leaves.sort(key=lambda r: (r.grade or "", r.leave_type or "", r.employee or ""))

    data = []
    for row in relevant_leaves:
        # For Annual Leave rows use pre-calculated values
        if row.get("_is_annual_leave"):
            allowed = row._allowed
            excess = row._excess
        else:
            if row.from_date and row.to_date:
                allowed = int(date_diff(row.to_date, row.from_date)) + 1
            else:
                allowed = int(row.total_leave_days or 0)
            is_overdue = row.to_date and getdate(row.to_date) < as_on_date
            excess = int(date_diff(as_on_date, row.to_date)) if is_overdue else None

        data.append({
            "employee":        row.employee,
            "employee_name":   row.employee_name,
            "designation":     row.designation,
            "department":      row.grade,
            "employment_type": row.employment_type,
            "leave_type":      row.leave_type,
            "from_date":       row.from_date,
            "to_date":         row.to_date,
            "rejoined":        row.custom_actual_rejoin_date,
            "allowed":         allowed,
            "excess":          excess,
            "cell_number":     row.cell_number,
        })

    return data
