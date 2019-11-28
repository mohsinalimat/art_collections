# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import throw, _
import frappe.defaults
from frappe.utils import cint, flt, get_fullname, cstr
from frappe.contacts.doctype.address.address import get_address_display
from erpnext.shopping_cart.doctype.shopping_cart_settings.shopping_cart_settings import get_shopping_cart_settings
from frappe.utils.nestedset import get_root_of
from erpnext.accounts.utils import get_account_name
from erpnext.utilities.product import get_qty_in_stock

# imported by art_collections
from erpnext.shopping_cart.cart import get_party,update_cart_address,get_shopping_cart_menu,apply_cart_settings,get_address_docs
from erpnext.shopping_cart.cart import get_applicable_shipping_rules

class WebsitePriceListMissingError(frappe.ValidationError):
	pass




# called from individual item page to show or not to show heart after checking in quotation wishlist
#not used
# @frappe.whitelist(allow_guest=True)
# def get_product_info_for_website(item_code):
# 	from erpnext.shopping_cart.doctype.shopping_cart_settings.shopping_cart_settings \
# 	import get_shopping_cart_settings, show_quantity_in_website
# 	from erpnext.utilities.product import get_price, get_qty_in_stock
# 	"""get product price / stock info for website"""

# 	cart_settings = get_shopping_cart_settings()
# 	if not cart_settings.enabled:
# 		return frappe._dict()

# 	cart_quotation = _get_cart_quotation(order_type='Shopping Cart Wish List')

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

# 	return frappe._dict({
# 		"wishlist_product_info": product_info,
# 		"cart_settings": cart_settings
# 	})

#called internaly
def set_cart_count(quotation=None):
	if cint(frappe.db.get_singles_value("Shopping Cart Settings", "enabled")):
		# if not quotation:
		party = get_party()
		order_type='Shopping Cart Wish List'
		quotations = frappe.get_all("Quotation", fields=["name"], filters={"party_name": party.name, "order_type": order_type, "docstatus": 0},order_by="modified desc")
		wishlist_cart_count=0
		for quotation in quotations:
			doc = frappe.get_doc('Quotation', quotation)
			wishlist_cart_count = (len(doc.get("items"))) + wishlist_cart_count
		wishlist_cart_count=cstr(wishlist_cart_count)
		if hasattr(frappe.local, "cookie_manager"):
			frappe.local.cookie_manager.set_cookie("wishlist_cart_count", wishlist_cart_count)

def decorate_quotation_doc(doc):
	from art_collections.api import get_qty_in_stock
	for d in doc.get("items", []):
		stock_status =get_qty_in_stock(d.item_code, "website_warehouse") 
		qty_in_stock=stock_status.stock_qty
		if qty_in_stock:
			d.update({'qty_in_stock':flt(qty_in_stock[0][0])})

		d.update(frappe.db.get_value("Item", d.item_code,
			["thumbnail", "website_image", "description", "route"], as_dict=True))

	return doc

# called from art_cart.py for rendering art_cart.html
@frappe.whitelist()
def get_cart_quotation(doc=None,wish_list_name=None):
	
	party = get_party()
	wish_list_names=frappe.db.get_all('Wish List Name',filters={'customer':party.name},fields='wish_list_name', order_by='wish_list_name asc',as_list=False)
	if not wish_list_name:
		if wish_list_names:
			wish_list_name=wish_list_names[0]['wish_list_name']
		else:
			wish_list_name=None

	if not doc:
		quotation = _get_cart_quotation(party,order_type='Shopping Cart Wish List',wish_list_name=wish_list_name)
		doc = quotation
		set_cart_count(quotation)

	addresses = get_address_docs(party=party)

	if not doc.customer_address and addresses:
		update_cart_address("customer_address", addresses[0].name)
	return {
		"doc": decorate_quotation_doc(doc),
		"shipping_addresses": [{"name": address.name, "display": address.display}
			for address in addresses],
		"billing_addresses": [{"name": address.name, "display": address.display}
			for address in addresses],
		"shipping_rules": get_applicable_shipping_rules(party),
		"cart_settings": frappe.get_cached_doc("Shopping Cart Settings"),
		"wish_list_name":wish_list_names,
		"selected_wish_list":wish_list_name
	}


