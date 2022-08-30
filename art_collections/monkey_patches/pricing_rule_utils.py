# Copyright (c) 2013, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, today
from erpnext.accounts.doctype.pricing_rule import pricing_rule
from erpnext.accounts.doctype.pricing_rule.pricing_rule import (
    get_pricing_rule_for_item as _get_pricing_rule_for_item,
)
from erpnext.accounts.doctype.pricing_rule import utils
from erpnext.accounts.doctype.pricing_rule.utils import (
    filter_pricing_rules_for_qty_amount as _filter_pricing_rules_for_qty_amount,
)


def get_pricing_rule_for_item(args, price_list_rate=0, doc=None, for_validate=False):
    if args.get("customer"):
        if cint(
            frappe.db.get_value("Customer", args.get("customer"), "has_volume_price_cf")
        ):
            args["customer_has_volume_price_cf"] = 1
    return _get_pricing_rule_for_item(args, price_list_rate, doc, for_validate)


def filter_pricing_rules_for_qty_amount(qty, rate, pricing_rules, args=None):
    """Override check fo min_qty while applying pricing rule if:
    >> customer has_volume_price = 1
    >> pricing_rule is_volume_price_cf = 1"""
    rules = []
    if args.get("parenttype") in [
        "Quotation",
        "Sales Order",
        "Sales Invoice",
        "Delivery Note",
    ]:
        for rule in pricing_rules:
            if not cint(rule.get("is_volume_price_cf")):
                continue
            if args.get("customer_has_volume_price_cf"):
                rule.min_qty = 0
                rule.min_amt = 0
    return _filter_pricing_rules_for_qty_amount(qty, rate, pricing_rules, args)


pricing_rule.get_pricing_rule_for_item = get_pricing_rule_for_item
utils.filter_pricing_rules_for_qty_amount = filter_pricing_rules_for_qty_amount
