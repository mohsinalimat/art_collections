import frappe

def execute():
  if frappe.db.exists("DocType", "Website Item"):

    frappe.reload_doc("e_commerce", "doctype", "website_item")
    frappe.delete_doc_if_exists("Website Item", "copy_catalogue_item_cf")
    frappe.delete_doc_if_exists("Custom Field", "Website Item-copy_catalogue_item_cf")  