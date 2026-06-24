import frappe
from frappe.utils import getdate, add_days


@frappe.whitelist()
def sync_attendance_for_extension(leave_application):
    """
    Reconcile Attendance records against the latest Leave Extension date.
    Creates 'On Leave' attendance for newly extended days, and cancels/deletes
    attendance for days beyond a shortened extension.
    """
    doc = frappe.get_doc("Leave Application", leave_application)

    extensions = frappe.get_all(
        "Leave Extension",
        filters={"parent": leave_application},
        fields=["extended_to_date"],
        order_by="extended_to_date desc",
        limit=1,
    )

    original_to_date = getdate(doc.to_date)
    new_end_date = (
        getdate(extensions[0].extended_to_date)
        if extensions
        else original_to_date
    )

    # Existing attendance tied to this leave application, On Leave/Half Day, not cancelled
    existing = frappe.get_all(
        "Attendance",
        filters={
            "leave_application": leave_application,
            "status": ["in", ["On Leave", "Half Day"]],
            "docstatus": ["<", 2],
        },
        fields=["name", "attendance_date"],
    )

    if existing:
        existing_max = max(getdate(e.attendance_date) for e in existing)
    else:
        existing_max = original_to_date

    created = []
    removed = []

    if new_end_date > existing_max:
        # Create On Leave attendance for each new day
        d = add_days(existing_max, 1)

        while d <= new_end_date:
            date_str = d.strftime("%Y-%m-%d")

            attendance_name = frappe.db.exists(
                "Attendance",
                {
                    "employee": doc.employee,
                    "attendance_date": date_str,
                    "docstatus": ("!=", 2),
                },
            )

            if attendance_name:
                att = frappe.get_doc("Attendance", attendance_name)
                att.db_set(
                    {
                        "status": "On Leave",
                        "leave_type": doc.leave_type,
                        "leave_application": doc.name,
                    }
                )
            else:
                att = frappe.new_doc("Attendance")
                att.employee = doc.employee
                att.employee_name = doc.employee_name
                att.attendance_date = date_str
                att.company = doc.company
                att.leave_type = doc.leave_type
                att.leave_application = doc.name
                att.status = "On Leave"
                att.flags.ignore_validate = True
                att.insert(ignore_permissions=True)
                att.submit()

            created.append(date_str)
            d = add_days(d, 1)

    elif new_end_date < existing_max:
        # Cancel/delete attendance for days beyond the shortened extension
        for e in existing:
            if getdate(e.attendance_date) > new_end_date:
                att = frappe.get_doc("Attendance", e.name)
                att.flags.ignore_permissions = True

                if att.docstatus == 1:
                    att.cancel()

                frappe.delete_doc("Attendance", e.name, force=1)
                removed.append(e.attendance_date)

    frappe.db.commit()

    return {
        "new_end_date": str(new_end_date),
        "created": created,
        "removed": [str(r) for r in removed],
    }


def sync_attendance_for_extension_hook(doc, method):
    """doc_events on_update hook for Leave Application"""

    if doc.docstatus != 1:
        return

    try:
        sync_attendance_for_extension(doc.name)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "sync_attendance_for_extension_hook failed",
        )

    try:
        sync_leave_days_and_ledger(doc.name)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "sync_leave_days_and_ledger failed",
        )


def sync_leave_days_and_ledger(leave_application_name):
    """
    Recalculate total_leave_days on Leave Application from from_date to the
    latest submitted extension's extended_to_date (or original to_date if none).
    Also updates the Leave Ledger Entry to match.
    """

    from hrms.hr.doctype.leave_application.leave_application import (
        get_number_of_leave_days,
    )

    lap = frappe.get_doc("Leave Application", leave_application_name)

    extensions = frappe.get_all(
        "Leave Extension",
        filters={
            "parent": leave_application_name,
            "parenttype": "Leave Application",
            "docstatus": 1,
        },
        fields=["extended_to_date"],
        order_by="extended_to_date desc",
        limit=1,
    )

    effective_to_date = (
        extensions[0].extended_to_date
        if extensions
        else lap.to_date
    )

    new_total = get_number_of_leave_days(
        lap.employee,
        lap.leave_type,
        lap.from_date,
        effective_to_date,
        half_day=lap.half_day,
        half_day_date=lap.half_day_date,
    )

    frappe.db.set_value(
        "Leave Application",
        leave_application_name,
        "total_leave_days",
        new_total,
        update_modified=False,
    )

    ledger_name = frappe.db.get_value(
        "Leave Ledger Entry",
        {
            "transaction_name": leave_application_name,
            "transaction_type": "Leave Application",
            "is_expired": 0,
        },
        "name",
    )

    if ledger_name:
        frappe.db.set_value(
            "Leave Ledger Entry",
            ledger_name,
            "leaves",
            -new_total,
            update_modified=False,
        )

    frappe.db.commit()

    frappe.logger().info(
        f"[LeaveExtension] {leave_application_name}: "
        f"total_leave_days={new_total}, "
        f"effective_to={effective_to_date}"
    )


@frappe.whitelist()
def sync_leave_days_and_ledger_api(leave_application_name):
    """
    Whitelisted wrapper so the client script (Extend Leave button) can call
    sync_leave_days_and_ledger directly, instead of relying on the on_update
    hook firing reliably after frappe.client.save on a submitted document.
    """

    sync_leave_days_and_ledger(leave_application_name)

    return frappe.db.get_value(
        "Leave Application",
        leave_application_name,
        "total_leave_days",
    )


