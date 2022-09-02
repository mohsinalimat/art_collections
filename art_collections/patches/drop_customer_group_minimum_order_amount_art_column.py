import frappe

def execute():
  if frappe.db.exists("DocType", "Customer Group"):
    
    frappe.reload_doc("setup", "doctype", "customer_group")
    frappe.delete_doc_if_exists("Customer Group", "minimum_order_amount_art")
    frappe.delete_doc_if_exists("Custom Field", "Customer Group-minimum_order_amount_art")  