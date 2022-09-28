import frappe

def execute():
  if frappe.db.exists("DocType", "Item"):

    frappe.reload_doc("stock", "doctype", "item")
    frappe.delete_doc_if_exists("Item", "website_item_events_art")
    frappe.delete_doc_if_exists("Custom Field", "Item-website_item_events_art")  

    frappe.reload_doc("stock", "doctype", "item")
    frappe.delete_doc_if_exists("Item", "max_qty_allowed_in_shopping_cart_art")
    frappe.delete_doc_if_exists("Custom Field", "Item-max_qty_allowed_in_shopping_cart_art")      

    frappe.reload_doc("stock", "doctype", "item")
    frappe.delete_doc_if_exists("Item", "website_item_flag_icon_art")
    frappe.delete_doc_if_exists("Custom Field", "Item-website_item_flag_icon_art")     

    frappe.reload_doc("stock", "doctype", "item")
    frappe.delete_doc_if_exists("Item", "allow_insufficient_images_for_web_art")
    frappe.delete_doc_if_exists("Custom Field", "Item-allow_insufficient_images_for_web_art")       

    frappe.reload_doc("website", "doctype", "website_slideshow")
    frappe.delete_doc_if_exists("Website Slideshow", "allow_insufficient_images_for_web_art")
    frappe.delete_doc_if_exists("Custom Field", "Website Slideshow-allow_insufficient_images_for_web_art")       



    