from __future__ import unicode_literals
import frappe
from frappe import throw, _
from frappe.model.naming import make_autoname
from frappe.utils import cstr

def set_address_title_based_on_customer(self,method):
	address_title=None
	if self.links:
		if self.links[0].link_doctype=='Customer':
			trade_name=frappe.db.get_value('Customer', self.links[0].link_name, 'trade_name')
			address_lists=[
													trade_name,
													self.city,
													self.zip_code,
													self.art_state,
													self.art_county,	
									]

			address_lists_filtered = filter(lambda address: address !=None, address_lists)
			address_title = "-".join(
					cstr(_(d).strip())
					for d in address_lists_filtered
			)
			self.address_title=address_title[0:140]

	if address_title:
		self.name = self.address_title
		if frappe.db.exists("Address", self.name):
			self.name = make_autoname(self.address_title + "-.#")
	else:
		throw(_("Address Title is mandatory."))