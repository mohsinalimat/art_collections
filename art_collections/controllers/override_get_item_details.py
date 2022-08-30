# Copyright (c) 2013, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import art_collections
import frappe
from frappe import _
from frappe.utils import cint, today

from erpnext.stock.get_item_details import (
    get_item_details as _get_item_details,
    process_args,
)

from erpnext.accounts.doctype.pricing_rule.utils import (
    filter_pricing_rules_for_qty_amount as original,
)

import erpnext.accounts.doctype.pricing_rule.utils


@frappe.whitelist()
def get_item_details(args, doc=None, for_validate=False, overwrite_warehouse=True):
    """Override check fo min_qty while applying pricing rule if:
    >> customer has_volume_price = 1
    >> pricing_rule is_volume_price_cf = 1"""

    meta = frappe.get_meta("Customer")
    if not meta.has_field("has_volume_price_cf"):
        return _get_item_details(args, doc, for_validate, overwrite_warehouse)

    args = process_args(args)

    if not args.get("doctype") in (
        "Quotation",
        "Sales Order",
        "Delivery Note",
        "Sales Invoice",
    ):
        return _get_item_details(args, doc, for_validate, overwrite_warehouse)

    has_volume_price_cf = frappe.db.get_value(
        "Customer", args.get("customer"), "has_volume_price_cf"
    )
    if not has_volume_price_cf:
        return _get_item_details(args, doc, for_validate, overwrite_warehouse)

    args["ignore_pricing_rule"] = 0

    def filter_pricing_rules_for_qty_amount(qty, rate, pricing_rules, args=None):
        for rule in pricing_rules:
            if cint(rule.get("is_volume_price_cf")):
                rule.min_qty = 0
                rule.min_amt = 0

        return original(qty, rate, pricing_rules, args)

    patch_method(
        erpnext.accounts.doctype.pricing_rule.utils,
        "filter_pricing_rules_for_qty_amount",
        filter_pricing_rules_for_qty_amount,
    )

    return _get_item_details(args, doc, for_validate, overwrite_warehouse)


def patch_method(obj, method, override):
    """Monkey Patch helper. Will override an object's method with a custome one"""
    orig = getattr(obj, method)
    if hasattr(orig, "monkeypatched") and orig.monkeypatched == override:
        return

    override.patched_method = orig

    def __fn(*args, **kwargs):
        return override(*args, **kwargs)

    __fn.monkeypatched = override

    setattr(obj, method, __fn)
