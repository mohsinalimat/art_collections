# Copyright (c) 2013, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from pypika import NULL
from frappe.utils import flt
from art_collections.api import get_average_daily_outgoing_art,get_average_delivery_days_art

def execute(filters=None):
	print('-'*100)
	columns, data = [], []
	columns=get_columns()
	data = get_data()
	return columns, data

def get_columns():
	return [  {
   "fieldname": "item_code",
   "fieldtype": "Link",
   "label": "Item",
   "options": "Item",
   "width": 400
  },
  {
   "fieldname": "item_group",
   "fieldtype": "Link",
   "label": "Group",
   "options": "Item Group",
   "width": 120
  },
  {
   "fieldname": "total_in_stock",
   "fieldtype": "Float",
   "label": "Total Stock",
   "width": 100
  },
  {
   "fieldname": "sold_qty_to_deliver",
   "fieldtype": "Float",
   "label": "Qty Sold: to Deliver",
   "width": 120
  },
  {
   "fieldname": "sold_qty_delivered",
   "fieldtype": "Float",
   "label": "Qty Sold: Delivered",
   "width": 120
  },
  {
   "fieldname": "total_virtual_stock",
   "fieldtype": "Float",
   "label": "Qty available",
   "width": 100
  },
  {
   "fieldname": "avg_qty_sold_per_month",
   "fieldtype": "Float",
   "label": "Avg. Qty sold per month",
   "width": 140
  },
  {
   "fieldname": "avg_daily_outgoing",
   "fieldtype": "Float",
   "label": "Avg. Daily Outgoing",
   "width": 140
  },
  {
   "fieldname": "avg_delivery_days",
   "fieldtype": "Float",
   "label": "Avg. Delivery Days",
   "width": 140
  },
  {
   "fieldname": "day_remaining_with_the_stock",
   "fieldtype": "Float",
   "label": "Days remaining with Stock",
   "width": 160
  }
	]

def get_data():
	data = []
	items=frappe.db.sql("""select name, item_name,item_group,has_variants,is_fixed_asset,is_stock_item,variant_of from `tabItem` as item
where item.has_variants =0 and item.is_fixed_asset =0 and item.is_stock_item =1 and item.variant_of is NULL and item.disabled =0
order by name """,as_dict=True)
	for d in items:
		item_code=d.name
		total_in_stock=frappe.db.sql("""select COALESCE(sum(actual_qty),0) from tabBin where item_code = %s """,(item_code))[0][0]
		sold_qty_to_deliver=frappe.db.sql("""select sum(so_item.stock_qty-so_item.delivered_qty) as sold_qty_to_deliver from `tabSales Order` so inner join `tabSales Order Item` so_item on so_item.parent =so.name 
	where so.status in ("To Deliver and Bill","To Deliver") and so_item.item_code =%s """,(item_code))[0][0]
		sold_qty_delivered=frappe.db.sql("""select sum(so_item.delivered_qty) as sold_qty_to_deliver from `tabSales Order` so inner join `tabSales Order Item` so_item on so_item.parent =so.name 
	where so.status in ("To Deliver and Bill","To Deliver") and so_item.item_code =%s """,(item_code))[0][0]
		if sold_qty_to_deliver!=None:
			total_virtual_stock=flt(total_in_stock-sold_qty_to_deliver)
		else:
			total_virtual_stock=flt(total_in_stock)
		avg_daily_outgoing=get_average_daily_outgoing_art(item_code).average_daily_outgoing_art or 0.0
		avg_qty_sold_per_month=flt(avg_daily_outgoing*30)
		avg_delivery_days=flt(get_average_delivery_days_art(item_code))
		day_remaining_with_the_stock=flt(total_in_stock/avg_daily_outgoing) if avg_daily_outgoing!=0.0 else 0.0

		row = {
			"item_code": item_code, 
			"item_name": d.item_name,
			"item_group": d.item_group
		, "total_in_stock": total_in_stock
		, "sold_qty_to_deliver": sold_qty_to_deliver
		, "sold_qty_delivered": sold_qty_delivered
		, "total_virtual_stock": total_virtual_stock
		, "avg_qty_sold_per_month": avg_qty_sold_per_month
		, "avg_daily_outgoing": avg_daily_outgoing
		, "avg_delivery_days": avg_delivery_days,
		"day_remaining_with_the_stock": day_remaining_with_the_stock}

		data.append(row)
	return data	