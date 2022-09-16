import frappe

def execute():
  if frappe.db.exists("DocType", "Item"):

    frappe.reload_doc("stock", "doctype", "item")
    frappe.delete_doc_if_exists("Item", "web_long_description")
    frappe.delete_doc_if_exists("Custom Field", "Item-web_long_description-hidden")     