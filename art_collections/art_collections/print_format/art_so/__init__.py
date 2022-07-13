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


# sales order print format
def get_print_context(name):
    doc = frappe.get_doc("Sales Order", name)

    ctx = {"doc": {}}

    ctx["items"] = list(
        frappe.db.sql(
            """
        select 
            i.item_name, 
            i.item_code,
            i.customer_code, 
            tib.barcode,
            soi.uom,
            soi.stock_uom, 
            soi.qty, 
            soi.stock_qty , 
            soi.base_net_rate , 
            soi.base_net_amount , 
            tip.price_list_rate , 
            i.customs_tariff_number ,
            soi.conversion_factor ,
            if(soi.total_saleable_qty_cf <= soi.stock_qty,1,0) in_stock ,
            case when soi.image is null then ''
                when SUBSTR(soi.image,1,4) = 'http' then soi.image
                else concat('{}/',soi.image) end image
        from 
            `tabSales Order Item` soi
        inner join `tabSales Order` so on so.name = soi.parent
        inner join tabItem i on i.name = soi.item_code
        left outer join `tabItem Barcode` tib on tib.parent = i.name 
            and tib.idx  = (
                select min(idx) from `tabItem Barcode` tib2
                where parent = i.name
            )       
        left outer join `tabItem Price` tip 
        on tip.item_code = soi.item_code and tip.uom = soi.stock_uom 
        and tip.price_list = (
            select value from tabSingles ts
            where doctype = 'Selling Settings' 
            and field = 'selling_price_list'
        )
        where 
            soi.parent = %(name)s
    """.format(
                get_url()
            ),
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
