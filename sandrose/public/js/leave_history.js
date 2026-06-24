$(document).ready(function() {
    setInterval(function() {
        if (
            frappe.get_route_str().indexOf('query-report/Leave History') !== -1 &&
            frappe.query_report &&
            frappe.query_report.page &&
            $(".dt-scrollable").length &&
            !document.getElementById("lh-print-btn")
        ) {
            $(".page-actions .btn").each(function() {
                if ($(this).text().trim() === "Print") {
                    $(this).hide();
                }
            });

            var btn = frappe.query_report.page.add_inner_button(__("Print Report"), function() {
                var visibleRows = frappe.query_report.datatable.bodyRenderer.visibleRows;
                if (!visibleRows || !visibleRows.length) { frappe.msgprint("No data to print"); return; }
                var rows = visibleRows.map(function(cells) {
                    return {
                        employee: cells[1] ? cells[1].content : "",
                        employee_name: cells[2] ? cells[2].content : "",
                        leave_type: cells[3] ? cells[3].content : "",
                        from_date: cells[4] ? cells[4].content : "",
                        to_date: cells[5] ? cells[5].content : "",
                        total_leave_days: cells[6] ? cells[6].content : "",
                        date_of_exit: cells[7] ? cells[7].content : "",
                        date_of_re_entry: cells[8] ? cells[8].content : "",
                        noof_days: cells[9] ? cells[9].content : "",
                        gratuity_days: cells[10] ? cells[10].content : ""
                    };
                });
                var employees = {}; var order = [];
                rows.forEach(function(row) {
                    if (!employees[row.employee]) { employees[row.employee] = { name: row.employee, employee_name: row.employee_name, leaves: [] }; order.push(row.employee); }
                    employees[row.employee].leaves.push(row);
                });
                var today = frappe.datetime.now_date();
                function formatDate(d) { if (!d) return ""; var parts = d.split("-"); if (parts.length !== 3) return d; return parts[2] + "/" + parts[1] + "/" + parts[0]; }
                var body = "<!DOCTYPE html><html><head><style>";
                body += "* { margin: 0; padding: 0; box-sizing: border-box; }";
                body += "body { font-family: 'Times New Roman', serif; font-size: 12px; color: #000; margin: 20px 30px; }";
                body += ".lh-header { text-align: center; margin-bottom: 8px; }";
                body += ".lh-company { font-size: 15px; font-weight: bold; letter-spacing: 0.5px; }";
                body += ".lh-title { font-size: 12px; font-weight: bold; margin: 2px 0; }";
                body += ".lh-divider { border: none; border-top: 1.5px solid #000; margin: 6px 0; }";
                body += ".lh-divider-thin { border: none; border-top: 0.5px solid #000; margin: 4px 0; }";
                body += ".lh-emp-section { margin-bottom: 14px; }";
                body += ".lh-emp-row { display: flex; gap: 30px; font-size: 12px; margin: 6px 0 3px 0; }";
                body += ".lh-emp-row span { font-weight: bold; }";
                body += "table { width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 3px; }";
                body += "th { border: 1px solid #000; padding: 3px 5px; text-align: center; font-weight: bold; }";
                body += "td { border: 1px solid #000; padding: 3px 5px; text-align: center; }";
                body += "td.lh-left { text-align: left; padding-left: 6px; }";
                body += ".lh-footer { display: flex; justify-content: space-between; font-size: 11px; margin-top: 12px; }";
                body += "</style></head><body>";
                body += "<div class='lh-header'>";
                body += "<div class='lh-company'>" + (frappe.boot.sysdefaults.company || "") + "</div>";
                body += "<div class='lh-title'>Employee Leave History As On " + formatDate(today) + "</div>";
                body += "</div><hr class='lh-divider'>";
                order.forEach(function(emp_id) {
                    var emp = employees[emp_id];
                    body += "<div class='lh-emp-section'><div class='lh-emp-row'>";
                    body += "<div>Code : <span>" + emp.name + "</span></div>";
                    body += "<div>Name : <span>" + emp.employee_name + "</span></div>";
                    body += "</div><hr class='lh-divider-thin'>";
                    body += "<table><thead><tr><th>Leave Type</th><th>From</th><th>To</th><th>Rejoin</th><th>Leave Days</th><th>Service Days</th></tr></thead><tbody>";
                    emp.leaves.forEach(function(row) {
                        var is_annual = row.leave_type === "Annual Leave";
                        var from = is_annual ? formatDate(row.date_of_exit) : formatDate(row.from_date);
                        var to = is_annual ? formatDate(row.date_of_re_entry) : formatDate(row.to_date);
                        var rejoin = is_annual ? formatDate(row.date_of_re_entry) : "";
                        var leave_days = is_annual ? (row.noof_days || "") : (row.total_leave_days || "");
                        var service_days = is_annual ? (row.gratuity_days || "") : "";
                        body += "<tr><td class='lh-left'>" + (row.leave_type || "") + "</td><td>" + from + "</td><td>" + to + "</td><td>" + rejoin + "</td><td>" + leave_days + "</td><td>" + service_days + "</td></tr>";
                    });
                    body += "</tbody></table></div>";
                });
                body += "<div class='lh-footer'><span>" + formatDate(today) + "</span><span>Page 1 of 1</span></div></body></html>";
                var w = window.open("", "_blank"); w.document.write(body); w.document.close(); w.print();
            });
            if (btn) { btn.attr("id", "lh-print-btn"); }
        }
    }, 1000);
});
