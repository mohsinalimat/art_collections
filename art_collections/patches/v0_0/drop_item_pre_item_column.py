import frappe

def execute():
  if frappe.db.exists("DocType", "Item"):

    frappe.reload_doc("stock", "doctype", "item")
    frappe.delete_doc_if_exists("Item", "pre_item_naming_series_art")
    frappe.delete_doc_if_exists("Custom Field", "Item-pre_item_naming_series_art")  

    frappe.reload_doc("stock", "doctype", "item")
    frappe.delete_doc_if_exists("Item", "is_pre_item_art")
    frappe.delete_doc_if_exists("Custom Field", "Item-is_pre_item_art")      