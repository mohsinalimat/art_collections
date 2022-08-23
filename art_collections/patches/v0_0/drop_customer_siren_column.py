import frappe

def execute():
  if frappe.db.exists("DocType", "Customer"):
    
    frappe.reload_doc("selling", "doctype", "customer")
    frappe.delete_doc_if_exists("Customer", "subledger_account")
    frappe.delete_doc_if_exists("Custom Field", "Customer-subledger_account")  

    frappe.reload_doc("selling", "doctype", "customer")
    frappe.delete_doc_if_exists("Customer", "naf")
    frappe.delete_doc_if_exists("Custom Field", "Customer-naf")   

    frappe.reload_doc("selling", "doctype", "customer")
    frappe.delete_doc_if_exists("Customer", "siret")
    frappe.delete_doc_if_exists("Custom Field", "Customer-siret")   

    frappe.reload_doc("selling", "doctype", "customer")
    frappe.delete_doc_if_exists("Customer", "siren")
    frappe.delete_doc_if_exists("Custom Field", "Customer-siren")  
    
   

  

   