# Copyright (c) 2013, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns, data = [], []
	columns=get_columns()
	data = get_data(filters)	
	return columns, data

def get_columns():
	return [
  {
   "fieldname": "picker",
   "fieldtype": "Data",
   "label": "Picker",
   "width": 300
  },
  {
   "fieldname": "qty_order_prepared",
   "fieldtype": "Int",
   "label": "Qty order prepared ",
   "width": 150
  },
  {
   "fieldname": "qty_product_picked",
   "fieldtype": "Int",
   "label": "Qty product picked",
   "width": 150
  }
 ]

def get_data(filters):
	data = []
	conditions = ''
	if filters.from_date and filters.to_date:
		values = {
			'from_date': filters.from_date,
			'to_date': filters.to_date
		}
	
	if filters.picker:
		conditions += " and pi.picker_responsible_art = '{0}'".format(filters.picker)

	data = frappe.db.sql("""
SELECT  user.full_name as picker, COUNT(DISTINCT(pi.name)) as qty_order_prepared ,
sum(item.picked_qty) as qty_product_picked
from `tabPick List` pi
inner join `tabPick List Item` item on pi.name=item.parent 
inner join `tabUser` user on pi.picker_responsible_art=user.name
where pi.docstatus!=2
and pi.creation BETWEEN %(from_date)s and %(to_date)s
{0}
group by picker_responsible_art 
order by user.full_name
""".format(conditions), values, as_dict=1)
	
	return data		