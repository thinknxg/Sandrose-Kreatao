frappe.query_reports["Employees On Leave As On Date"] = {
filters: [
{
fieldname: "as_on_date",
label: __("As On Date"),
fieldtype: "Date",
default: frappe.datetime.get_today(),
reqd: 1,
},
{
fieldname: "company",
label: __("Company"),
fieldtype: "Link",
options: "Company",
},
],

onload: function (report) {
report.page.add_inner_button(__("Print"), function () {
let filters = report.get_values();
if (!filters) return;

let data = report.data;
if (!data || data.length === 0) {
frappe.msgprint(__("No data to print."));
return;
}

let company = "SANDROSE TRADING LLC";
let as_on_date = frappe.datetime.str_to_user(filters.as_on_date);
let print_date = frappe.datetime.str_to_user(frappe.datetime.get_today());

let grouped = {};
data.forEach((row) => {
let dept = row.department || "\u2014";
let leave_type = row.leave_type || "\u2014";
if (!grouped[dept]) grouped[dept] = {};
if (!grouped[dept][leave_type]) grouped[dept][leave_type] = [];
grouped[dept][leave_type].push(row);
});

let rows_html = "";
Object.keys(grouped).forEach((dept) => {
rows_html += "<tr><td colspan='9' style='font-weight:bold; padding: 6px 4px 2px 4px; font-size: 11pt;'>Department : " + dept + "</td></tr>";

Object.keys(grouped[dept]).forEach((leave_type) => {
rows_html += "<tr><td colspan='9' style='padding: 2px 4px 2px 20px; font-style: italic; font-size: 10.5pt; font-weight: 600;'>" + leave_type + "</td></tr>";

grouped[dept][leave_type].forEach((row) => {
rows_html += "<tr>"
+ "<td>" + (row.employee || "") + "</td>"
+ "<td>" + (row.employee_name || "") + "</td>"
+ "<td>" + (row.designation || "") + "</td>"
+ "<td>" + (row.employment_type || row.category || "") + "</td>"
+ "<td>" + (row.from_date ? frappe.datetime.str_to_user(row.from_date) : "") + "</td>"
+ "<td>" + (row.to_date ? frappe.datetime.str_to_user(row.to_date) : "") + "</td>"
+ "<td>" + (row.rejoined || "") + "</td>"
+ "<td style='text-align:center;'>" + (row.allowed || "") + "</td>"
+ "<td style='text-align:center;'>" + (row.excess || "") + "</td>"
+ "</tr>";
});
});
});

let html = "<!DOCTYPE html><html><head><meta charset='UTF-8'>"
+ "<title>Employees On Leave - " + company + "</title>"
+ "<style>"
+ "* { margin: 0; padding: 0; box-sizing: border-box; }"
+ "body { font-family: Arial, sans-serif; font-size: 10pt; color: #000; background: #fff; }"
+ ".page-wrapper { width: 100%; max-width: 900px; margin: 0 auto; padding: 24px 32px; }"
+ ".report-header { text-align: center; margin-bottom: 10px; border-bottom: 2px solid #000; padding-bottom: 8px; }"
+ ".company-name { font-size: 16pt; font-weight: bold; letter-spacing: 0.5px; }"
+ ".report-title { font-size: 11pt; font-weight: bold; margin-top: 2px; }"
+ ".meta-row { display: flex; justify-content: space-between; margin: 6px 0 10px 0; font-size: 9.5pt; }"
+ "table { width: 100%; border-collapse: collapse; font-size: 9.5pt; }"
+ "thead tr th { border-top: 1.5px solid #000; border-bottom: 1.5px solid #000; padding: 5px 4px; text-align: left; font-weight: bold; white-space: nowrap; }"
+ "tbody tr td { padding: 3px 4px; vertical-align: top; white-space: nowrap; }"
+ "tbody tr:last-child td { border-bottom: 1.5px solid #000; }"
+ "@media print { .no-print { display: none !important; } @page { size: landscape; margin: 10mm 12mm; } }"
+ "</style></head><body>"
+ "<div class='page-wrapper'>"
+ "<div class='no-print' style='text-align:right; margin-bottom:12px;'>"
+ "<button onclick='window.print()' style='padding:6px 18px; font-size:10pt; cursor:pointer; background:#171717; color:#fff; border:none; border-radius:3px;'>Print</button>"
+ "</div>"
+ "<div class='report-header'>"
+ "<div class='company-name'>" + company.toUpperCase() + "</div>"
+ "<div class='report-title'>Employees On Leave As On " + as_on_date + "</div>"
+ "</div>"
+ "<div class='meta-row'><span>" + print_date + "</span><span>Page 1 of 1</span></div>"
+ "<table><thead><tr>"
+ "<th>Code</th><th>Name</th><th>Designation</th><th>Category</th>"
+ "<th>Leave From</th><th>Leave To</th><th>Rejoined</th><th>Allowed</th><th>Excess</th>"
+ "</tr></thead><tbody>" + rows_html + "</tbody></table>"
+ "</div></body></html>";

let w = window.open("", "_blank", "width=960,height=700");
w.document.write(html);
w.document.close();
});
},
};
