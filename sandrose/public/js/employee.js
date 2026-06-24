frappe.ui.form.on("Employee", {
    onload: function(frm) {
        frm.fields_dict["status"].df.options = "Active\nInactive\nSuspended\nLeft\nAnnual Leave";
        frm.refresh_field("status");
    }
});
