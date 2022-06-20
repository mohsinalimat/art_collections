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
                tpri.item_code , tpri.item_name , 
                sum(tsplda.qty_of_outer) qty_of_outer, 
                sum(tsplda.qty_of_outer) /coalesce(tucd.conversion_factor ,1) pallet_qty
                from `tabPurchase Receipt` tpr 
            inner join `tabPurchase Receipt Item` tpri on tpri.parent = tpr.name 
            left outer join `tabUOM Conversion Detail` tucd on tucd.parent = tpri.item_code and tucd.uom = (
                select value from tabSingles ts
                where doctype = 'Art Collections Settings' and field = 'pallet_uom'
            )
            left outer join `tabSupplier Packing List Detail Art` tsplda on tsplda.purchase_order = tpri.purchase_order 
                and tsplda.po_item_code = tpri.purchase_order_item 
            where tpr.name = %(name)s
            group by tpri.item_code , tpri.item_name 
    """,
            dict(name=name),
            as_dict=True,
        )
    )

    return ctx
