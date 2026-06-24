import frappe
from frappe import _
from erpnext.setup.doctype.employee.employee import Employee


class CustomEmployee(Employee):
    def validate(self):
        # Temporarily allow Annual Leave by swapping to Left, validating, then swapping back
        if self.status == "Annual Leave":
            self.status = "Left"
            super().validate()
            self.status = "Annual Leave"
        else:
            super().validate()
