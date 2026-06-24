frappe.ui.form.on("Bulk Attendance", {
    month: function(frm) {
        if (frm.doc.month) {
            // Map month names to month numbers
            const month_map = {
                "January": 1,
                "February": 2,
                "March": 3,
                "April": 4,
                "May": 5,
                "June": 6,
                "July": 7,
                "August": 8,
                "September": 9,
                "October": 10,
                "November": 11,
                "December": 12
            };

            let year = frappe.datetime.str_to_obj(frappe.datetime.nowdate()).getFullYear();
            let month_number = month_map[frm.doc.month];

            // First date of selected month
            let first_day = frappe.datetime.obj_to_str(new Date(year, month_number - 1, 1));

            // Last date of selected month
            let last_day = frappe.datetime.obj_to_str(new Date(year, month_number, 0));

            frm.set_value("from", first_day);
            frm.set_value("to", last_day);
        }
    },    

    category: function(frm) {
        if (frm.doc.category) {
            category = frm.doc.category;
            frm.set_query('employee', function() {
                return {
                    filters: {
                        grade: category
                    }
                };
            });
        }
    },

    to: function(frm) {
        if (frm.doc.from && frm.doc.to) {
            frm.clear_table('attendance_details');

            let from_date = frm.doc.from;
            let to_date = frm.doc.to;
            let category = frm.doc.category;

            // Call server method to get employees without attendance
            frappe.call({
                method: "sandrose.sandrose.doctype.bulk_attendance.bulk_attendance.get_available_employees",
                args: {
                    from_date: from_date,
                    to_date: to_date,
                    category: category
                },
                callback: function(r) {
                    if (r.message) {
                        let employee_ids = r.message.map(emp => emp.employee);

                        // Filter employee field to only those not yet marked
                        frm.set_query("employee", function() {
                            return {
                                filters: {
                                    name: ["in", employee_ids]
                                }
                            };
                        });

                        // Optionally store the list for later use (like export)
                        // let row = frm.add_child('unmarked_employee');
                        // row.unmarked_employee = employee_ids;
                        // row.name1 = r.message.map(emp => emp.employee_name);
                    }
                    frm.refresh_field('unmarked_employee');
                }
            });

            let currentDate = frappe.datetime.str_to_obj(frm.doc.from);
            let endDate = frappe.datetime.str_to_obj(frm.doc.to);

            while (currentDate <= endDate) {
                let row = frm.add_child('attendance_details');
                row.day = frappe.datetime.obj_to_str(currentDate);
                row.week = currentDate.toLocaleDateString('en-US', { weekday: 'long' });

                // Increment date by one day
                currentDate.setDate(currentDate.getDate() + 1);
            }

            frm.refresh_field('attendance_details');
        }
    },
    employee(frm) {
        if (frm.doc.from && frm.doc.to && frm.doc.employee) {
            frappe.call({
                method: "frappe.client.get_list",
                args: {
                    doctype: "Attendance",
                    fields: ["employee", "attendance_date"],
                    filters: {
                        employee: frm.doc.employee,
                        attendance_date: ["between", [frm.doc.from, frm.doc.to]]
                    },
                    limit: 1000
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        let marked_dates = r.message.map(att => att.attendance_date);

                        frm.doc.attendance_details = (frm.doc.attendance_details || []).filter(row => {
                            return !marked_dates.some(marked =>
                                frappe.datetime.str_to_obj(marked).toDateString() === frappe.datetime.str_to_obj(row.day).toDateString()
                            );
                        });

                        frm.refresh_field("attendance_details");
                        frappe.msgprint(__("Marked attendance dates removed from Attendance Details."));
                    }
                }
            });
        }
    },

    refresh: function(frm) {
        frm.add_custom_button(__('Export Unmarked Employees'), function () {
            if (frm.doc.from && frm.doc.to && frm.doc.category) {
                frappe.call({
                    method: "sandrose.sandrose.doctype.bulk_attendance.bulk_attendance.get_available_employees",
                    args: {
                        from_date: frm.doc.from,
                        to_date: frm.doc.to,
                        category: frm.doc.category
                    },
                    callback: function (r) {
                        if (r.message && r.message.length > 0) {
                            download_csv(r.message, "Unmarked_Employees.csv");
                        } else {
                            frappe.msgprint("No unmarked employees found.");
                        }
                    }
                });
            } else {
                frappe.msgprint("Please select Category, From Date, and To Date first.");
            }
        });
        if (frm.doc.docstatus==1)
            frm.add_custom_button(__('New Bulk Attendance'), function() {
                frappe.route_options = {
                    category: frm.doc.category,
                    from: frm.doc.from,
                    to: frm.doc.to
                };
                frappe.new_doc('Bulk Attendance');
            });
    },
    //   exclude_holidays: function(frm) {
    //     if (frm.doc.exclude_holidays && frm.doc.from && frm.doc.to) {
    //         frappe.call({
    //             method: "erpnext.hr.doctype.holiday_list.holiday_list.get_holidays",
    //             args: {
    //                 from_date: frm.doc.from,
    //                 to_date: frm.doc.to,
    //                 holiday_list: null,
    //                 company: frm.doc.company
    //             },
    //             callback: function(res) {
    //                 let holiday_dates = (res.message || []).map(h => h.holiday_date);

    //                 let updated_rows = frm.doc.attendance_details.filter(row => {
    //                     return !holiday_dates.includes(row.day);
    //                 });

    //                 frm.doc.attendance_details = updated_rows;
    //                 frm.refresh_field("attendance_details");
    //                 frappe.msgprint(__("Holiday dates removed from Attendance Details."));
    //             }
    //         });
    //     }
    // }
    exclude_holidays: function(frm) {
        if (frm.doc.exclude_holidays && frm.doc.from && frm.doc.to) {
            frappe.call({
                method: "sandrose.sandrose.doctype.bulk_attendance.bulk_attendance.get_leave_dates",
                args: {
                    from_date: frm.doc.from,
                    to_date: frm.doc.to,
                    employee: frm.doc.employee // optional
                },
                callback: function(res) {
                    let leave_dates = (res.message || []).map(l => l.leave_date);
    
                    // Remove rows that match leave dates
                    frm.doc.attendance_details = frm.doc.attendance_details.filter(row => {
                        return !leave_dates.includes(row.day);
                    });
    
                    frm.refresh_field("attendance_details");
                    frappe.msgprint(__("Leave dates removed from Attendance Details."));
                }
    
            });
        }
    }
    
});

