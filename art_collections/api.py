from __future__ import unicode_literals
import frappe
from frappe import _
import functools

@frappe.whitelist()
def get_sales_person_based_on_address(address=None):
    if address:
        sales_person=frappe.db.sql("""select territory.territory_manager as sales_person
from `tabAddress` as address
inner join `tabTerritory` as territory
on address.territory=territory.name
where address.name=%s""",address,as_dict=True)
        return sales_person[0] if sales_person else None
    else:
        return None

@frappe.whitelist()
def get_address_list(name,doctype):
        filters = [
                ["Dynamic Link", "link_doctype", "=", doctype],
                ["Dynamic Link", "link_name", "=", name],
                ["Dynamic Link", "parenttype", "=", "Address"],
        ]
        address_list = frappe.get_all("Address", filters=filters, fields=["*"])

        address_list = sorted(address_list,
                key = functools.cmp_to_key(lambda a, b:
                        (int(a.is_primary_address - b.is_primary_address)) or
                        (1 if a.modified - b.modified else 0)), reverse=True)
        return address_list if address_list else None