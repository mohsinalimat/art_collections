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
                frappe.throw(_("When {0} is not allowed back order, there cannot be different sales orders {2}".format(self.customer,back_order_accepted)))

@frappe.whitelist()
def update_so_status_based_on_back_order_accepted(self,method):
    back_order_accepted = frappe.db.get_value('Customer', self.customer, 'back_order_accepted')
    if back_order_accepted==0:
        for item in  self.get("items"):
            so_name=item.against_sales_order
            print(so_name,'222')
            if so_name:
                print('inside if')
                per_delivered=frappe.db.get_value('Sales Order', so_name, 'per_delivered')
                status=frappe.db.get_value('Sales Order', so_name, 'status')
                docstatus=frappe.db.get_value('Sales Order', so_name, 'docstatus')
                # so=frappe.get_doc('Sales Order', so_name)
                # SO docstatus==1
                if method=='on_submit' and docstatus==1 and per_delivered <100 and (status!='Closed' or  status!='On Hold'):
                    update_status('Closed',so_name)
                    frappe.msgprint(_("Status changed to Closed for Sales Order {0} ").format(frappe.bold(get_link_to_form("Sales Order", so_name)), alert=True))  
                    return        
                #    DN cannot be cancelled if corresponding SO is in Closed or Hold status
                # elif method=='on_cancel' and docstatus==1  and status=='Closed': 
                #     print('closed')
                #     # doc.status === 'Closed'
                #     update_status('Draft',so_name)
                #     frappe.msgprint(_("Status changed to Draft for Sales Order {0} ").format(frappe.bold(get_link_to_form("Sales Order", so_name)), alert=True))
                #     return
            
    return