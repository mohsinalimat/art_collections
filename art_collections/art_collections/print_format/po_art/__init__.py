# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import re
from io import BytesIO
import io
import openpyxl
import xlrd
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from frappe.utils import cint, get_site_url, get_url
import frappe


def get_print_context(name):
    doc = frappe.get_doc("Purchase Order", name)

    ctx = {"doc": {}}

    ctx["items"] = list(
        frappe.db.sql(
            """
        select 
            i.item_name, 
            i.item_code, 
            tib.barcode,
            poi.supplier_part_no , 
            i.customs_tariff_number ,
            poi.qty, 
            poi.stock_uom , 
            poi.base_net_rate , 
            poi.base_net_amount ,
            case when i.image is null then ''
                when SUBSTR(i.image,1,4) = 'http' then i.image
                else concat('{}/',i.image) end image
        from `tabPurchase Order Item` poi
        inner join `tabPurchase Order` po on po.name = poi.parent
        inner join tabItem i on i.name = poi.item_code
        left outer join `tabItem Barcode` tib on tib.parent = i.name 
            and tib.idx  = (
                select min(idx) from `tabItem Barcode` tib2
                where parent = i.name
            )
        left outer join `tabUOM Conversion Detail` ucd on ucd.parent = i.name 
            and ucd.parenttype='Item' 
            and ucd.uom = (
                select value from tabSingles
                where doctype like 'Art Collections Settings' 
                and field = 'inner_carton_uom' 
            )   
        where poi.parent = %(name)s
    """,
            dict(name=name),
            as_dict=True,
        )
    )

    ctx["has_discount"] = any(x.discount_amount for x in doc.items)

    shipping_cost = 0
    taxes_cost = 0
    for tax in doc.taxes:
        account_type = frappe.db.get_value("Account", tax.account_head, "account_type")
        if account_type == "Tax":
            taxes_cost += tax.base_tax_amount
        else:
            shipping_cost += tax.base_tax_amount
    ctx["shipping_cost"] = shipping_cost
    ctx["taxes_cost"] = taxes_cost

    return ctx
