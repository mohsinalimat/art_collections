import frappe


def execute():
    frappe.reload_doc("art_collections", "doctype", "catalogue_directory_art_item_detail")
    frappe.db.sql("""UPDATE  `tabCatalogue Directory Art Item Detail` set catalog_type='Permanent' where catalog_type='Permanant' """)