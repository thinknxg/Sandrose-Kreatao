
frappe.ui.form.on('Vacation Details', {
    flight_charge: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.call({
            method: "sandrose.sandrose.custom_script.employee.calculate_flight_charge",
            args: {
                employee: frm.doc.name,
                date_of_exit: row.date_of_exit
            },
            callback: function(r) {
                if (r.message) {
                    frappe.model.set_value(cdt, cdn, "flight_charges", r.message);
                    frm.refresh_field("custom_vacation_details");
                }
            }
        });
    },

    gratuity: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.call({
            method: "sandrose.sandrose.custom_script.employee.calculate_gratuity",
            args: {
                employee: frm.doc.name,
                date_of_exit: row.date_of_exit
            },
            callback: function(r) {
                if (r.message) {
                    frappe.model.set_value(cdt, cdn, "gratuity_amount", r.message);
                    frm.refresh_field("custom_vacation_details");
                }
            }
        });
    },

    date_of_exit: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.date_of_exit) {
            frappe.call({
                method: "sandrose.sandrose.custom_script.employee.update_gratuity_days",
                args: {
                    employee: frm.doc.name,
                    row_name: row.name,
                    date_of_exit: row.date_of_exit
                },
                callback: function(r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, "gratuity_days", r.message);
                        frm.refresh_field("vacation_details");
                    }
                }
            });
        }
    }
});
