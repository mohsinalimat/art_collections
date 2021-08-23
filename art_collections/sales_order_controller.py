from __future__ import unicode_literals
import frappe
import datetime
from frappe import _
from frappe.utils import get_link_to_form


def sales_order_custom_validation(self, method):
    validate_minimum_order_amount_as_per_customer_group(self)
    valiate_payment_terms_and_credit_limit_for_customer(self)

def validate_minimum_order_amount_as_per_customer_group(self):
    if self.customer:
        customer = frappe.get_doc("Customer", self.customer)
        customer_group=frappe.db.get_value("Customer", self.customer, 'customer_group')
        if customer_group:
            minimum_order_amount_art=frappe.db.get_value("Customer Group", customer_group, 'minimum_order_amount_art')
            if minimum_order_amount_art and self.base_net_total<minimum_order_amount_art:
               frappe.throw(
                _(
                    "For customer group {0} minimum order amount required is {1}.<br>The sales order amount is {2}. Please set higher order value to continue...".format(
                        frappe.bold(customer_group),
                         frappe.bold(minimum_order_amount_art),
                         frappe.bold(self.base_net_total)
                    )
                )
            )             

def valiate_payment_terms_and_credit_limit_for_customer(self):
    if self.customer:
        customer = frappe.get_doc("Customer", self.customer)
        customer_credit_limit_found = False
        for credit in customer.credit_limits:
            if credit.credit_limit:
                customer_credit_limit_found = True
                break

        if customer_credit_limit_found == False and not customer.payment_terms:
            frappe.throw(
                _(
                    "There is no payment terms or credit limit defined for {0} customer. <br> Please set {1} to continue...".format(
                        frappe.bold(customer.customer_name),
                        frappe.bold(get_link_to_form("Customer", self.customer)),
                    )
                )
            )


@frappe.whitelist()
def make_sales_invoice(names):
    import json
    from six import string_types

    if isinstance(names, string_types):
        names = json.loads(names)

    if len(names) == 0:
        frappe.throw(_("At least one order has to be selected."))

    validate_billed(names)
    from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

    for name in names:
        for d in frappe.db.get_all("Sales Order", {"name": name, "docstatus": 1}):
            si = make_sales_invoice(d.name)
            si = si.insert()
            for item in si.get("payment_schedule"):
                if isinstance(item.get("due_date"), datetime.date):
                    item.due_date = item.get("due_date").strftime("%Y-%m-%d")
            si.submit()


def validate_billed(names):
    billed = [
        d.name
        for d in frappe.db.get_all(
            "Sales Order",
            {"name": ["in", names], "docstatus": 1, "per_billed": [">", 0]},
        )
    ]
    if billed:
        frappe.throw(
            "Sales Orders {} have already been billed.".format(
                frappe.bold(",".join(billed))
            )
        )
