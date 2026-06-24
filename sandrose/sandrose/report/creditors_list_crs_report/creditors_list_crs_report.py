# Copyright (c) 2026, Sandrose and contributors
# For license information, please see license.txt

# import frappe


# def execute(filters=None):
# 	columns, data = [], []
# 	return columns, data


from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import (
    AccountsReceivableSummary,
)
import frappe


class CreditorsListCRSReport(AccountsReceivableSummary):

    def run(self, args):
        columns, data = super().run(args)

        # ---------------------------------------------------------
        # Find index of Outstanding column
        # ---------------------------------------------------------
        outstanding_index = None
        for i, col in enumerate(columns):
            if col.get("fieldname") == "outstanding":
                outstanding_index = i
                break

        # If not found, append at end (fallback)
        if outstanding_index is None:
            outstanding_index = len(columns) - 1

        # ---------------------------------------------------------
        # Define new columns
        # ---------------------------------------------------------
        new_columns = [
            {
                "label": "PDC",
                "fieldname": "pdc",
                "fieldtype": "Currency",
                "width": 120,
            },
            {
                "label": "Total Purchase Order Amount",
                "fieldname": "total_po_amount",
                "fieldtype": "Currency",
                "width": 180,
            },
            {
                "label": "Net CRS",
                "fieldname": "net_crs",
                "fieldtype": "Currency",
                "width": 120,
            },
        ]

        # ---------------------------------------------------------
        # Insert new columns after Outstanding
        # ---------------------------------------------------------
        for idx, col in enumerate(new_columns):
            columns.insert(outstanding_index + 1 + idx, col)

        # ---------------------------------------------------------
        # Add values to each row
        # ---------------------------------------------------------
        company = self.filters.get("company")

        for row in data:
            supplier = row.get("party")
            outstanding = row.get("outstanding") or 0

            # PDC (Future-dated Payment Entries)
            pdc = frappe.db.sql(
                """
                SELECT SUM(paid_amount)
                FROM `tabPayment Entry`
                WHERE party_type = 'Supplier'
                AND party = %s
                AND company = %s
                AND docstatus = 1
                AND posting_date > CURDATE()
                """,
                (supplier, company),
            )[0][0] or 0

            # Total Purchase Order Amount
            # total_po = frappe.db.sql(
            #     """
            #     SELECT SUM(grand_total)
            #     FROM `tabPurchase Order`
            #     WHERE supplier = %s
            #     AND company = %s
            #     AND docstatus = 1
            #     """,
            #     (supplier, company),
            # )[0][0] or 0

            # Total Purchase Order Amount (Unbilled / To Receive and Bill / To Bill)
            total_po = 0
            po_list = frappe.db.sql(
                """
                SELECT name, grand_total
                FROM `tabPurchase Order`
                WHERE supplier=%s
                AND company=%s
                AND docstatus=1
                AND status IN ('To Receive and Bill', 'To Bill')
                """,
                (supplier, company),
                as_dict=True
            )

            for po in po_list:
                billed_amount = frappe.db.sql(
                    """
                    SELECT SUM(pi_item.amount)
                    FROM `tabPurchase Invoice Item` pi_item
                    JOIN `tabPurchase Invoice` pi
                    ON pi.name = pi_item.parent AND pi.docstatus = 1
                    WHERE pi_item.purchase_order = %s
                    """,
                    (po.name,),
                )[0][0] or 0

                total_po += po.grand_total - billed_amount
            # Net CRS Formula
            net_crs = outstanding + pdc + total_po

            row.update(
                {
                    "pdc": pdc,
                    "total_po_amount": total_po,
                    "net_crs": net_crs,
                }
            )

        return columns, data


def execute(filters=None):
    args = {
        "account_type": "Payable",
        "naming_by": ["Buying Settings", "supp_master_name"],
    }

    return CreditorsListCRSReport(filters).run(args)