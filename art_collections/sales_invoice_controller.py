from __future__ import unicode_literals
import frappe
import datetime
from frappe import _

@frappe.whitelist()
def set_bank_account_for_customer(customer=None,shipping_address=None):
    if shipping_address:
        bank_account_based_on_shipping_address=frappe.db.sql("""SELECT link_name as bank_name FROM  `tabDynamic Link`
                        where parenttype ='Address' and link_doctype ='Bank Account' and parent = %(shipping_address)s""",
			            {"shipping_address": shipping_address},as_dict=True)
        if len(bank_account_based_on_shipping_address)>0:
            return bank_account_based_on_shipping_address[0].bank_name
    if customer:
        customer_default_bank_account=frappe.db.get_value('Customer', customer, 'default_bank_account')
        return customer_default_bank_account
    return None