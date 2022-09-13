# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils.print_format import download_pdf as frappe_download_pdf
from frappe.utils.pdf import cleanup, get_pdf


def get_print_context(doctype, name):
    doc = frappe.get_doc(doctype, name)
    ctx = dict(doc={}, items=[])
    ctx["items"] = list(
        frappe.db.sql(
            """
            select 
                substring(tpli.item_name , 1, 40) item_name ,
                substring(tpli.warehouse , 1, 5) warehouse ,
                substring(COALESCE(tpli.sales_order,'') , -3) sales_order ,
                DATE_FORMAT(tsoi.delivery_date, '%%d/%%m') delivery_date ,
                substring(tso.po_no , 1, 20) po_no ,
                tpli.item_code , tpli.qty , tpli.sales_order sales_order_name ,
                tpli.uom , tpli.stock_uom , tpli.conversion_factor ,
                case when tso.facing_required_art = 1 then 'Y' else 'N' end facing_required_art 
            from `tabPick List` tpl 
            inner join `tabPick List Item` tpli on tpli.parent = tpl.name
            left outer join `tabSales Order Item` tsoi on tsoi.name = tpli.sales_order_item
            left outer join `tabSales Order` tso on tso.name = tsoi.parent
            where tpl.name = %(name)s   
            order by tpli.warehouse , tpli.item_name , tsoi.delivery_date 
    """,
            dict(name=name),
            as_dict=True,
        )
    )

    for d in ctx["items"]:
        d["uom"] = "".join([x[0] for x in d["uom"].split(" ")])
        d["stock_uom"] = "".join([x[0] for x in d["stock_uom"].split(" ")])

    if ctx["items"] and ctx["items"][0].get("sales_order_name"):
        so = frappe.db.sql(
            """
        select 
            case when tso.facing_required_art = 1 then 'Yes' else 'No' end facing_required_art , po_no , 
            case when double_check_order_flag_art then 'Yes' else 'No' end  double_check_order_flag_art,
            tso.shipping_address_name , ta.address_line1 , ta.address_line2 , 
            ta.pincode , ta.city , ta.country 
        from `tabSales Order` tso 
        left outer join tabAddress ta on ta.name = tso.shipping_address_name 
        where tso.name = %(so_name)s
        """,
            dict(so_name=ctx["items"][0].get("sales_order_name")),
            as_dict=True,
        )
        if so:
            ctx["doc"] = so[0]

    return ctx


@frappe.whitelist()
def download_pdf(doctype, name, format=None, doc=None, no_letterhead=0):
    if not format == "Art SI" and doctype in (
        "Pick List",
        "Sales Order",
        "Delivery Note",
        "Sales Invoice",
    ):
        """
        Overriding default in order to set pdf options to wkhtmltopdf for custom margin
        Frappe should provide a way to set wkhtmltopdf flags https://wkhtmltopdf.org/usage/wkhtmltopdf.txt
        """
        html = frappe.get_print(
            doctype, name, format, doc=doc, no_letterhead=no_letterhead
        )
        frappe.local.response.filename = "{name}.pdf".format(
            name=name.replace(" ", "-").replace("/", "-")
        )
        frappe.local.response.filecontent = get_pdf(
            html,
            options={
                "margin-left": "8mm",
                "margin-right": "8mm",
                "margin-top": "8mm",
                "margin-bottom": "8mm",
            },
        )
        frappe.local.response.type = "pdf"
    else:
        return frappe_download_pdf(doctype, name, format, doc, no_letterhead)
