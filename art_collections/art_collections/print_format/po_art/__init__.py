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
        select i.item_name, i.customer_code, tib.barcode, i.customs_tariff_number,
        tw.warehouse_name, poi.price_list_rate,  
        poi.net_rate, poi.net_amount, poi.description, poi.total_weight, 
        poi.qty, poi.image, po.overall_directive_art,
        coalesce(ucd.conversion_factor,0) * poi.qty nb_selling_packs_in_inner_art
        from `tabPurchase Order Item` poi
        inner join `tabPurchase Order` po on po.name = poi.parent
        left outer join tabWarehouse tw on tw.name = poi.warehouse 
        inner join tabItem i on i.name = poi.item_code
        left outer join `tabItem Barcode` tib on tib.parent = i.name and tib.idx = 1 
        left outer join `tabUOM Conversion Detail` ucd on ucd.parent = i.name 
            and ucd.parenttype='Item' and ucd.uom = (
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