frappe.ui.form.on("Bulk Attendance Details", {
    is_contract: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.is_contract) {
            row.status = "Absent";
            frm.refresh_field("attendance_details");
        }
    },
});

// function download_csv(data, filename) {
//     let csv = "Employee ID,Employee Name\n";
//     data.forEach(function (row) {
//         csv += `"${row.employee}","${row.employee_name}"\n`;
//     });

//     let hiddenElement = document.createElement("a");
//     hiddenElement.href = "data:text/csv;charset=utf-8," + encodeURI(csv);
//     hiddenElement.target = "_blank";
//     hiddenElement.download = filename;
//     hiddenElement.click();
// }
function download_csv(data, filename) {
    let csv = "Employee ID,Employee Name,Leave Type\n";   // added Leave Type column
    data.forEach(function (row) {
        csv += `"${row.employee}","${row.employee_name}","${row.leave_type || ""}"\n`;
    });

    let hiddenElement = document.createElement("a");
    hiddenElement.href = "data:text/csv;charset=utf-8," + encodeURI(csv);
    hiddenElement.target = "_blank";
    hiddenElement.download = filename;
    hiddenElement.click();
}

frappe.ui.form.on("Bulk Attendance", {
    refresh(frm) {
        $("button:contains('Select All')").off('click').on('click', () => {
            (frm.doc.attendance_details || []).forEach(row => {
                row.custom_project = 1;
                row.job = frm.doc.project || "";
            });
            frm.refresh_field("attendance_details");
        });

        $("button:contains('Unselect All')").off('click').on('click', () => {
            (frm.doc.attendance_details || []).forEach(row => {
                row.custom_project = 0;
                row.job = "";
            });
            frm.refresh_field("attendance_details");
        });
    }
});

frappe.ui.form.on("Bulk Attendance Details", {
    custom_project(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.custom_project) {
            row.job = frm.doc.project || "";
        } else {
            row.job = "";
        }
        frm.refresh_field("attendance_details");
    }
});
frappe.ui.form.on("Bulk Attendance", {
    
});