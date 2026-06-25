frappe.ui.form.on("Employee", {
    onload: function(frm) {
        frm.fields_dict["status"].df.options = "Active\nInactive\nSuspended\nLeft\nAnnual Leave";
        frm.refresh_field("status");

        var tracker_fields = [
            'custom_passport_attach', 'custom_medical_attach', 'custom_bls_attach',
            'custom_certificate_attach', 'custom_data_flow_attach', 'custom_prometric_attach',
            'custom_cv_attach', 'custom_police_clearance_attach', 'custom_acls_attach',
            'custom_noc_attach', 'custom_offer_letter_attach', 'custom_civil_id_attach',
            'custom_mol_contract_attach', 'custom_license_attach', 'custom_visa'
        ];

        var original_clear = frappe.ui.form.ControlAttach.prototype.clear_attachment;
        frappe.ui.form.ControlAttach.prototype.clear_attachment = function() {
            var self = this;
            if (tracker_fields.includes(self.df.fieldname)) {
                var d = frappe.confirm(
                    'Are you sure you want to clear this attachment?',
                    function() {
                        original_clear.call(self);
                    }
                );
            } else {
                original_clear.call(self);
            }
        };
    }
});
