# Copyright (c) 2013, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint
import calendar


def execute(filters=None):
    from erpnext.accounts.report.general_ledger.general_ledger import execute

    columns, data = execute(filters)

    out = []

    for idx, d in enumerate(data):
        out.append(d)
        curr_date = d.get("posting_date")
        if not curr_date:
            continue
        next_date = data[idx + 1].get("posting_date")
        if next_date and not next_date.month == curr_date.month:
            # closing for curr month
            debit = sum([i["debit"] for i in out if i.get("voucher_no")])
            credit = sum([i["credit"] for i in out if i.get("voucher_no")])
            balance = sum([i["balance"] for i in out if i.get("voucher_no")])
            out.append(
                {
                    "posting_date": None,
                    "account": "Closing {}".format(_(curr_date.strftime("%B %Y"))),
                    "debit": debit,
                    "credit": credit,
                    "balance": debit-credit,
                }
            )
            # opening for next month
            out.append(
                {
                    "posting_date": None,
                    "account": "Opening {}".format(_(next_date.strftime("%B %Y"))),
                    "debit": debit,
                    "credit": credit,
                    "balance": debit-credit,
                }
            )

    return columns, out
