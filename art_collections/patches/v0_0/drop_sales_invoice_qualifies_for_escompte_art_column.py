import frappe

def execute():
  if frappe.db.exists("DocType", "Sales Invoice"):
    
    frappe.reload_doc("accounts", "doctype", "sales_invoice")
    frappe.delete_doc_if_exists("Sales Invoice", "qualifies_for_escompte_art")
    frappe.delete_doc_if_exists("Custom Field", "Sales Invoice-qualifies_for_escompte_art")  