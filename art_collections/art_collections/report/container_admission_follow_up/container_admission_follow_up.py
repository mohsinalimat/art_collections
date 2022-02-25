# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _


def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = [
		{
			"fieldname": "owner",
			"fieldtype": "Link",
			"options": "User",
			"label": _('Created by'),
			"width": 100
		},
		{
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"label": _('Supplier'),
			"width": 100
		},
		{
			"fieldname": "supplier_name",
			"fieldtype": "Data",
			"label": _("Supplier Name"),
			"width": 130
		},
		{
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Purchase Order",
			"label": _('PO name'),
			"width": 100
		},	
		{
			"fieldname": "total_outer_cartons_ordered_art",
			"fieldtype": "Int",
			"label": _("Outer Qty"),
			"width": 50
		},			
		{
			"fieldname": "total_qty",
			"fieldtype": "Int",
			"label": _("Total Qty"),
			"width": 50
		},		
		{
			"fieldname": "container_number_art",
			"fieldtype": "Data",
			"label": _("Container #"),
			"width": 80
		},		
		{
			"fieldname": "transport_type_art",
			"fieldtype": "Data",
			"label": _("Transport Type"),
			"width": 60
		},	
		{
			"fieldname": "transport_size_art",
			"fieldtype": "Data",
			"label": _("Transport Size"),
			"width": 60
		},			
		{
			"fieldname": "schedule_date",
			"fieldtype": "Date",
			"label": _("Availibility Date"),
			"width": 100
		},
		{
			"fieldname": "set_apart_art",
			"fieldtype": "Data",
			"label": _("Set Apart"),
			"width": 80
		},	
		{
			"fieldname": "set_apart_comment_art",
			"fieldtype": "Data",
			"label": _("Set Apart Comment"),
			"width": 60
		},		
		{
			"fieldname": "arrival_forecast_date_art",
			"fieldtype": "Date",
			"label": _("Arrival Forcast Date"),
			"width": 100
		},
		{
			"fieldname": "arrival_forecast_hour_art",
			"fieldtype": "Time",
			"label": _("Arrival Forecast Hour"),
			"width": 60
		},
		{
			"fieldname": "status",
			"fieldtype": "Data",
			"label": _("Received"),
			"width": 50
		},							
		{
			"fieldname": "telex_release_sent_date_art",
			"fieldtype": "Date",
			"label": _("Telex Sent Date"),
			"width": 100
		},
		{
			"fieldname": "ship_name_art",
			"fieldtype": "Data",
			"label": _("Ship"),
			"width": 70
		}
	]

	return columns

def get_data(filters):	
	query='''SELECT po.owner, po.supplier, po.supplier_name ,po.name,po.total_outer_cartons_ordered_art,count(po_item.idx) as total_qty,po.container_number_art,po.transport_type_art,
	po.transport_size_art,po.schedule_date,po.set_apart_art,IF(ISNULL(po.set_apart_comment_art),NULL,'YES') as set_apart_comment_art,po.arrival_forecast_date_art,po.arrival_forecast_hour_art,
IF(po.status IN('To Bill','Completed','Delivered'),'YES','NO') as status,
po.telex_release_sent_date_art,po.ship_name_art 
FROM  `tabPurchase Order` po
inner join `tabPurchase Order Item` po_item
on po.name=po_item.parent
group by po.name
order by po.creation DESC'''
	data = frappe.db.sql(query, as_dict=1)
	return data	