# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt
from __future__ import unicode_literals

no_cache = 1

import frappe
from art_collections.art_cart import get_cart_quotation

def get_context(context):
	if frappe.form_dict:
		print('frappe.form_dict.wish_list',frappe.form_dict.wish_list)
		context.update(get_cart_quotation(wish_list_name=frappe.form_dict.wish_list))
		# context.update({'selected_wish_list':frappe.form_dict.wish_list})
	else:
		context.update(get_cart_quotation())
