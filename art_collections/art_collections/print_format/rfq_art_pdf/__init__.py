# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe


def get_print_context(name, supplier):
    doc = frappe.get_doc("Request for Quotation", name)

    ctx = {"doc": doc.as_dict()}

    ctx["supplier_name"] = frappe.db.get_value(
        "Supplier", {"name": supplier}, "supplier_name"
    )

    for d in doc.suppliers:
        if d.supplier == supplier:
            ctx["supplier_contact"] = d.contact
            ctx["supplier_email_id"] = d.email_id

    ctx["items"] = list(
        frappe.db.sql(
            """
        select 
            i.item_name, 
            i.item_code, 
            tib.barcode,
            tis.supplier_part_no , 
            i.customs_tariff_number ,
            trfqi.qty, 
            trfqi.stock_uom 
        from `tabRequest for Quotation` trfq
        inner join `tabRequest for Quotation Item` trfqi on trfqi.parent = trfq.name
        inner join tabItem i on i.name = trfqi.item_code
        left outer join `tabItem Supplier` tis on tis.parent = i.item_code 
            and tis.supplier = %(supplier)s
        left outer join `tabItem Barcode` tib on tib.parent = i.name 
            and tib.idx  = (
                select min(idx) from `tabItem Barcode` tib2
                where parent = i.name
            )  
        where trfq.name = %(name)s
    """,
            dict(name=name, supplier=supplier),
            as_dict=True,
        )
    )

    return ctx
