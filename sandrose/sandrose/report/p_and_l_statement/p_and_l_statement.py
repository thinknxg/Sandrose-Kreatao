# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.report.financial_statements import (
	get_columns,
	get_data,
	get_filtered_list_for_consolidated_report,
	get_period_list,
)


def execute(filters=None):
	period_list = get_period_list(
		filters.from_fiscal_year,
		filters.to_fiscal_year,
		filters.period_start_date,
		filters.period_end_date,
		filters.filter_based_on,
		filters.periodicity,
		company=filters.company,
	)

	income = get_data(
		filters.company,
		"Income",
		"Credit",
		period_list,
		filters=filters,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
	)

	# expense = get_data(
	# 	filters.company,
	# 	"Expense",
	# 	"Debit",
	# 	period_list,
	# 	filters=filters,
	# 	accumulated_values=filters.accumulated_values,
	# 	ignore_closing_entries=True,
	# 	ignore_accumulated_values_for_fy=True,
	# )
		# Get standard expense data
	expense = get_data(
		filters.company,
		"Expense",
		"Debit",
		period_list,
		filters=filters,
		accumulated_values=filters.accumulated_values,
		ignore_closing_entries=True,
		ignore_accumulated_values_for_fy=True,
	)

	# 👇 Inject salary if project is selected
	if filters.get("project"):
		from sandrose.sandrose.custom_script.project import get_project_salary_data

		salary_data = get_project_salary_data(filters["project"])
		salary_total = salary_data.get("total_cost", 0)

		if salary_total:
			project_salary_row = {
				"account": "Project Salary - STL",
				"account_name": "Project Salary - STL",
				"parent_account": "5000 - Expenses - STL",
				"is_group": 0,
				"indent": 1,
				"report_type": "Profit and Loss",
				"root_type": "Expense",
				"account_type": "Expense Account",
				"currency": filters.presentation_currency or frappe.get_cached_value("Company", filters.company, "default_currency"),
			}

			# Spread salary over periods (uniformly or in total column)
			for period in period_list:
				key = period.key
				project_salary_row[key] = salary_total if len(period_list) == 1 else 0

			# Add total if needed
			project_salary_row["total"] = salary_total
			# expense.append(project_salary_row)
			expense.insert(-2, project_salary_row)  # instead of expense.append
			# After inserting salary row
			total_row = expense[-2]  # The existing total row
			for period in period_list:
				key = period.key
				total_row[key] = total_row.get(key, 0) + project_salary_row.get(key, 0)
			total_row["total"] = total_row.get("total", 0) + project_salary_row.get("total", 0)




	net_profit_loss = get_net_profit_loss(
		income, expense, period_list, filters.company, filters.presentation_currency
	)

	data = []
	data.extend(income or [])
	data.extend(expense or [])
	if net_profit_loss:
		data.append(net_profit_loss)

	columns = get_columns(filters.periodicity, period_list, filters.accumulated_values, filters.company)

	currency = filters.presentation_currency or frappe.get_cached_value(
		"Company", filters.company, "default_currency"
	)
	chart = get_chart_data(filters, columns, income, expense, net_profit_loss, currency)

	report_summary, primitive_summary = get_report_summary(
		period_list, filters.periodicity, income, expense, net_profit_loss, currency, filters
	)

	return columns, data, None, chart, report_summary, primitive_summary


