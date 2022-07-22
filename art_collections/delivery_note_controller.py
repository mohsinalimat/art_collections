from __future__ import unicode_literals
import frappe
import datetime
from frappe import _
from erpnext.selling.doctype.sales_order.sales_order import update_status
from frappe.utils import get_link_to_form


@frappe.whitelist()
def check_dn_has_unique_so_when_no_back_order_accepted(self,method):
    back_order_accepted = frappe.db.get_value('Customer', self.customer, 'back_order_accepted')
    against_all_so=[]
    if back_order_accepted==0:
        for item in  self.get("items"):
            if item.against_sales_order:
                against_all_so.append(item.against_sales_order)
        if len(against_all_so)>0:
            if len(set(against_all_so)) != 1:
                frappe.throw(_("When {0} is not allowed back order, there cannot be multiple sales orders {2}".format(self.customer,back_order_accepted)))