app_name = "sandrose"
app_title = "Sandrose"
app_publisher = "Sandrose"
app_description = "Sandrose"
app_email = "sandrose@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "sandrose",
# 		"logo": "/assets/sandrose/logo.png",
# 		"title": "Sandrose",
# 		"route": "/sandrose",
# 		"has_permission": "sandrose.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------
fixtures = [
    {
        "doctype":"Custom Field",
        "filters":[
            [
                "name",
                "in",
                [
                    "Retention Bonus-custom_project",
                    "Retention Bonus-custom_cost_center",
                    "Attendance-custom_project",
                    "Attendance-custom_cost_center",
                    "Employee-custom_first_day_of_joining",
                    "Employee-custom_section_break_f7wph",
                    "Employee-custom_vacation_details",
                    "Employee-custom_rejoining",
                    "Employee-custom_flight_rate",
                    "Employee-custom_gratuity_rate",
                    "Attendance-custom_overtime_hours",
                    "Employee-custom_overtime_rate",
                    "Attendance-custom_overtime_rate",
                    "Attendance-custom_overtime_amount",
                    "Attendance-custom_salary_amount",
                    "Project-custom_total_cost",
                    "Expense Entry-custom_employee_name",
                    "Expense Entry-custom_license_plate",
                    "Expense Entry-custom_vehicle_log_id",
                    "Expense Entry-custom_journal_entry_id",
                    "Purchase Order-custom_section_break_8w3q6",
                    "Purchase Order-custom_item_transaction_details",
                    "Sales Invoice-custom_section_break_dbm3p",
                    "Sales Invoice-custom_item_transaction_details",
                    "Quotation-custom_section_break_zqvlz",
                    "Quotation-custom_item_transaction_details",
                    "Employee-custom_labour_card_designation"
                ]
            ]    
        ]
    }]


# include js, css files in header of desk.html
# app_include_css = "/assets/sandrose/css/sandrose.css"
# app_include_js = "/assets/sandrose/js/sandrose.js"

# include js, css files in header of web template
# web_include_css = "/assets/sandrose/css/sandrose.css"
# web_include_js = "/assets/sandrose/js/sandrose.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "sandrose/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
    "Salary Slip" : "public/js/salary_slip.js",
    "Employee" : "public/js/employee.js",
    "Payroll Entry" : "public/js/payroll_entry.js",
    "Project" : "public/js/project.js",
    "Vehicle Log" : "public/js/vehicle_log.js",
    "Purchase Order" : "public/js/purchase_order.js",
    "Payment Entry" : "public/js/payment_entry.js",
    "Purchase Order": "public/js/item_transaction.js",
    "Sales Invoice": "public/js/item_transaction.js",
    "Quotation": "public/js/item_transaction.js",
    }

# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "sandrose/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "sandrose.utils.jinja_methods",
# 	"filters": "sandrose.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "sandrose.install.before_install"
# after_install = "sandrose.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "sandrose.uninstall.before_uninstall"
# after_uninstall = "sandrose.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "sandrose.utils.before_app_install"
# after_app_install = "sandrose.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "sandrose.utils.before_app_uninstall"
# after_app_uninstall = "sandrose.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "sandrose.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Retention Bonus":"sandrose.sandrose.custom_script.retention_bonus.CustomRetentionBonus"
}
override_report = {
	"Profit and Loss Statement": "sandrose.sandrose.report.p_and_l_statement.p_and_l_statement"
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Retention Bonus": {
        "on_submit": "sandrose.sandrose.custom_script.retention_bonus.on_submit"
    },
    "Salary Slip": {
        "before_save": "sandrose.sandrose.custom_script.salary_slip.before_save"
    },
    "Employee": {
        "on_update": "sandrose.sandrose.custom_script.employee.update_vacation_details",
        "validate": "sandrose.sandrose.custom_script.employee.set_first_day_of_joining"
    },
    "Salary Structure Assignment": {
        "after_insert": "sandrose.sandrose.custom_script.salary_structure_assignment.calculate_gratuity_on_assignment"
    },
    "Attendance": {
        "before_submit": "sandrose.sandrose.custom_script.attendance.update_attendance_fields"
    },
    "Expense Entry": {
        "on_submit": "sandrose.sandrose.custom_script.expense_entry.link_journal_entry_to_expense_entry",
        "on_cancel": "sandrose.sandrose.custom_script.expense_entry.cancel_linked_journal_entry",
        "validate": "sandrose.sandrose.custom_script.expense_entry.calculate_totals"
    }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"sandrose.tasks.all"
# 	],
# 	"daily": [
# 		"sandrose.tasks.daily"
# 	],
# 	"hourly": [
# 		"sandrose.tasks.hourly"
# 	],
# 	"weekly": [
# 		"sandrose.tasks.weekly"
# 	],
# 	"monthly": [
# 		"sandrose.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "sandrose.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "sandrose.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "sandrose.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["sandrose.utils.before_request"]
# after_request = ["sandrose.utils.after_request"]

# Job Events
# ----------
# before_job = ["sandrose.utils.before_job"]
# after_job = ["sandrose.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"sandrose.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
fixtures = [
    {"dt": "Custom Field", "filters": [["dt", "=", "Employee"]]},
    {"dt": "DocType", "filters": [["name", "in", ["Preparation Record", "Preparation List"]]]},
    {"dt": "Server Script", "filters": [["name", "=", "Push Preparation to Employee Trackers"]]},
]
