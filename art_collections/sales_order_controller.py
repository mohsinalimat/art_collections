from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_link_to_form

def sales_order_custom_validation(self,method):
	valiate_payment_terms_and_credit_limit_for_customer(self)


def valiate_payment_terms_and_credit_limit_for_customer(self):
	if self.customer:
		customer=frappe.get_doc('Customer',self.customer)	
		customer_credit_limit_found=False
		for credit in customer.credit_limits:
			if credit.credit_limit:
				customer_credit_limit_found=True
				break

		if customer_credit_limit_found==False and not customer.payment_terms:
			frappe.throw(_('There is no payment terms or credit limit defined for {0} customer. <br> Please set {1} to continue...'
			.format(frappe.bold(customer.customer_name),frappe.bold(get_link_to_form("Customer",self.customer)))))