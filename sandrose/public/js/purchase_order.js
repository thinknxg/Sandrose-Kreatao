frappe.ui.form.on("Purchase Order", {
    project(frm) {
        update_items(frm);
    },
    cost_center(frm) {
        update_items(frm);
    },
    before_save(frm) {
        update_items(frm);
    }
});

function update_items(frm) {
    const project = frm.doc.project;
    const cost_center = frm.doc.cost_center;

    if (!project && !cost_center) return;

    frm.doc.items.forEach(row => {
        if (project) {
            frappe.model.set_value(row.doctype, row.name, "project", project);
        }
        if (cost_center) {
            frappe.model.set_value(row.doctype, row.name, "cost_center", cost_center);
        }
    });

    frm.refresh_field("items");
}
