# # -*- coding: utf-8 -*-

from __future__ import unicode_literals
import os
import importlib

__version__ = "0.0.1"

import frappe

patches_loaded = False
app_name = "art_collections"


def load_monkey_patches():
    """
    https://github.com/aakvatech/CSF_TZ/blob/f3fd774aa8bb37e314f769a59f24285d238dae94/csf_tz/__init__.py
    Loads all modules present in monkey_patches to override some logic
    in Frappe / ERPNext. Returns if patches have already been loaded earlier.
    """
    global patches_loaded

    if patches_loaded:
        return

    patches_loaded = True

    if app_name not in frappe.get_installed_apps():
        return

    for module_name in os.listdir(frappe.get_app_path(app_name, "monkey_patches")):
        if not module_name.endswith(".py") or module_name == "__init__.py":
            continue

        importlib.import_module(app_name + ".monkey_patches." + module_name[:-3])
        frappe.log_error(app_name + ": loaded module " + module_name)


old_get_hooks = frappe.get_hooks


def get_hooks(*args, **kwargs):
    load_monkey_patches()
    return old_get_hooks(*args, **kwargs)


frappe.get_hooks = get_hooks

# from erpnext.e_commerce.shopping_cart.cart import _get_cart_quotation,get_party
# from erpnext.e_commerce.doctype.e_commerce_settings.e_commerce_settings import get_shopping_cart_settings, show_quantity_in_website
# from erpnext.utilities.product import get_price
# from art_collections.api import get_qty_in_stock

# # from erpnext.e_commerce.shopping_cart.product_info import  product_info,cart

# from erpnext.stock.doctype.item import item_dashboard

# from erpnext.e_commerce.shopping_cart.cart import apply_cart_settings,set_cart_count,get_cart_quotation

# def patch_method(obj, method, override):
#     # https://github.com/DigiThinkIT/frappe_utils/blob/master/monkey.py
#     """Monkey Patch helper. Will override an object's method with a custome one"""
#     orig = getattr(obj, method)
#     if hasattr(orig, "monkeypatched") and orig.monkeypatched == override:
#         return

#     override.patched_method = orig

#     def __fn(*args, **kwargs):
#         return override(*args, **kwargs)
#     __fn.monkeypatched = override

#     setattr(obj, method, __fn)

# @frappe.whitelist(allow_guest=True)
# def get_product_info_for_website(item_code,skip_quotation_creation=False):
# 	from erpnext.e_commerce.shopping_cart.cart import get_party
# 	"""get product price / stock info for website"""

# 	cart_settings = get_shopping_cart_settings()
# 	if not cart_settings.enabled:
# 		return frappe._dict()

# 	cart_quotation = get_cart_quotation()

# 	price = get_price(
# 		item_code,
# 		cart_quotation.selling_price_list,
# 		cart_settings.default_customer_group,
# 		cart_settings.company
# 	)

# 	stock_status = get_qty_in_stock(item_code, "website_warehouse")

# 	product_info = {
# 		"price": price,
# 		"stock_qty": stock_status.stock_qty,
# 		"in_stock": stock_status.in_stock if stock_status.is_stock_item else 1,
# 		"qty": 0,
# 		"uom": frappe.db.get_value("Item", item_code, "stock_uom"),
# 		"show_stock_qty": show_quantity_in_website(),
# 		"sales_uom": frappe.db.get_value("Item", item_code, "sales_uom")
# 	}

# 	if product_info["price"]:
# 		if frappe.session.user != "Guest":
# 			item = cart_quotation.get({"item_code": item_code})
# 			if item:
# 				product_info["qty"] = item[0].qty
#     # wish_list_name and is_item_in_wishlist parameters are added
# 	party = get_party()
# 	if frappe.db.exists("DocType", 'Wish List Name'):
# 		wish_list_name=frappe.db.get_all('Wish List Name',filters={'customer':party.name},fields='wish_list_name', order_by='wish_list_name asc',as_list=False)
# 	else:
# 		wish_list_name=None

# 	return frappe._dict({
# 		"product_info": product_info,
# 		"cart_settings": cart_settings,
# 		"wish_list_name":wish_list_name,
#         "is_item_in_wishlist":is_item_in_wishlist(item_code)
# 	})

# def is_item_in_wishlist(item_code):
# 	found=False
# 	party = get_party()
# 	order_type='Shopping Cart Wish List'
# 	quotation = frappe.get_all("Quotation", fields=["name"], filters=
# 		{"party_name": party.name, "order_type": order_type, "docstatus": 0},
# 		order_by="modified desc", limit_page_length=1)

# 	if quotation:
# 		qdoc = frappe.get_doc("Quotation", quotation[0].name)
# 		for item in qdoc.get("items"):
# 			if item.item_code==item_code:
# 				found=True
# 				return found
# 		return found
# 	else:
# 		return found

# def get_data():
# 	from frappe import _
# 	return {
# 		'heatmap': True,
# 		'heatmap_message': _('This is based on stock movement. See {0} for details')\
# 			.format('<a href="#query-report/Stock Ledger">' + _('Stock Ledger') + '</a>'),
# 		'fieldname': 'item_code',
# 		'non_standard_fieldnames': {
# 			'Work Order': 'production_item',
# 			'Product Bundle': 'new_item_code',
# 			'BOM': 'item',
# 			'Batch': 'item',
# 			'Issue':'item'
# 		},
# 		'transactions': [
# 			{
# 				'label': _('Groups'),
# 				'items': ['BOM', 'Product Bundle', 'Item Alternative']
# 			},
# 			{
# 				'label': _('Pricing'),
# 				'items': ['Item Price', 'Pricing Rule']
# 			},
# 			{
# 				'label': _('Sell'),
# 				'items': ['Quotation', 'Sales Order', 'Delivery Note', 'Sales Invoice']
# 			},
# 			{
# 				'label': _('Buy'),
# 				'items': ['Material Request', 'Supplier Quotation', 'Request for Quotation',
# 					'Purchase Order', 'Purchase Receipt', 'Purchase Invoice']
# 			},
# 			{
# 				'label': _('Traceability'),
# 				'items': ['Serial No', 'Batch']
# 			},
# 			{
# 				'label': _('Move'),
# 				'items': ['Stock Entry']
# 			},
# 			{
# 				'label': _('Manufacture'),
# 				'items': ['Production Plan', 'Work Order', 'Item Manufacturer']
# 			},
# 			{
# 				'label': _('Support'),
# 				'items': ['Issue']
# 			}
# 		]
# 	}

# app_name='art_collections'
# # if (app_name in frappe.get_installed_apps()):

# # patch_method(product_info,"get_product_info_for_website", get_product_info_for_website)

# # patch_method(item_dashboard,"get_data", get_data)
