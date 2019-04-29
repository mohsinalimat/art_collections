from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import sanitize_html

@frappe.whitelist()
def get_sales_person_based_on_address(address=None):
    if address:
        address=sanitize_html(address)
        print address
        sales_person=frappe.db.sql("""select territory.territory_manager as sales_person
from `tabAddress` as address
inner join `tabTerritory` as territory
on address.territory=territory.name
where address.name=%s""",address,as_dict=True)
        return sales_person[0] if sales_person else None
    else:
        return None