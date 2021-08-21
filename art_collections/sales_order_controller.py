from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import get_link_to_form


def sales_order_custom_validation(self, method):
    valiate_payment_terms_and_credit_limit_for_customer(self)


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
