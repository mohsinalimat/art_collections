import frappe
from frappe import _


def get_data():
    return {
        "fieldname": "name",
        "non_standard_fieldnames": {"Purchase Receipt": "ref_supplier_packing_list_art"},
        "transactions": [
            {
                "label": _("Reference"),
                "items": ["Purchase Receipt"],
            }
        ],
    }