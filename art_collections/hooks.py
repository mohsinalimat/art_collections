# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version
from frappe import _

app_name = "art_collections"
app_title = "Art Collections"
app_publisher = "GreyCube Technologies"
app_description = "Customization for art collections"
app_icon = "octicon octicon-gift"
app_color = "violet"
app_email = "admin@greycube.in"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/art_collections/css/art_collections.css"
# app_include_js = "/assets/art_collections/js/art_collections.js"

# include js, css files in header of web template
web_include_css = "/assets/art_collections/css/art_collections.css"
web_include_js = ["/assets/art_collections/js/shopping_cart.js"]

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
"Customer" : "public/js/customer.js",
"Supplier" : "public/js/supplier.js",
"Address" : "public/js/address.js",
"Item" : "public/js/item.js",
"Delivery Note":"public/js/delivery_note.js",
"Sales Order" : "public/js/sales_order.js",
"Purchase Order" : "public/js/purchase_order.js",
"Issue" : "public/js/issue.js",
"Pricing Rule" : "public/js/pricing_rule.js",
"POS Profile": "public/js/pos_profile.js",
"Supplier Quotation": "public/js/supplier_quotation.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "art_collections.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "art_collections.install.before_install"
# after_install = "art_collections.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "art_collections.notifications.get_notification_config"

on_session_creation = "art_collections.art_cart.set_wishlist_cart_count"
on_logout = "art_collections.art_cart.clear_wishlist_cart_count"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Item": { 
		"validate": "art_collections.api.update_flag_table",
		"autoname": "art_collections.api.set_item_code_for_pre_item"
		},
	"Pricing Rule": { "on_update": "art_collections.api.update_flag_table_from_pricing_rule"},
	"Issue Type":{ "autoname": "art_collections.api.autoname_issue_type"},
	"Purchase Receipt": { "on_submit": "art_collections.api.stock_availability_notification"},
	"Sales Order":{"on_submit":"art_collections.api.sales_order_from_shopping_cart" },
	"Purchase Order":{
		"on_submit":["art_collections.api.purchase_order_convert_preorder_item" ,
		"art_collections.api.purchase_order_update_delivery_date_of_item" ],
		"on_update_after_submit":"art_collections.api.purchase_order_update_delivery_date_of_item"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"art_collections.tasks.all"
# 	],
# 	"daily": [
# 		"art_collections.tasks.daily"
# 	],
# 	"hourly": [
# 		"art_collections.tasks.hourly"
# 	],
# 	"weekly": [
# 		"art_collections.tasks.weekly"
# 	]
# 	"monthly": [
# 		"art_collections.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "art_collections.install.before_tests"

standard_portal_menu_items = [
	{"title": _("Manage Wish List Name"), "route": "/wish-list-name", "reference_doctype": "Wish List Name", "role": "Customer"}
]

# Overriding Whitelisted Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.shopping_cart.cart.update_cart": "art_collections.api.update_cart"
}
