import frappe
from frappe.utils import date_diff


def set_first_day_of_joining(doc, method):
    if not doc.get("custom_first_day_of_joining"):  # Check if field exists
        doc.custom_first_day_of_joining = doc.date_of_joining  # Set only if empty


@frappe.whitelist()
def update_vacation_details(doc, method):
    """Updates the re-entry date in the last vacation entry if blank, otherwise appends a new entry."""

    if not doc.date_of_joining:
        frappe.throw("Joining Date is missing for this Employee.")

    if doc.custom_vacation_details and doc.custom_rejoining == 1:
        last_vacation = doc.custom_vacation_details[-1]  # Get last row
        if last_vacation.date_of_exit:
            if not last_vacation.date_of_re_entry:
                # Update existing entry if re-entry date is blank
                frappe.db.set_value(
                    "Vacation Details", last_vacation.name, {
                        "date_of_re_entry": doc.date_of_joining,
                        "noof_days": frappe.utils.date_diff(doc.date_of_joining, last_vacation.date_of_exit)
                    }
                )
            else:
                # Append a new entry if the last one is already filled
                doc.append("custom_vacation_details", {
                    "date_of_exit": last_vacation.date_of_exit,
                    "date_of_re_entry": doc.date_of_joining,
                    "noof_days": frappe.utils.date_diff(doc.date_of_joining, last_vacation.date_of_exit)
                })
                doc.save()  # Save only if a new entry is added

            # Reset the rejoining flag
            frappe.db.set_value("Employee", doc.name, "custom_rejoining", 0)
            
            frappe.db.commit()

            frappe.msgprint("Vacation details updated successfully.")
            doc.reload()
        else:
            frappe.throw("Date of Exit is not set in the last vacation entry.")
    


from datetime import datetime

@frappe.whitelist()
def calculate_flight_charge(employee, date_of_exit):
    employee_doc = frappe.get_doc("Employee", employee)
    flight_rate = employee_doc.get("custom_flight_rate", 0)

    if not date_of_exit or not employee_doc.date_of_joining:
        return 0  # Return 0 if missing data

    # # Parse date_of_exit as string if it is not already a date object
    # date_of_exit = datetime.strptime(date_of_exit, "%Y-%m-%d").date() if isinstance(date_of_exit, str) else date_of_exit

    # # Use date_of_joining directly if it is already a datetime.date object
    # date_of_joining = employee_doc.date_of_joining if isinstance(employee_doc.date_of_joining, datetime.date) else datetime.strptime(employee_doc.date_of_joining, "%Y-%m-%d").date()
    no_of_days= abs(frappe.utils.date_diff(employee_doc.date_of_joining, date_of_exit))
    # no_of_days = (date_of_exit - date_of_joining).days
    flight_charge = no_of_days * flight_rate

    return flight_charge

@frappe.whitelist()
def calculate_gratuity(employee, date_of_exit):
    employee_doc = frappe.get_doc("Employee", employee)
    gratuity_rate = employee_doc.get("custom_gratuity_rate", 0)

    if not date_of_exit or not employee_doc.date_of_joining:
        return 0  # Return 0 if missing data

    no_of_days= abs(frappe.utils.date_diff(employee_doc.date_of_joining, date_of_exit))
    gratuity = no_of_days * gratuity_rate

    return gratuity

@frappe.whitelist()
def update_gratuity_days(employee, row_name, date_of_exit):
    employee_doc = frappe.get_doc("Employee", employee)

    if not date_of_exit or not employee_doc.date_of_joining:
        return  # Exit if data is missing

    # Calculate the number of days
    no_of_days = abs(frappe.utils.date_diff(employee_doc.date_of_joining, date_of_exit))

    # Find the correct row in Vacation Details by row_name (name field in child table)
    # for vacation in employee_doc.custom_vacation_details:
    #     if vacation.name == row_name:  # Ensure we update the correct row
    #         vacation.gratuity_days = no_of_days
    #         break

    # # Save changes to Employee document
    # employee_doc.save(ignore_permissions=True)
    # frappe.db.commit()

    return no_of_days
