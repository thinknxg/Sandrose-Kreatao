import frappe
from frappe import _
from frappe.utils import getdate
from hrms.payroll.doctype.retention_bonus.retention_bonus import RetentionBonus
from hrms.hr.utils import validate_active_employee

class CustomRetentionBonus(RetentionBonus):
    def validate(self):
        validate_active_employee(self.employee)

        # Custom Logic: Allow past dates or modify validation
        if self.bonus_payment_date and getdate(self.bonus_payment_date) < getdate():
            frappe.msgprint(_("Warning: Bonus Payment Date is in the past"), alert=True)

def on_submit(doc, method):
    if doc.salary_component == "Contract" and doc.bonus_payment_date:
        # Check if attendance already exists for the bonus date
        attendance = frappe.get_value(
            "Attendance",
            {"employee": doc.employee, "attendance_date": doc.bonus_payment_date},
            ["name", "status"]
        )

        if attendance:
            # If attendance exists, update the status to 'Absent'
            frappe.db.set_value("Attendance", attendance[0], "status", "Absent")
        else:
            # If attendance does not exist, create a new attendance record
            new_attendance = frappe.get_doc({
                "doctype": "Attendance",
                "employee": doc.employee,
                "attendance_date": doc.bonus_payment_date,
                "status": "Absent",
                "company": doc.company,
                "custom_project" : doc.custom_project,
                "custom_cost_center" : doc.custom_cost_center
            })
            new_attendance.insert(ignore_permissions=True)

        # Update Contract Days in Salary Slip
        # update_contract_days(doc.employee, doc.bonus_payment_date)

        # Commit the changes
        frappe.db.commit()

def update_contract_days(employee, bonus_date):
    # Find the Salary Slip for the employee where the Bonus Date falls within the payroll period
    salary_slips = frappe.get_all(
        "Salary Slip",
        filters={
            "employee": employee,
            "start_date": ["<=", bonus_date],
            "end_date": [">=", bonus_date]
        },
        fields=["name", "custom_contract_days"]
    )

    for slip in salary_slips:
        # Increment the contract_days field
        new_contract_days = (slip.custom_contract_days or 0) + 1
        frappe.db.set_value("Salary Slip", slip.name, "custom_contract_days", new_contract_days)
