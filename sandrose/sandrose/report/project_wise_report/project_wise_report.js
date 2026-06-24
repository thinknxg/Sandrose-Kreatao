// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["Project wise Report"] = {
	"filters": [
		{
            "fieldname": "project",
            "label": __("Project"),
            "fieldtype": "Link",
            "options": "Project",
            "reqd": 1 // Required field
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 1 // Required field
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 1 // Required field
        },
        // {
        //     "fieldname": "cost_center",
        //     "label": "Cost Center",
        //     "fieldtype": "Link",
        //     "options": "Cost Center"
        // },

         {
            "fieldname": "grade",
            "label": __("Grade"),
            "fieldtype": "Link",
            "options": "Employee Grade",
            "reqd": 0 
        },
    ],

    formatter: function (value, row, column, data, default_formatter) {

        value = default_formatter(value, row, column, data);

        //Make TOTAL bold
        if (data && data.project === "TOTAL") {
            value = `<b>${value}</b>`;
        }

        return value;
    }
    

	
};



