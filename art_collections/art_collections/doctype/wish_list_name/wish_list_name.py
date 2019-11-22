# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class WishListName(Document):
	def autoname(self):
		self.name = self.wish_list_name +" "+ self.customer

	
	def on_trash(self):
		frappe.msgprint('All Linked Wish List are getting deleted..')
		linked_quotation=frappe.db.get_all('Quotation',filters={'order_type':'Shopping Cart Wish List','docstatus':0,'wish_list_name':self.wish_list_name,'party_name': self.customer})
		if linked_quotation:
			for quot in linked_quotation:
				print(quot)
				doc=frappe.get_doc('Quotation', quot.name)
				doc.flags.ignore_permissions = True
				doc.delete()