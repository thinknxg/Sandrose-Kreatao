// frappe.ui.form.on('Payment Entry', {
//     onload: function(frm) {
//         // Add click event to child table rows
//         frm.fields_dict.references.grid.wrapper.on('click', '.grid-row', function() {
//             let row_idx = $(this).attr('data-idx');
//             let row = frm.doc.references.find(r => r.idx == row_idx);
//             allocate_row(frm, row);
//         });
//     }
// });

// // Function to allocate outstanding to allocated column
// function allocate_row(frm, row) {
//     if (!row) return;

//     let total_allocated = frm.doc.references.reduce((sum, r) => sum + flt(r.allocated_amount), 0);
//     let remaining_amount = flt(frm.doc.paid_amount) - total_allocated;

//     if (remaining_amount <= 0) {
//         frappe.msgprint(__('Paid Amount fully allocated'));
//         return;
//     }

//     // Allocate either the full outstanding or remaining amount, whichever is smaller
//     let allocation = Math.min(flt(row.outstanding_amount), remaining_amount);
//     row.allocated_amount = allocation;

//     // Refresh child table and totals
//     frm.refresh_field('references');
//     update_totals(frm);
// }

// function update_totals(frm) {
//     let total_allocated = frm.doc.references.reduce((sum, r) => sum + flt(r.allocated_amount), 0);
//     frm.set_value('total_allocated_amount', total_allocated);
//     frm.set_value('unallocated_amount', flt(frm.doc.paid_amount) - total_allocated);
//     frm.set_value('difference_amount', flt(frm.doc.paid_amount) - total_allocated);
//     frm.refresh_field('total_allocated_amount');
//     frm.refresh_field('unallocated_amount');
//     frm.refresh_field('difference_amount');
// }


frappe.ui.form.on('Payment Entry', {
    refresh(frm) {

        // Ensure references grid exists
        if (!frm.fields_dict.references) return;

        // Remove old handlers to avoid duplicate firing
        frm.fields_dict.references.grid.wrapper
            .off('click.allocate_row')

            // Attach click handler to grid rows
            .on('click.allocate_row', '.grid-row', function () {

                let idx = $(this).attr('data-idx');
                if (!idx) return;

                // Find the clicked row
                let row = frm.doc.references.find(r => r.idx == idx);
                if (!row) return;

                let paid_amount = flt(frm.doc.paid_amount || 0);

                // Calculate total allocated so far
                let total_allocated = frm.doc.references.reduce(
                    (sum, r) => sum + flt(r.allocated_amount),
                    0
                );

                let remaining = paid_amount - total_allocated;

                // Stop if nothing left to allocate
                if (remaining <= 0) {
                    frappe.msgprint(__('Paid Amount fully allocated'));
                    return;
                }

                // Allocate min(outstanding, remaining)
                let allocation = Math.min(
                    flt(row.outstanding_amount),
                    remaining
                );

                //use frappe.model.set_value
                frappe.model.set_value(
                    row.doctype,
                    row.name,
                    'allocated_amount',
                    allocation
                );
            });
    }
});
