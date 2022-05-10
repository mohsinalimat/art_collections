from __future__ import unicode_literals
import frappe
import datetime
from frappe import _
from frappe.utils import get_link_to_form, flt
from art_collections.item_controller import get_stock_qty_for_saleable_warehouse
from art_collections.item_controller import get_qty_of_inner_cartoon


import re
from io import BytesIO
import io
import openpyxl
import xlrd
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from frappe.utils import cint, get_site_url, get_url
from art_collections.directive_controller import get_directive


def sales_order_custom_validation(self, method):
    if self.is_offline_art == 0:
        validate_minimum_order_amount_as_per_customer_group(self)
        valiate_payment_terms_and_credit_limit_for_customer(self)
        validate_inner_qty_and_send_notification(self)
        update_total_saleable_qty(self)
        get_directive(self,method)


def update_total_saleable_qty(self, method=None):
    for item in self.get("items"):
        total_saleable_qty = get_stock_qty_for_saleable_warehouse(item.item_code)
        if len(total_saleable_qty) > 0:
            item.total_saleable_qty_cf = total_saleable_qty[0].saleable_qty


def validate_inner_qty_and_send_notification(self):
    msg = ""

    for item in self.get("items"):
        raise_warning = False
        nb_selling_packs_in_inner_art = get_qty_of_inner_cartoon(item.item_code)
        if (
            (item.uom == item.stock_uom)
            and nb_selling_packs_in_inner_art
            and nb_selling_packs_in_inner_art > 0
        ):
            if item.qty >= nb_selling_packs_in_inner_art:
                allowed_selling_packs_in_inner = (
                    item.qty % nb_selling_packs_in_inner_art
                )
                if allowed_selling_packs_in_inner != 0:
                    raise_warning = True
            else:
                raise_warning = True
            if raise_warning == True:
                msg += "Row# : <b>{0}</b> : Item {1} : qty should be in multiples of <b>{2}</b> (inner selling packs). It is <b>{3}</b>".format(
                    item.idx, item.item_name, nb_selling_packs_in_inner_art, item.qty
                )
    if msg != "":
        print("-" * 100)
        print(msg)
        selling_pack_invalid_qty_so_notification = frappe.db.get_single_value(
            "Art Collections Settings", "selling_pack_invalid_qty_so_notification"
        )
        if selling_pack_invalid_qty_so_notification:
            send_email_via_custom_notification(
                selling_pack_invalid_qty_so_notification, self.name, msg
            )


def send_email_via_custom_notification(notification_name, doc_name, custom_message):
    from frappe.email.doctype.notification.notification import get_context
    import json

    notification = frappe.get_doc("Notification", notification_name)
    if notification.enabled == 1:
        doc = frappe.get_doc(notification.document_type, doc_name)

        context = get_context(doc)
        context = {"doc": doc, "alert": notification, "comments": None}
        if doc.get("_comments"):
            context["comments"] = json.loads(doc.get("_comments"))

        if notification.is_standard:
            notification.load_standard_properties(context)
        try:
            if notification.channel == "Email":
                send_an_email(notification, doc, context, custom_message)

            if (
                notification.channel == "System Notification"
                or notification.send_system_notification
            ):
                create_system_notification(notification, doc, context)

        except:
            frappe.log_error(
                title="Failed to send notification", message=frappe.get_traceback()
            )


def send_an_email(notification, doc, context, custom_message):
    from email.utils import formataddr
    from frappe.core.doctype.communication.email import make as make_communication

    subject = notification.subject
    if "{" in subject:
        subject = frappe.render_template(notification.subject, context)

    attachments = notification.get_attachment(doc)
    recipients, cc, bcc = notification.get_list_of_recipients(doc, context)
    if not (recipients or cc or bcc):
        return

    sender = None
    message = (
        frappe.render_template(notification.message, context) + "\n" + custom_message
    )
    if notification.sender and notification.sender_email:
        sender = formataddr((notification.sender, notification.sender_email))

    frappe.sendmail(
        recipients=recipients,
        subject=subject,
        sender=sender,
        cc=cc,
        bcc=bcc,
        message=message,
        reference_doctype=doc.doctype,
        reference_name=doc.name,
        attachments=attachments,
        expose_recipients="header",
        print_letterhead=(
            (attachments and attachments[0].get("print_letterhead")) or False
        ),
    )

    # Add mail notification to communication list
    # No need to add if it is already a communication.
    if doc.doctype != "Communication":
        make_communication(
            doctype=doc.doctype,
            name=doc.name,
            content=message,
            subject=subject,
            sender=sender,
            recipients=recipients,
            communication_medium="Email",
            send_email=False,
            attachments=attachments,
            cc=cc,
            bcc=bcc,
            communication_type="Automated Message",
            ignore_permissions=True,
        )


def create_system_notification(notification, doc, context):
    from frappe.desk.doctype.notification_log.notification_log import (
        enqueue_create_notification,
    )
    import json

    subject = notification.subject
    if "{" in subject:
        subject = frappe.render_template(notification.subject, context)

    attachments = notification.get_attachment(doc)

    recipients, cc, bcc = notification.get_list_of_recipients(doc, context)

    users = recipients + cc + bcc

    if not users:
        return

    notification_doc = {
        "type": "Alert",
        "document_type": doc.doctype,
        "document_name": doc.name,
        "subject": subject,
        "from_user": doc.modified_by or doc.owner,
        "email_content": frappe.render_template(notification.message, context),
        "attached_file": attachments and json.dumps(attachments[0]),
    }
    enqueue_create_notification(users, notification_doc)


def validate_minimum_order_amount_as_per_customer_group(self):
    if self.customer:
        customer = frappe.get_doc("Customer", self.customer)
        customer_group = frappe.db.get_value(
            "Customer", self.customer, "customer_group"
        )
        if customer_group:
            minimum_order_amount_art = frappe.db.get_value(
                "Customer Group", customer_group, "minimum_order_amount_art"
            )
            if (
                minimum_order_amount_art
                and self.base_net_total < minimum_order_amount_art
            ):

                msg=_(
                        "For customer group {0} minimum order amount required is {1}.<br>The sales order amount is {2}. Please set higher order value and continue...".format(
                            frappe.bold(customer_group),
                            frappe.bold(minimum_order_amount_art),
                            frappe.bold(self.base_net_total),
                        )
                    )
                
                frappe.msgprint(msg= msg,title= _('Minimum Order Amount Alert'),indicator= 'orange', alert=False)


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


@frappe.whitelist()
def get_item_details(item_code, qty):
    item = frappe.db.sql(
        """select is_sales_item,item_code, item_name, stock_uom,  description, item_group,rate
        from `tabItem` where name = %s""",
        item_code,
        as_dict=1,
    )
    return {
        "is_sales_item": item and item[0]["is_sales_item"] or 0,
        "item_code": item and item[0]["item_code"] or "",
        "qty": qty or 1,
        "rate": item[0]["rate"] or 0,
        "item_name": item and item[0]["item_name"] or "",
        "uom": item and item[0]["stock_uom"] or "",
        "description": item and item[0]["description"] or "",
        "item_group": item and item[0]["item_group"] or "",
    }

@frappe.whitelist()
def get_shipping_rule(country):
    return frappe.db.sql("""select sr.name from `tabShipping Rule` sr inner join `tabShipping Rule Country` sr_country 
    on sr.name=sr_country.parent where sr.disabled=0 and sr_country.country=%s order by sr.creation DESC  limit 1""",country,as_dict=1,debug=1)