@frappe.whitelist()
def add_leave_extension(leave_application, extended_to_date, reason=None):
    """
    Records a Leave Extension against the original (for audit trail), but does
    NOT touch the original's total_leave_days or create submitted attendance
    against it. Instead, creates a separate DRAFT Leave Application covering
    just the extended range, with DRAFT attendance linked to that new record.
    When the new Leave Application is later submitted, its draft attendance
    is auto-submitted via the on_submit hook.
    """
    from frappe.utils import getdate, add_days

    original = frappe.get_doc("Leave Application", leave_application)

    # Determine the start of the new extension range: day after the latest
    # existing extension's end date, or day after original to_date if this
    # is the first extension.
    existing_extensions = frappe.get_all(
        "Leave Extension",
        filters={"parent": leave_application, "parenttype": "Leave Application", "docstatus": 1},
        fields=["extended_to_date"],
        order_by="extended_to_date desc",
        limit=1,
    )
    if existing_extensions:
        new_from_date = add_days(getdate(existing_extensions[0].extended_to_date), 1)
    else:
        new_from_date = add_days(getdate(original.to_date), 1)

    new_to_date = getdate(extended_to_date)

    if new_to_date < new_from_date:
        frappe.throw(
            f"Extended To Date ({new_to_date}) cannot be before {new_from_date}, "
            f"which is the day after the latest existing extension/leave end date."
        )

    # Record the extension row against the original for audit/visa tracking
    extension = frappe.new_doc("Leave Extension")
    extension.parent = leave_application
    extension.parenttype = "Leave Application"
    extension.parentfield = "custom_leave_extensions"
    extension.extended_to_date = extended_to_date
    extension.reason = reason or ""
    extension.extended_on = frappe.utils.today()
    extension.docstatus = 1
    extension.insert(ignore_permissions=True)

    # Reset original to its own range only - extended days now live on the new draft
    original_days = get_leave_days_for_range(
        original.employee, original.leave_type, original.from_date, original.to_date,
        original.half_day, original.half_day_date
    )
    frappe.db.set_value("Leave Application", leave_application, "total_leave_days", original_days, update_modified=False)
    _sync_ledger_entry(leave_application, original_days)

    # Create the new draft Leave Application for the extended range
    new_days = get_leave_days_for_range(
        original.employee, original.leave_type, new_from_date, new_to_date,
        0, None
    )
    new_lap = frappe.new_doc("Leave Application")
    new_lap.employee = original.employee
    new_lap.employee_name = original.employee_name
    new_lap.leave_type = original.leave_type
    new_lap.company = original.company
    new_lap.from_date = new_from_date
    new_lap.to_date = new_to_date
    new_lap.half_day = 0
    new_lap.total_leave_days = new_days
    new_lap.leave_approver = original.leave_approver
    new_lap.custom_original_leave_application = leave_application
    new_lap.insert(ignore_permissions=True)
    frappe.db.commit()

    # Create DRAFT attendance for each day in the new range, linked to the new Leave Application
    d = new_from_date
    created = []
    while d <= new_to_date:
        date_str = d.strftime("%Y-%m-%d")
        if not frappe.db.exists("Attendance", {"employee": original.employee, "attendance_date": date_str, "docstatus": ("!=", 2)}):
            att = frappe.new_doc("Attendance")
            att.employee = original.employee
            att.employee_name = original.employee_name
            att.attendance_date = date_str
            att.company = original.company
            att.leave_type = original.leave_type
            att.leave_application = new_lap.name
            att.status = "On Leave"
            att.flags.ignore_validate = True
            att.insert(ignore_permissions=True)
            # deliberately NOT submitting - stays as Draft (docstatus 0)
            created.append(date_str)
        d = add_days(d, 1)

    frappe.db.commit()

    return {
        "new_leave_application": new_lap.name,
        "original_total_leave_days": original_days,
        "new_total_leave_days": new_days,
        "draft_attendance_created": created
    }


def get_leave_days_for_range(employee, leave_type, from_date, to_date, half_day=0, half_day_date=None):
    """Thin wrapper around HRMS get_number_of_leave_days for reuse here."""
    from hrms.hr.doctype.leave_application.leave_application import get_number_of_leave_days
    return get_number_of_leave_days(
        employee, leave_type, from_date, to_date,
        half_day=half_day, half_day_date=half_day_date
    )


def _sync_ledger_entry(leave_application_name, total_days):
    """Update the Leave Ledger Entry for a Leave Application to match total_days."""
    ledger_name = frappe.db.get_value(
        "Leave Ledger Entry",
        {
            "transaction_name": leave_application_name,
            "transaction_type": "Leave Application",
            "is_expired": 0
        },
        "name"
    )
    if ledger_name:
        frappe.db.set_value("Leave Ledger Entry", ledger_name, "leaves", -total_days, update_modified=False)


def submit_draft_attendance_for_leave(doc, method):
    """
    on_submit hook for Leave Application. If this Leave Application was created
    as a chained extension (has custom_original_leave_application set), submit
    all DRAFT attendance records linked to it.
    """
    if not doc.get("custom_original_leave_application"):
        return
    draft_attendance = frappe.get_all(
        "Attendance",
        filters={"leave_application": doc.name, "docstatus": 0},
        pluck="name"
    )
    for att_name in draft_attendance:
        try:
            att = frappe.get_doc("Attendance", att_name)
            att.submit()
        except Exception:
            frappe.log_error(frappe.get_traceback(), f"submit_draft_attendance_for_leave failed for {att_name}")
    frappe.db.commit()