def get_report_summary(
	period_list, periodicity, income, expense, net_profit_loss, currency, filters, consolidated=False
):
	net_income, net_expense, net_profit = 0.0, 0.0, 0.0

	# from consolidated financial statement
	if filters.get("accumulated_in_group_company"):
		period_list = get_filtered_list_for_consolidated_report(filters, period_list)

	if filters.accumulated_values:
		key = period_list[-1].key
		# if income and len(income) >= 2:
		# 	net_income = income[-2].get(key, 0)
		# if expense and len(expense) >= 2:
		# 	net_expense = expense[-2].get(key, 0)
		if income:
			net_income = sum(row.get(key, 0) for row in income if isinstance(row, dict) and key in row)
		if expense:
			net_expense = sum(row.get(key, 0) for row in expense if isinstance(row, dict) and key in row)

		if net_profit_loss:
			net_profit = net_profit_loss.get(key, 0)
	else:
		for period in period_list:
			key = period if consolidated else period.key
			if income and len(income) >= 2:
				net_income += income[-2].get(key, 0)
			if expense and len(expense) >= 2:
				net_expense += expense[-2].get(key, 0)
			# if income:
			# 	net_income += sum(row.get(key, 0) for row in income if isinstance(row, dict) and key in row)
			# if expense:
			# 	net_expense += sum(row.get(key, 0) for row in expense if isinstance(row, dict) and key in row)

			if net_profit_loss:
				net_profit += net_profit_loss.get(key, 0)


	if len(period_list) == 1 and periodicity == "Yearly":
		profit_label = _("Profit This Year")
		income_label = _("Total Income This Year")
		expense_label = _("Total Expense This Year")
	else:
		profit_label = _("Net Profit")
		income_label = _("Total Income")
		expense_label = _("Total Expense")

	return [
		{"value": net_income, "label": income_label, "datatype": "Currency", "currency": currency},
		{"type": "separator", "value": "-"},
		{"value": net_expense, "label": expense_label, "datatype": "Currency", "currency": currency},
		{"type": "separator", "value": "=", "color": "blue"},
		{
			"value": net_profit,
			"indicator": "Green" if net_profit > 0 else "Red",
			"label": profit_label,
			"datatype": "Currency",
			"currency": currency,
		},
	], net_profit


# def get_net_profit_loss(income, expense, period_list, company, currency=None, consolidated=False):
# 	total = 0
# 	net_profit_loss = {
# 		"account_name": "'" + _("Profit for the year") + "'",
# 		"account": "'" + _("Profit for the year") + "'",
# 		"warn_if_negative": True,
# 		"currency": currency or frappe.get_cached_value("Company", company, "default_currency"),
# 	}

# 	has_value = False

# 	for period in period_list:
# 		key = period if consolidated else period.key
# 		total_income = flt(income[-2][key], 3) if income else 0
# 		total_expense = flt(expense[-2][key], 3) if expense else 0

# 		net_profit_loss[key] = total_income - total_expense

# 		if net_profit_loss[key]:
# 			has_value = True

# 		total += flt(net_profit_loss[key])
# 		net_profit_loss["total"] = total

# 	if has_value:
# 		return net_profit_loss
def get_net_profit_loss(income, expense, period_list, company, currency=None, consolidated=False):
	total = 0
	net_profit_loss = {
		"account_name": "'" + _("Profit for the year") + "'",
		"account": "'" + _("Profit for the year") + "'",
		"warn_if_negative": True,
		"currency": currency or frappe.get_cached_value("Company", company, "default_currency"),
	}

	has_value = False

	for period in period_list:
		key = period if consolidated else period.key
		frappe.log_error(title="DEBUG: P&L Expense", message=str(expense))
		total_income = flt(income[-2][key], 3) if income and len(income) >= 2 else 0
		total_expense = flt(expense[-2].get(key, 0), 3) if len(expense) >= 2 else 0

		net_profit_loss[key] = total_income - total_expense

		if net_profit_loss[key]:
			has_value = True

		total += flt(net_profit_loss[key])
		net_profit_loss["total"] = total

	if has_value:
		return net_profit_loss


def get_chart_data(filters, columns, income, expense, net_profit_loss, currency):
	labels = [d.get("label") for d in columns[2:]]

	income_data, expense_data, net_profit = [], [], []

	for p in columns[2:]:
		if income:
			income_data.append(income[-2].get(p.get("fieldname")))
		# if expense:
		# 	expense_data.append(expense[-2].get(p.get("fieldname")))
		if len(expense) >= 2:
			expense_data.append(expense[-2].get(p.get("fieldname")))
			frappe.logger().debug("Expense Data", p.get("expense", []))
		else:
			expense_data.append(0)

		if net_profit_loss:
			net_profit.append(net_profit_loss.get(p.get("fieldname")))

	datasets = []
	if income_data:
		datasets.append({"name": _("Income"), "values": income_data})
	if expense_data:
		datasets.append({"name": _("Expense"), "values": expense_data})
	if net_profit:
		datasets.append({"name": _("Net Profit/Loss"), "values": net_profit})

	chart = {"data": {"labels": labels, "datasets": datasets}}

	if not filters.accumulated_values:
		chart["type"] = "bar"
	else:
		chart["type"] = "line"

	chart["fieldtype"] = "Currency"
	chart["options"] = "currency"
	chart["currency"] = currency

	return chart