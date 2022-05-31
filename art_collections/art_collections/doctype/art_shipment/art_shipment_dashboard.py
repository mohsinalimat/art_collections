import frappe
from frappe import _


def get_data():
    return {
        "fieldname": "name",
        "non_standard_fieldnames": {"Supplier Packing List Art": "shipment"},
        "transactions": [
            {
                "label": _("Reference"),
                "items": ["Supplier Packing List Art"],
            }
        ],
    }