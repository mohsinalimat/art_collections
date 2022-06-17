# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe


def get_print_context(doctype, name):
    doc = frappe.get_doc(doctype, name)
    ctx = dict(doc={}, items=[])
    ctx["items"] = list(
        frappe.db.sql(
            """
            select 
                tpli.item_name , tpli.item_code , tpli.warehouse , sum(tpli.qty) qty ,
                tpli.uom , tpli.stock_uom , tpli.conversion_factor ,
                GROUP_CONCAT(DISTINCT tpli.sales_order) sales_order, 
                GROUP_CONCAT(DISTINCT tsoi.delivery_date) delivery_date, 
                case when tso.facing_required_art = 1 then 'Yes' else 'No' end facing_required_art ,
                GROUP_CONCAT(DISTINCT tso.po_no) po_no
            from `tabPick List` tpl 
            inner join `tabPick List Item` tpli on tpli.parent = tpl.name
            left outer join `tabSales Order Item` tsoi on tsoi.name = tpli.sales_order_item
            left outer join `tabSales Order` tso on tso.name = tsoi.parent
            where tpl.name = %(name)s   
            group by tpli.item_name , tpli.item_code , tpli.warehouse , tso.facing_required_art
    """,
            dict(name=name),
            as_dict=True,
        )
    )

    for d in ctx["items"]:
        d["warehouse"] = d["warehouse"][0:5]
        d["uom"] = "".join([x[0] for x in d["uom"].split(" ")])
        d["stock_uom"] = "".join([x[0] for x in d["stock_uom"].split(" ")])
        d["sales_order"] = ", ".join([x[-3:] for x in d["sales_order"].split(",")])
        d["delivery_date"] = ", ".join(
            [x[-5:].replace("-", "/") for x in d["delivery_date"].split(",")]
        )

    if ctx["items"] and ctx["items"][0].get("sales_order"):
        so = frappe.db.sql(
            """
        select 
            case when tso.facing_required_art = 1 then 'Yes' else 'No' end facing_required_art , po_no , 
            case when double_check_order_flag_art then 'Yes' else 'No' end  double_check_order_flag_art,
            tso.shipping_address_name , ta.address_line1 , ta.address_line2 , 
            ta.pincode , ta.city , ta.country 
        from `tabSales Order` tso 
        left outer join tabAddress ta on ta.name = tso.shipping_address_name 
        where tso.name = %(name)s
        """,
            dict(name=ctx["items"][0].get("sales_order")),
            as_dict=True,
        )
        if so:
            ctx["doc"] = so[0]

    return ctx