def create_wish_list(wish_list_name):
	party = get_party()

	wish_list = frappe.get_all("Wish List Name", fields=["name"], filters=
		{"customer": party.name, "wish_list_name": wish_list_name},
		order_by="modified desc")
	if not wish_list:	
		doc = frappe.get_doc({
		'doctype': 'Wish List Name',
		'wish_list_name': wish_list_name,
		'customer':party.name
		})
		doc.insert()

#  main update wishlist cart function - called from heart icon on item detail / and on 'add to cart' from wishlist items page
@frappe.whitelist()
def update_cart_for_wishlist_preorder(item_code, qty, additional_notes=None, with_items=False,wish_list_name=None,is_stock_available=None):
	create_wish_list(wish_list_name)
	quotation = _get_cart_quotation(order_type='Shopping Cart Wish List',wish_list_name=wish_list_name)
	empty_card = False
	qty = flt(qty)
	if qty == 0:
		quotation_items = quotation.get("items", {"item_code": ["!=", item_code]})
		if quotation_items:
			quotation.set("items", quotation_items)
		else:
			empty_card = True

	else:
		quotation_items = quotation.get("items", {"item_code": item_code})
		if not quotation_items:
			quotation.append("items", {
				"doctype": "Quotation Item",
				"item_code": item_code,
				"qty": qty,
				"additional_notes": additional_notes,
				"is_stock_available_art":is_stock_available
			})
		else:
			quotation_items[0].qty = qty
			quotation_items[0].additional_notes = additional_notes

	apply_cart_settings(quotation=quotation)

	quotation.flags.ignore_permissions = True
	quotation.payment_schedule = []
	if not empty_card:
		quotation.flags.ignore_validate=True
		quotation.save()		
	else:
		quotation.delete()
		quotation = None

	set_cart_count(quotation)

	context = get_cart_quotation(quotation)

	if cint(with_items):
		return {
			"items": frappe.render_template("templates/includes/cart/art_cart_items.html",
				context),
			"taxes": frappe.render_template("templates/includes/order/order_taxes.html",
				context),
		}
	else:
		return {
			'name': quotation.name,
			'shopping_cart_menu': get_shopping_cart_menu(context)
		}

def _get_cart_quotation(party=None,order_type=None,wish_list_name=None):
	'''Return the open Quotation of type "Shopping Cart" or make a new one'''
	if not party:
		party = get_party()

	quotation = frappe.get_all("Quotation", fields=["name"], filters=
		{"party_name": party.name, "order_type": order_type, "docstatus": 0,"wish_list_name":wish_list_name},
		order_by="modified desc", limit_page_length=1)

	if quotation:
		qdoc = frappe.get_doc("Quotation", quotation[0].name)
	else:
		company = frappe.db.get_value("Shopping Cart Settings", None, ["company"])
		qdoc = frappe.get_doc({
			"doctype": "Quotation",
			"naming_series": get_shopping_cart_settings().quotation_series or "QTN-CART-",
			"title":party.customer_name or party.name,
			"quotation_to": party.doctype,
			"company": company,
			"order_type": order_type,
			"status": "Draft",
			"docstatus": 0,
			"__islocal": 1,
			"party_name": party.name,
			"wish_list_name":wish_list_name
		})

		qdoc.contact_person = frappe.db.get_value("Contact", {"email_id": frappe.session.user})
		qdoc.contact_email = frappe.session.user

		qdoc.flags.ignore_permissions = True
		qdoc.run_method("set_missing_values")
		apply_cart_settings(party, qdoc)

	return qdoc

# called from hook
def set_wishlist_cart_count(login_manager):
	from erpnext.shopping_cart.utils import  show_cart_count , check_customer_or_supplier
	role, parties = check_customer_or_supplier()
	if role == 'Supplier': return
	if show_cart_count():
		set_cart_count()

def clear_wishlist_cart_count(login_manager):
	from erpnext.shopping_cart.utils import  show_cart_count
	if show_cart_count():
		frappe.local.cookie_manager.delete_cookie("wishlist_cart_count")