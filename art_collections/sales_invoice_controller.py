from __future__ import unicode_literals
import frappe
import datetime
from frappe import _
from erpnext.selling.doctype.sales_order.sales_order import update_status
from frappe.utils import get_link_to_form

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

@frappe.whitelist()
def update_so_status_based_on_back_order_accepted(self,method):
    for item in  self.get("items"):
        so_name=item.sales_order
        if so_name:
            back_order_accepted = frappe.db.get_value('Sales Order', so_name, 'back_order_accepted_art')
            per_delivered = frappe.db.get_value('Sales Order', so_name, 'per_delivered')
            status = frappe.db.get_value('Sales Order', so_name, 'status')
            docstatus=frappe.db.get_value('Sales Order', so_name, 'docstatus')
            if method=='on_submit' and back_order_accepted==0 and docstatus==1  and per_delivered<100 and (status!='Closed' or  status!='On Hold'):
                update_status('Closed',so_name)
                frappe.msgprint(_("Status changed to Closed for Sales Order {0} ").format(frappe.bold(get_link_to_form("Sales Order", so_name)), alert=True))  
                return
            elif method=='before_cancel' and docstatus==1  and status=='Closed': 
                update_status('Draft',so_name)
                frappe.msgprint(_("Sales Order {0} is re-opened.").format(frappe.bold(get_link_to_form("Sales Order", so_name)), alert=True))
                return                
    return    