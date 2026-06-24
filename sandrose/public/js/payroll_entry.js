frappe.ui.form.on('Payroll Entry', {
    refresh: function(frm) {
        frm.add_custom_button(__('Get Overtime'), function() {
            get_overtime_for_all_salary_slips(frm);
        });
        frm.add_custom_button(__('Get Flight Charge and Gratuity'), function() {
            get_flight_charge_and_gratuity_for_all_salary_slips(frm);
        });
    }
});

function get_overtime_for_all_salary_slips(frm) {
    let payroll_entry = frm.doc.name;
    
    // Create minimal progress dialog (no buttons)
    let dialog = new frappe.ui.Dialog({
        title: __('Calculating Overtime'),
        indicator: 'green',
        size: 'small',
        minimizable: true
    });
    
    // Remove all dialog buttons
    dialog.$wrapper.find('.modal-footer').remove();
    
    // Add only progress bar
    dialog.$body.append(`
        <div class="progress" style="height: 20px; margin: 15px 0;">
            <div class="progress-bar" role="progressbar" style="width: 0%; transition: width 0.3s ease;">
                0%
            </div>
        </div>
        <div class="text-center status-text" style="font-size: 12px;">Initializing...</div>
    `);
    
    dialog.show();

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Salary Slip',
            filters: {
                payroll_entry: payroll_entry,
                docstatus: 0
            },
            fields: ['name', 'employee', 'start_date', 'end_date'],
            limit_page_length: 1000
        },
        callback: async function(response) {
            let salary_slips = response.message;
            let total = salary_slips.length;
            
            if (total === 0) {
                dialog.hide();
                frappe.msgprint(__('No salary slips found for processing'));
                return;
            }
            
            // Process with UI updates
            for (let i = 0; i < salary_slips.length; i++) {
                let slip = salary_slips[i];
                let percent = Math.round(((i + 1) / total) * 100);
                
                // Update progress
                dialog.$wrapper.find('.progress-bar')
                    .css('width', percent + '%')
                    .text(percent + '%');
                dialog.$wrapper.find('.status-text').text(`Processing ${i + 1} of ${total}`);
                
                // Tiny delay to keep UI responsive
                await new Promise(resolve => setTimeout(resolve, 0));
                
                try {
                    await calculate_overtime(slip);
                } catch (error) {
                    console.error(`Error processing ${slip.name}:`, error);
                }
            }
            
            // Close dialog and refresh when done
            dialog.hide();
            frm.reload_doc();
            frappe.show_alert(__('Overtime calculated for {0} salary slips', [total]), 5);
        },
        error: function(error) {
            dialog.hide();
            frappe.msgprint({
                title: __('Error'),
                indicator: 'red',
                message: __('Failed to fetch salary slips: {0}', [error.message])
            });
        }
    });
}

function calculate_overtime(slip) {
    return new Promise(function(resolve, reject) {
        let { start_date, end_date, employee, name: salary_slip_name } = slip;

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Attendance',
                filters: {
                    employee: employee,
                    attendance_date: ['between', [start_date, end_date]],
                    docstatus: 1
                },
                fields: ['name', 'custom_overtime_hours', 'custom_overtime_amount'],
                limit_page_length: 2000
            },
            callback: function(response) {
                let attendances = response.message || [];
                let total_overtime = 0;

                attendances.forEach(attendance => {
                    if (attendance.custom_overtime_hours > 0) {
                        const overtime_amount = flt(attendance.custom_overtime_amount || 0);
                        console.log(`Included Attendance: ${attendance.name}, Hours: ${attendance.custom_overtime_hours}, Amount: ${overtime_amount}`);
                        total_overtime += overtime_amount;
                    } else {
                        console.log(`Skipped Attendance (0 hours): ${attendance.name}`);
                    }
                });

                frappe.call({
                    method: 'frappe.client.get',
                    args: {
                        doctype: 'Salary Slip',
                        name: salary_slip_name
                    },
                    callback: function(r) {
                        let salary_slip = r.message;
                        let earnings = salary_slip.earnings || [];

                        let overtime_entry = earnings.find(e => e.salary_component === 'Overtime');
                        if (overtime_entry) {
                            overtime_entry.amount = total_overtime;
                        } else {
                            earnings.push({
                                salary_component: 'Overtime',
                                amount: total_overtime
                            });
                        }

                        frappe.call({
                            method: 'frappe.client.set_value',
                            args: {
                                doctype: 'Salary Slip',
                                name: salary_slip_name,
                                fieldname: {
                                    earnings: earnings
                                }
                            },
                            callback: function() {
                                console.log(`Total Overtime Amount Set: ${total_overtime}`);
                                resolve();
                            },
                            error: function(err) {
                                reject(err);
                            }
                        });
                    },
                    error: function(err) {
                        reject(err);
                    }
                });
            },
            error: function(err) {
                reject(err);
            }
        });
    });
}


function get_flight_charge_and_gratuity_for_all_salary_slips(frm) {
    let payroll_entry = frm.doc.name;

    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Salary Slip',
            filters: {
                payroll_entry: payroll_entry,
                docstatus: 0
            },
            fields: ['name', 'employee', 'start_date', 'end_date'],
            limit_page_length: 1000
        },
        callback: function(response) {
            let salary_slips = response.message;

            let promises = salary_slips.map(function(slip) {
                return calculate_flight_charge_and_gratuity(slip);
            });

            Promise.all(promises).then(function() {
                frappe.msgprint(__('Flight charge and gratuity Amount have been updated for all salary slips.'));
                frm.reload_doc();
            });
        }
    });
}

function calculate_flight_charge_and_gratuity(slip) {
    return new Promise(function(resolve, reject) {
        let { employee, start_date, end_date, name: salary_slip_name } = slip;

        // Step 1: Call your whitelisted server method
        frappe.call({
            method: 'sandrose.sandrose.custom_script.payroll_entry.get_flight_and_gratuity',
            args: {
                employee: employee,
                start_date: start_date,
                end_date: end_date
            },
            callback: function(response) {
                let data = response.message || {};
                let flight_charge = data.flight_charges || 0;
                let gratuity = data.gratuity_amount || 0;

                // Step 2: Fetch the salary slip to update earnings
                frappe.call({
                    method: 'frappe.client.get',
                    args: {
                        doctype: 'Salary Slip',
                        name: salary_slip_name
                    },
                    callback: function(r) {
                        let salary_slip = r.message;
                        let earnings = salary_slip.earnings || [];
                        let deductions = salary_slip.deductions || [];

                        // Add or update Flight Charge
                        let flight_entry = earnings.find(e => e.salary_component === 'Flight Charge');
                        if (flight_entry) {
                            flight_entry.amount = flight_charge;
                        } else if (flight_charge > 0) {
                            earnings.push({
                                salary_component: 'Flight Charge',
                                amount: flight_charge
                            });
                        }

                        // Add or update Gratuity
                        let gratuity_entry = earnings.find(e => e.salary_component === 'Gratuity');
                        if (gratuity_entry) {
                            gratuity_entry.amount = gratuity;
                        } else if (gratuity > 0) {
                            earnings.push({
                                salary_component: 'Gratuity',
                                amount: gratuity
                            });
                        }

                        // Step 3: Update salary slip with new earnings
                        frappe.call({
                            method: 'frappe.client.set_value',
                            args: {
                                doctype: 'Salary Slip',
                                name: salary_slip_name,
                                fieldname: {
                                    earnings: earnings,
                                    deductions: deductions
                                }
                            },
                            callback: function() {
                                resolve();  // Done
                            }
                        });
                    }
                });
            }
        });
    });
}



