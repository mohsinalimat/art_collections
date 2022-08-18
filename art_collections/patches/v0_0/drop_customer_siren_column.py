import frappe

def execute():
  pass
  # if frappe.db.exists("DocType", "Customer"):
  #   frappe.reload_doc("selling", "doctype", "customer")
  #   if "siren" in frappe.db.get_table_columns("Customer"):
  #     frappe.db.sql("alter table `tabCustomer` drop column siren")
  #   frappe.delete_doc_if_exists("Custom Field", "Customer-siren")  