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
app_include_css = ["/assets/css/pos_list.min.css"]
app_include_js = "/assets/art_collections/js/art_collections.js"

# include js, css files in header of web template
web_include_css = "/assets/art_collections/css/art_collections.css"
web_include_js = ["/assets/art_collections/js/shopping_cart.js"]

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Customer": "public/js/customer.js",
    "Supplier": "public/js/supplier.js",
    "Address": "public/js/address.js",
    "Item": "public/js/item.js",
    "Delivery Note": "public/js/delivery_note.js",
    "Sales Order": "public/js/sales_order.js",
    "Quotation": "public/js/quotation.js",
    "Purchase Order": "public/js/purchase_order.js",
    "Issue": "public/js/issue.js",
    "Pricing Rule": "public/js/pricing_rule.js",
    "POS Profile": "public/js/pos_profile.js",
    "Supplier Quotation": "public/js/supplier_quotation.js",
    "Pick List": "public/js/pick_list.js",
    "Stock Entry": "public/js/stock_entry.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Website Item": "public/js/website_item.js",
    "Data Import": "public/js/data_import.js",
    "Purchase Receipt": "public/js/purchase_receipt.js",
    # "Request for Quotation": "public/js/request_for_quotation.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}

doctype_list_js = {"Sales Order": "public/js/sales_order_list.js"}

# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
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
after_migrate = "art_collections.migrations.after_migrations"

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
    "Website Item": {
        "on_change": "art_collections.website_item_controller.make_route_ascents_free",
        "validate": "art_collections.website_item_controller.make_route_ascents_free",
    },
    "Item": {
        "validate": "art_collections.item_controller.item_custom_validation",
        # "before_insert": "art_collections.item_controller.set_custom_item_name",
        "autoname": "art_collections.item_controller.set_item_code_for_pre_item",
    },
    "Pricing Rule": {
        "on_update": "art_collections.api.update_flag_table_from_pricing_rule"
    },
    "Issue Type": {"autoname": "art_collections.api.autoname_issue_type"},
    "Purchase Receipt": {
        "validate": "art_collections.directive_controller.get_directive",
        "on_submit": "art_collections.purchase_receipt_controller.purchase_receipt_custom_submit_logic",
        "before_cancel":"art_collections.purchase_receipt_controller.unlink_supplier_packing_list_from_purchase_receipt"
    },
    "Sales Order": {
        "validate": [
            "art_collections.sales_order_controller.sales_order_custom_validation",
            # "art_collections.sales_order_controller.update_total_saleable_qty",
            # "art_collections.directive_controller.get_directive",
        ],
        "on_submit": [
            "art_collections.api.sales_order_from_shopping_cart",
            "art_collections.controllers.excel.sales_order.on_submit_sales_order",
        ],
        # "on_update": [
        #     "art_collections.sales_order_controller.sales_order_custom_validation",
        # ],
    },
    "Purchase Order": {
        "on_submit": [
            "art_collections.purchase_order_controller.purchase_order_custom_on_submit",
            "art_collections.controllers.excel.purchase_order.on_submit_purchase_order",
        ],
        "on_update_after_submit": [
            "art_collections.purchase_order_controller.purchase_order_custom_on_submit"
            # "art_collections.purchase_order_controller.purchase_order_update_delivery_date_of_item",
            # "art_collections.purchase_order_controller.purchase_order_update_schedule_date_of_item",
        ],
        "validate": [
            "art_collections.purchase_order_controller.purchase_order_custom_validation",
            "art_collections.directive_controller.get_directive",
        ],
    },
    "Supplier Quotation": {
        "validate": [
            "art_collections.supplier_quotation_controller.supplier_quotation_custom_validation",
            "art_collections.directive_controller.get_directive",
        ]
    },
    "Request for Quotation": {
        "validate": [
            "art_collections.request_for_quotation_controller.request_for_quotation_custom_validation",
            "art_collections.directive_controller.get_directive",
        ],
        "on_submit": "art_collections.controllers.excel.request_for_quotation_excel.on_submit_request_for_quotation",
    },
    "Address": {
        "autoname": "art_collections.address_controller.set_address_title_based_on_customer",
        "validate": "art_collections.address_controller.fetch_default_mode_of_payment",
    },
    "Quotation": {
        "validate": "art_collections.directive_controller.get_directive",
        "on_submit": "art_collections.controllers.excel.quotation_excel.on_submit_quotation",
    },
    "Delivery Note": {
        "validate": "art_collections.directive_controller.get_directive",
        "on_submit": "art_collections.controllers.excel.delivery_note_excel.on_submit_delivery_note",
    },
    "Sales Invoice": {
        "validate": "art_collections.directive_controller.get_directive",
        "on_submit": "art_collections.controllers.excel.sales_invoice_excel.on_submit_sales_invoice",
    },
    "Purchase Invoice": {
        "validate": "art_collections.directive_controller.get_directive"
    },
    "Pick List": {"validate": "art_collections.directive_controller.get_directive"},
    "Data Import": {
        "validate": "art_collections.controllers.item_import.start_item_import"
    },
}

# Scheduled Tasks
# ---------------

scheduler_events = {
    # "all": [
    # 	"art_collections.tasks.all"
    # ],
    "cron": {
        "15 00 * * *": [
            "art_collections.item_controller.allow_order_still_stock_last",
        ]
    },
    "daily": ["art_collections.scheduler_task_controller.daily"]
    # "hourly": [
    # 	"art_collections.tasks.hourly"
    # ],
    # "weekly": [
    # 	"art_collections.tasks.weekly"
    # ]
    # "monthly": [
    # 	"art_collections.tasks.monthly"
    # ]
}

# Testing
# -------

# before_tests = "art_collections.install.before_tests"

standard_portal_menu_items = [
    {
        "title": _("Manage Wish List Name"),
        "route": "/wish-list-name",
        "reference_doctype": "Wish List Name",
        "role": "Customer",
    }
]

# Overriding Whitelisted Methods
# ------------------------------
#
override_whitelisted_methods = {
    " erpnext.e_commerce.shopping_cart.cart.update_cart": "art_collections.api.update_cart",
    "erpnext.e_commerce.shopping_cart.product_info.get_product_info_for_website": "art_collections.api.get_product_info_for_website",
}

fixtures = [
    {"dt": "Workflow", "filters": [["name", "in", ["BDC"]]]},
    {
        "dt": "Notification",
        "filters": [
            [
                "name",
                "in",
                [
                    "Payment Reminder For Escompte Eligible Customers",
                    "validate_inner_qty_for_sales_order",
                ],
            ]
        ],
    },
    {
        "dt": "Property Setter",
        "filters": [["name", "in", ["Sales Order-delivery_date-no_copy"]]],
    },
]

jenv = {
    "methods": [
        "get_print_context_for_art_collectons_sales_order:art_collections.art_collections.print_format.art_so.get_print_context",
        "get_print_context_for_art_collectons_purchase_order:art_collections.art_collections.print_format.po_art.get_print_context",
    ],
    "filters": [],
}
