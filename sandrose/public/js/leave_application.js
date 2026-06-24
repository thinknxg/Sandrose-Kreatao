frappe.ui.form.on("Leave Application", {
    refresh: function(frm) {
        if (frm.doc.docstatus === 1 && frm.doc.status === "Approved") {

            if (!frm.doc.custom_actual_rejoin_date) {
                frm.add_custom_button(__("Mark as Rejoined"), function() {
                    frappe.prompt(
                        {
                            fieldname: "rejoin_date",
                            label: __("Rejoin Date"),
                            fieldtype: "Date",
                            default: frappe.datetime.get_today(),
                            reqd: 1
                        },
                        function(values) {
                            frappe.db.set_value("Leave Application", frm.doc.name, "custom_actual_rejoin_date", values.rejoin_date)
                                .then(() => {
                                    frappe.show_alert({message: __("Marked as rejoined"), indicator: "green"});
                                    frm.reload_doc();
                                });
                        },
                        __("Mark as Rejoined"),
                        __("Confirm")
                    );
                }, __("Status"));
            }

            frm.add_custom_button(__("Extend Leave"), function() {
                frappe.prompt(
                    [
                        {
                            fieldname: "extended_to_date",
                            label: __("Extended To Date"),
                            fieldtype: "Date",
                            reqd: 1
                        },
                        {
                            fieldname: "reason",
                            label: __("Reason"),
                            fieldtype: "Data"
                        }
                    ],
                    function(values) {
                        frappe.call({
                            method: "sandrose.sandrose.custom_script.leave_extension_attendance.add_leave_extension",
                            args: {
                                leave_application: frm.doc.name,
                                extended_to_date: values.extended_to_date,
                                reason: values.reason || ""
                            },
                            callback: function(r) {
                                frappe.show_alert({message: __("Leave extended successfully"), indicator: "green"});
                                frm.reload_doc();
                            }
                        });
                    },
                    __("Extend Leave"),
                    __("Extend")
                );
            }, __("Status"));
        }
    }
});
