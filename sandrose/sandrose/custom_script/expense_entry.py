import frappe

def link_journal_entry_to_expense_entry(doc, method):
    """
    When Expense Entry is submitted, link its Journal Entry ID if exists.
    """
    # Check if a Journal Entry was already created by the Expense Request app
    je_name = frappe.db.get_value("Journal Entry", {"bill_no": doc.name}, "name")
    
    if je_name and not doc.custom_journal_entry_id:
        doc.db_set("custom_journal_entry_id", je_name)
        frappe.msgprint(f"Linked Journal Entry <b>{je_name}</b> to Expense Entry <b>{doc.name}</b>.")

def cancel_linked_journal_entry(doc, method):
    """
    Cancel the Journal Entry linked to this Expense Entry when it is cancelled.
    """

    # Try to get linked journal entry from the field
    je_name = doc.custom_journal_entry_id or frappe.db.get_value("Journal Entry", {"bill_no": doc.name}, "name")

    if not je_name:
        frappe.msgprint("No linked Journal Entry found for this Expense Entry.")
        return

    try:
        je = frappe.get_doc("Journal Entry", je_name)
        if je.docstatus == 1:
            je.cancel()
            frappe.msgprint(f"Journal Entry <b>{je_name}</b> cancelled as Expense Entry was cancelled.")
        else:
            frappe.msgprint(f"Journal Entry <b>{je_name}</b> is already cancelled or in draft.")
        doc.db_set("custom_journal_entry_id", None)
    except Exception as e:
        frappe.throw(f"Unable to cancel linked Journal Entry {je_name}: {str(e)}")

def calculate_totals(doc, method):

    total = 0
    count = 0
    expense_items = []

    
    for detail in doc.expenses:
        total += float(detail.amount)        
        count += 1
        
        if not detail.project and doc.default_project:
            detail.project = doc.default_project
        
        if not detail.cost_center and doc.default_cost_center:
            detail.cost_center = doc.default_cost_center

        expense_items.append(detail)

    doc.expenses = expense_items

    doc.total = total
    doc.quantity = count