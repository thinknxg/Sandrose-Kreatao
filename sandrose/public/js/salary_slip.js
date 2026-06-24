frappe.ui.form.on('Salary Slip', {
    refresh: function(frm) {
        console.log("Refresh triggered for Salary Slip");
        frm.add_custom_button(__('Get Flight Charge and Gratuity'), function() {
            fetch_flight_and_gratuity(frm);
        });
    }
});
function fetch_flight_and_gratuity(frm) {
    let start_date = frm.doc.start_date;
    let end_date = frm.doc.end_date;
    let employee = frm.doc.employee;

    frappe.call({
        method: 'sandrose.sandrose.custom_script.salary_slip.get_flight_and_gratuity',
        args: {
            employee: employee,
            start_date: start_date,
            end_date: end_date
        },
        callback: function(res) {
            let flight_charge = res.message.flight_charges || 0;
            let gratuity = res.message.gratuity_amount || 0;

            let flight_charge_exists = frm.doc.earnings.some(e => e.salary_component === 'Flight Charge');
            let gratuity_exists = frm.doc.earnings.some(e => e.salary_component === 'Gratuity');

            if (flight_charge_exists) {
                frm.doc.earnings.forEach(e => {
                    if (e.salary_component === 'Flight Charge') {
                        e.amount = flight_charge;
                    }
                });
            } else {
                frm.add_child('earnings', {
                    salary_component: 'Flight Charge',
                    amount: flight_charge
                });
            }

            if (gratuity_exists) {
                frm.doc.earnings.forEach(e => {
                    if (e.salary_component === 'Gratuity') {
                        e.amount = gratuity;
                    }
                });
            } else {
                frm.add_child('earnings', {
                    salary_component: 'Gratuity',
                    amount: gratuity
                });
            }

            frm.refresh_field('earnings');
        }
    });
}

frappe.ui.form.on('Salary Slip', {
    refresh: function(frm) {
        frm.add_custom_button(__('Get Overtime'), function() {
            calculate_overtime(frm);
        });
    }
});

function calculate_overtime(frm) {
    console.log("button clicked")
    let start_date = frm.doc.start_date;
    let end_date = frm.doc.end_date;
    let employee = frm.doc.employee;

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Attendance',
            filters: {
                employee: employee,
                attendance_date: ['between', [start_date, end_date]]
            },
            fields: ['custom_overtime_hours']
        },
        callback: function(response) {
            let attendances = response.message || [];
            let total_overtime_hours = attendances.reduce((sum, att) => sum + (att.custom_overtime_hours || 0), 0);
            let overtime_exists = frm.doc.earnings.some(e => e.salary_component === 'Overtime');

            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Employee',
                    filters: { name: employee },
                    fieldname: 'custom_overtime_rate'
                },
                callback: function(res) {
                    let overtime_rate = res.message.custom_overtime_rate || 0;
                    console.log("overtime rate",overtime_rate);
                    let total_overtime_amount = total_overtime_hours * overtime_rate;
                    console.log("overtime hour",total_overtime_hours);
                    console.log("overtime amount",total_overtime_amount);



                    // if (total_overtime_amount > 0) {
                    //     frm.add_child('earnings', {
                    //         salary_component: 'Overtime',
                    //         amount: total_overtime_amount
                    //     });

                    //     frm.refresh_field('earnings');
                    // }
                    if (overtime_exists) {
                        frm.doc.earnings.forEach(e => {
                            if (e.salary_component === 'Overtime') {
                                e.amount = total_overtime_amount;
                            }
                        });
                    } else {
                        frm.add_child('earnings', {
                            salary_component: 'Overtime',
                            amount: total_overtime_amount
                        });
                    }
        
                    frm.refresh_field('earnings');
                }
            });
        }
    });
}
