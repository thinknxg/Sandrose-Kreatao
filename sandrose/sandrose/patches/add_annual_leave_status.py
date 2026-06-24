import frappe
import json
import os

def execute():
    """Ensure Annual Leave is in Employee status options after any ERPNext update"""
    # Fix via Property Setter (DB level)
    existing = frappe.db.get_value(
        "Property Setter",
        {"doc_type": "Employee", "field_name": "status", "property": "options"},
        "name"
    )
    options = "Active\nInactive\nSuspended\nLeft\nAnnual Leave"
    if existing:
        frappe.db.set_value("Property Setter", existing, "value", options)
    else:
        frappe.get_doc({
            "doctype": "Property Setter",
            "doc_type": "Employee",
            "field_name": "status",
            "property": "options",
            "value": options,
            "property_type": "Text",
            "is_system_generated": 0
        }).insert(ignore_permissions=True)

    # Also fix the JSON file directly
    json_path = frappe.get_app_path("erpnext", "setup", "doctype", "employee", "employee.json")
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            doc = json.load(f)
        for field in doc.get("fields", []):
            if field.get("fieldname") == "status" and "Annual Leave" not in field.get("options", ""):
                field["options"] = "Active\nInactive\nSuspended\nLeft\nAnnual Leave"
        with open(json_path, "w") as f:
            json.dump(doc, f, indent=1)

    frappe.db.commit()
