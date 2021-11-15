from __future__ import unicode_literals

import json

import frappe
from frappe import _
from frappe.utils import  nowdate

import erpnext

def daily():
	sales_order_workflow_update()

def sales_order_workflow_update():
	sales_orders=frappe.db.sql("""select name from `tabSales Order` so
			where docstatus=1 and needs_confirmation_art=1
				and workflow_state='Bon de Commande'
				and order_expiry_date_ar < %(today)s
				""",
			{"today": nowdate()},as_dict=True)	

	if len(sales_orders)>0:
		for so in sales_orders:
			doc = frappe.get_doc('Sales Order', so.name)
			doc.db_set('workflow_state', 'Cancelled', commit=True)