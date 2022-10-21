# import frappe

# def execute():
#   if frappe.db.exists("DocType", "Supplier"):
    
#     frappe.reload_doc("buying", "doctype", "supplier")
#     frappe.delete_doc_if_exists("Supplier", "subledger_account")
#     frappe.delete_doc_if_exists("Custom Field", "Supplier-subledger_account")  

#     frappe.reload_doc("buying", "doctype", "supplier")
#     frappe.delete_doc_if_exists("Customer", "naf")
#     frappe.delete_doc_if_exists("Custom Field", "Customer-naf")   

#     frappe.reload_doc("buying", "doctype", "supplier")
#     frappe.delete_doc_if_exists("Customer", "siret")
#     frappe.delete_doc_if_exists("Custom Field", "Customer-siret")   

#     frappe.reload_doc("buying", "doctype", "supplier")
#     frappe.delete_doc_if_exists("Customer", "siren")
#     frappe.delete_doc_if_exists("Custom Field", "Customer-siren")  