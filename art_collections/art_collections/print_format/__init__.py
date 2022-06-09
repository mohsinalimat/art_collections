# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe


def get_shipping_and_taxes_cost(doctype, docname):
    shipping_cost, taxes_cost = 0, 0
    doc = frappe.get_doc(doctype, docname)
    for tax in doc.get("taxes"):
        account_type = frappe.db.get_value(
            "Account", tax.get("account_head"), "account_type"
        )
        if account_type == "Tax":
            taxes_cost += tax.base_tax_amount
        else:
            shipping_cost += tax.base_tax_amount
    return shipping_cost, taxes_cost
