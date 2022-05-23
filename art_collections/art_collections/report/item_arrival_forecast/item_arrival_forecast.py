# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns, data = [], []
	return get_columns(filters), get_data(filters)

def get_data(filters=None):
	data = frappe.db.sql("""SELECT  po.name, po.status, po_item.item_code, po_item.item_name, po_item.stock_qty, 
po_item.arrival_forecast_date_art, spl_item.qty_as_per_spl, po_item.shipping_date_art ,
spl_item.shipment, spl_item.parent as spl  FROM `tabPurchase Order` as po
inner join `tabPurchase Order Item` as po_item 
on po.name=po_item.parent 
left outer join `tabSupplier Packing List Detail Art` as spl_item 
on spl_item.purchase_order =po.name where po_item.received_qty != po_item.stock_qty
order by po.name DESC""",as_dict=1,debug=1)
	print(data)
	return data	

def get_columns(filters):
    columns = [
        {
            "label": _("PO#"),
            "fieldtype": "Link",
            "fieldname": "name",
            "options": "Purchase Order",
            "width": 180
        },		
        {
            "label": _("PO Status"),
            "fieldname": "status",
            "width": 160
        },
        {
            "label": _("PO Item Code"),
            "fieldtype": "Link",
            "fieldname": "item_code",
            "options": "Item",
            "width": 220
        },
        {
            "label": _("PO Item Name"),
            "fieldname": "item_name",
            "width": 220
        },		
        {
            "label": _("PO Qty(Stock UOM)"),
            "fieldname": "stock_qty",
			"fieldtype": "Float",
            "width": 160
        },			
        {
            "label": _("Arrival Forecast Dt (PO Item)"),
            "fieldname": "arrival_forecast_date_art",
			"fieldtype": "Date",
            "width": 170
        },
        {
            "label": _("SPL Qty(Stock UOM)"),
            "fieldname": "qty_as_per_spl",
			"fieldtype": "Float",
            "width": 160
        },	
        {
            "label": _("Shipping Date"),
            "fieldname": "shipping_date_art",
			"fieldtype": "Date",
            "width": 150
        },
        {
            "label": _("Shipment"),
            "fieldtype": "Link",
            "fieldname": "shipment",
            "options": "Art Shipment",
            "width": 160
        },
        {
            "label": _("Supplier Packing List"),
            "fieldtype": "Link",
            "fieldname": "spl",
            "options": "Supplier Packing List Art",
            "width": 180
        },							
	    ]

    return columns	