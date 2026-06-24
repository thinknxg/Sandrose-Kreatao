import frappe

@frappe.whitelist()
def calculate_gratuity_on_assignment(doc, method):
    try:
        # Fetch Basic Salary and Food Allowance from the assigned Salary Structure
        salary_structure = frappe.get_doc('Salary Structure', doc.salary_structure)
        basic_salary = next((comp.amount for comp in salary_structure.earnings if comp.salary_component == 'Basic'), 0)
        food_allowance = next((comp.amount for comp in salary_structure.earnings if comp.salary_component == 'Food Allowance'), 0)

        # Calculate Gratuity and Overtime Rate
        gratuity = basic_salary / 365
        overtime_rate = (((basic_salary + food_allowance)*12)/365/8) * 1.25
        leave_encashment = (basic_salary*12) / 365
        # Update Employee DocType
        frappe.db.set_value('Employee', doc.employee, {
            'custom_gratuity_rate': gratuity,
            'custom_overtime_rate': overtime_rate
        })
        frappe.db.commit()
        doc.reload()
        frappe.msgprint(f"Gratuity and Overtime Rate updated for Employee {doc.employee}")

        # Update Salary Structure DocType
        frappe.db.set_value('Salary Structure', doc.employee, {
            'leave_encashment_amount_per_day': leave_encashment
        })
        frappe.db.commit()
        doc.reload()
        frappe.msgprint(f"Leave Encashment Rate updated for Employee {doc.employee}")
    except Exception as e:
        frappe.throw(f"Error calculating gratuity: {str(e)}")
