import frappe
from frappe import _


def get_data():
    return {
        "fieldname": "name",
        "non_standard_fieldnames": {"Purchase Receipt": "ref_supplier_packing_list_art"},
        "internal_links": {
			"Purchase Order": ["supplier_packing_list_detail", "purchase_order"],
            "Art Shipment": ["supplier_packing_list_detail", "shipment"],
		},
        "transactions": [
            {
                "label": _("Reference"),
                "items": ["Purchase Receipt","Purchase Order","Art Shipment"]
            }
        ],
    }