import frappe

def execute():
  if frappe.db.exists("DocType", "Supplier"):

    frappe.reload_doc("buying", "doctype", "supplier")
    frappe.delete_doc_if_exists("Supplier", "default_terms_and_conditions_art")
    frappe.delete_doc_if_exists("Custom Field", "Supplier-default_terms_and_conditions_art")   

    frappe.reload_doc("buying", "doctype", "supplier")
    frappe.delete_doc_if_exists("Supplier", "is_product_supplier")
    frappe.delete_doc_if_exists("Custom Field", "Supplier-is_product_supplier")       
    
    frappe.reload_doc("buying", "doctype", "supplier")
    frappe.delete_doc_if_exists("Supplier", "subledger_account")
    frappe.delete_doc_if_exists("Custom Field", "Supplier-subledger_account")  

#     frappe.reload_doc("buying", "doctype", "supplier")
#     frappe.delete_doc_if_exists("Customer", "naf")
#     frappe.delete_doc_if_exists("Custom Field", "Customer-naf")   

#     frappe.reload_doc("buying", "doctype", "supplier")
#     frappe.delete_doc_if_exists("Customer", "siret")
#     frappe.delete_doc_if_exists("Custom Field", "Customer-siret")   

#     frappe.reload_doc("buying", "doctype", "supplier")
#     frappe.delete_doc_if_exists("Customer", "siren")
#     frappe.delete_doc_if_exists("Custom Field", "Customer-siren")  