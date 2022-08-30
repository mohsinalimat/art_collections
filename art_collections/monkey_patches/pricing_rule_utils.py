# Copyright (c) 2013, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, today

from erpnext.accounts.doctype.pricing_rule import utils
from erpnext.accounts.doctype.pricing_rule.utils import (
    filter_pricing_rules_for_qty_amount as _filter_pricing_rules_for_qty_amount,
)


def filter_pricing_rules_for_qty_amount(qty, rate, pricing_rules, args=None):
    """Override check fo min_qty while applying pricing rule if:
    >> customer has_volume_price = 1
    >> pricing_rule is_volume_price_cf = 1"""
    has_volume_price_cf = frappe.db.get_value(
        "Customer", args.get("customer"), "has_volume_price_cf"
    )

    rules = []
    if (args.get("parenttype") or args.get("doctype")) in [
        "Quotation",
        "Sales Order",
        "Sales Invoice",
        "Delivery Note",
    ]:
        for rule in pricing_rules:
            if cint(has_volume_price_cf) and cint(rule.get("is_volume_price_cf")):
                rule.min_qty = 0
                rule.min_amt = 0
    rules = _filter_pricing_rules_for_qty_amount(qty, rate, pricing_rules, args)
    return rules


utils.filter_pricing_rules_for_qty_amount = filter_pricing_rules_for_qty_amount
