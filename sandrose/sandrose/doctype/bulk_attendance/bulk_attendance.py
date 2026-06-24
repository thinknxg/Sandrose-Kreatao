# Copyright (c) 2025, Sandrose and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, add_days

class BulkAttendance(Document):

	def on_submit(self):
		for row in self.attendance_details:
			# Create Attendance
			attendance = frappe.new_doc("Attendance")
			attendance.employee = self.employee
			attendance.attendance_date = row.day
			attendance.status = row.status
			attendance.custom_project = row.job
			attendance.custom_overtime_hours = row.ot_hours
			attendance.insert()
			# attendance.save()
			attendance.submit()
			frappe.db.commit()

			# If contract, create Retention Bonus
			if row.is_contract:
				bonus = frappe.new_doc("Retention Bonus")
				bonus.employee = self.employee
				bonus.bonus_payment_date = row.day
				bonus.bonus_amount = row.bonus_amount
				bonus.custom_project = row.job
				bonus.salary_component = "Contract"  # adjust as needed
				bonus.insert()
				# bonus.save()
				bonus.submit()
				frappe.db.commit()
				# frappe.db.set_value("Retention Bonus", bonus.name, "custom_project", row.job)

# def get_available_employees(from_date, to_date):
# 	# Get employees already marked in Bulk Attendance within date range
# 	marked_employees = frappe.get_all(
# 		"Bulk Attendance",
# 		filters={"from": ["<=", to_date], "to": [">=", from_date],"docstatus":1},
# 		fields=["employee"]
# 	)
# 	marked_employee_ids = list({emp["employee"] for emp in marked_employees})

# 	# Get all employees
# 	all_employees = frappe.get_all("Employee", filters={"status": "Active"}, pluck="name")

# 	# Return those not marked
# 	unmarked = list(set(all_employees) - set(marked_employee_ids))
# 	return unmarked

# @frappe.whitelist()
# def get_available_employees(from_date, to_date, category=None):
# 	# Get active employees with grade/category
# 	category_employees = frappe.get_all(
# 		"Employee",
# 		filters={"status": "Active", "grade": category},
# 		fields=["name", "employee_name"]
# 	)

# 	if not category_employees:
# 		return []

# 	# Get marked employees
# 	marked_employees = frappe.get_all(
# 		"Bulk Attendance",
# 		filters={
# 			"from": ["<=", to_date],
# 			"to": [">=", from_date],
# 			"docstatus": 1
# 		},
# 		fields=["employee"]
# 	)

# 	marked_employee_ids = {emp["employee"] for emp in marked_employees if emp.get("employee")}

# 	# Filter only unmarked employees
# 	unmarked = [
# 		{"employee": emp["name"], "employee_name": emp["employee_name"]}
# 		for emp in category_employees
# 		if emp["name"] not in marked_employee_ids
# 	]

# 	return unmarked

@frappe.whitelist()
def get_available_employees(from_date, to_date, category=None):
    # Get active employees with grade/category
    category_employees = frappe.get_all(
        "Employee",
        filters={"status": "Active", "grade": category} if category else {"status": "Active"},
        fields=["name", "employee_name"]
    )

    if not category_employees:
        return []

    # Get marked employees in Bulk Attendance
    marked_employees = frappe.get_all(
        "Bulk Attendance",
        filters={
            "from": ["<=", to_date],
            "to": [">=", from_date],
            "docstatus": 1
        },
        fields=["employee"]
    )

    marked_employee_ids = {emp["employee"] for emp in marked_employees if emp.get("employee")}

    unmarked = []
    for emp in category_employees:
        if emp["name"] not in marked_employee_ids:
            leave_type = None

            # Check if employee has leave application in the given range
            leave_app = frappe.db.sql(
                """
                SELECT leave_type 
                FROM `tabLeave Application`
                WHERE employee = %s
                  AND from_date <= %s
                  AND to_date >= %s
                  AND docstatus != 2
                ORDER BY creation DESC
                LIMIT 1
                """,
                (emp["name"], to_date, from_date),
                as_dict=True,
            )

            if leave_app:
                leave_type = leave_app[0].leave_type
                print("leave---",leave_type)
            unmarked.append({
                "employee": emp["name"],
                "employee_name": emp["employee_name"],
                "leave_type": leave_type
            })

    return unmarked


# @frappe.whitelist()
# def get_non_submitted_holidays(from_date, to_date, holiday_list=None, company=None):
#     holidays = frappe.get_all(
#         "Holiday",
#         filters={
#             "holiday_date": ["between", [from_date, to_date]],
#             "docstatus": ["!=", 1],  # include submitted holidays
#             "parenttype": "Holiday List"
#         },
#         fields=["holiday_date"]
#     )
#     return holidays
@frappe.whitelist()
def get_leave_dates(from_date, to_date, employee=None):
    # Get leave applications overlapping the date range
    filters = {
        "from_date": ["<=", to_date],
        "to_date": [">=", from_date],
        "docstatus": 1  # only submitted leaves
    }
    if employee:
        filters["employee"] = employee

    leave_apps = frappe.get_all(
        "Leave Application",
        filters=filters,
        fields=["from_date", "to_date"]
    )

    leave_dates = []
    for leave in leave_apps:
        start = getdate(leave.from_date)
        end = getdate(leave.to_date)
        while start <= end:
            if from_date <= str(start) <= to_date:
                leave_dates.append({"leave_date": str(start)})
            start = add_days(start, 1)

    return leave_dates