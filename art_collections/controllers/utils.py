# -*- coding: utf-8 -*-
# Copyright (c) 2022, GreyCube Technologies and Contributors
# See license.txt
import frappe
from erpnext.accounts.party import (
    get_default_contact,
    set_contact_details as _set_contact_details,
)


@frappe.whitelist()
def set_contact_details(party_name, party_type, party_details=None):
    if not party_details:
        party_details = frappe._dict()
    _set_contact_details(party_details, frappe._dict({"name": party_name}), party_type)
    return party_details


def after_insert_communication(doc, method=None):
    """handle reply from Supplier for Photo Quotation, Sales Confirmation"""
    try:
        reference_doctype = doc.get("reference_doctype")
        reference_name = doc.get("reference_name")
        if (
            doc.communication_type == "Communication"
            and reference_doctype
            and reference_name
        ):
            if reference_doctype == "Photo Quotation":
                frappe.db.set_value(
                    "Photo Quotation", reference_name, "status", "To be Treated"
                )
            elif reference_doctype == "Sales Confirmation":
                frappe.db.set_value(
                    "Sales Confirmation", reference_name, "status", "To be Treated"
                )
                frappe.db.set_value(
                    "Sales Confirmation",
                    reference_name,
                    "confirmation_date",
                    frappe.utils.today(),
                )
    except Exception:
        frappe.log_error(frappe.get_traceback())
