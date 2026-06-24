frappe.ui.form.on('Project', {
    onload: function (frm) {
        console.log("project loaded");
        if (!frm.is_new() && frm.doc.name) {
            frappe.call({
                method: "sandrose.sandrose.custom_script.project.get_project_salary_data",
                args: {
                    project_name: frm.doc.name
                },
                callback: function (r) {
                    if (r.message) {
                        // console.log("salary",r.message.total_salary);
                        // console.log("ot",r.message.total_overtime);
                        // console.log("bonus",r.message.total_bonus);
                        // console.log("cost",r.message.total_cost)
                        // // frm.set_value("total_salary", r.message.total_salary);
                        // // frm.set_value("total_overtime", r.message.total_overtime);
                        // // frm.set_value("total_bonus", r.message.total_bonus);
                        // const total_cost = r.message.total_cost || 0;
                        // const current_gross_margin = frm.doc.gross_margin || 0;
                        // console.log("cur margin",current_gross_margin);
                        // const updated_gross_margin = current_gross_margin - total_cost;
                        // console.log(" margin",updated_gross_margin);
                        // frm.set_value("custom_total_cost", r.message.total_cost);
                        // frm.set_value("gross_margin", updated_gross_margin);
                        // // Refresh the fields on the form
                        // frm.refresh_field("custom_total_cost");
                        // frm.refresh_field("gross_margin");
                        // // Calculate and set per_gross_margin if project_value exists
                        // const project_value = frm.doc.project_value || 0;
                        // if (project_value > 0) {
                        //     const per_gross_margin = (updated_gross_margin / project_value) * 100;
                        //     frm.set_value("per_gross_margin", per_gross_margin.toFixed(2));
                        //     frm.refresh_field("per_gross_margin");
                        // }
                        let total_salary_cost = flt(r.message.total_cost || 0);
                        // Update custom field
                        frm.set_value("custom_total_cost", total_salary_cost);

                        // Extract existing values from form
                        let total_costing_amount = flt(frm.doc.total_costing_amount);
                        let total_purchase_cost = flt(frm.doc.total_purchase_cost);
                        let total_consumed_material_cost = flt(frm.doc.total_consumed_material_cost);
                        let total_billed_amount = flt(frm.doc.total_billed_amount);

                        // Calculate total expense (including salary cost)
                        let expense_amount = total_costing_amount + total_purchase_cost + total_consumed_material_cost + total_salary_cost;

                        // Calculate gross margin
                        let gross_margin = total_billed_amount - expense_amount;
                        let per_gross_margin = total_billed_amount
                            ? (gross_margin / total_billed_amount) * 100
                            : 0;

                        // Set updated values
                        frm.set_value("gross_margin", gross_margin);
                        frm.set_value("per_gross_margin", per_gross_margin);

                        frm.refresh_field("custom_total_cost");
                        frm.refresh_field("gross_margin");
                        frm.refresh_field("per_gross_margin")
                        frm.doc.save();                    
                    }
                }
            });
        }
    }
});
