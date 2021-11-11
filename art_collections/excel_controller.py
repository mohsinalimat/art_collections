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
from frappe.utils import cint, get_site_url
import frappe

ILLEGAL_CHARACTERS_RE = re.compile(r"[\000-\010]|[\013-\014]|[\016-\037]")

COL_MAP = {
    "your_ref": "Your Ref",
    "our_ref": "Our Ref",
    "excel_designation_cf": "designation",
    "description_1_cf": "Description 1",
    "description_2_cf": "Description 2",
    "description_3_cf": "Description 3",
    "other_language_cf": "Other Language",
    "genco": "GENCO",
    "nb_selling_packs_in_inner_art": "INNER",
    "packaging_description_cf": "Packaging Description",
}


def on_submit_purchase_order(doc, method=None):
    make_excel(doc.name, doc.doctype)


def on_submit_sales_order(doc, method=None):
    make_excel(doc.name, doc.doctype)


@frappe.whitelist()
def make_excel(docname=None, doctype=None):
    data = frappe.db.sql(
        """
        select 
            i.is_existing_product_cf,
            {your_ref} your_ref,
            i.item_code our_ref,
            i.excel_designation_cf,
            i.description_1_cf,
            i.description_2_cf,
            i.description_3_cf,
            i.other_language_cf,
            (select barcode from `tabItem Barcode` x where x.parent = i.name order by idx limit 1) genco,
            i.nb_selling_packs_in_inner_art,
            i.packaging_description_cf
        from 
        `tab{doctype}` dt
        inner join `tab{doctype} Item` dti on dti.parent = dt.name
        inner join tabItem i on i.name = dti.item_code
        where dt.name = %s
    """.format(
            your_ref=("dti.supplier_part_no" if doctype == "Purchase Order" else "''"),
            doctype=doctype,
        ),
        (docname,),
        as_dict=True,
        # debug=True,
    )

    existing_art_works = frappe.db.sql(
        """
    select 
        i.item_code,
        group_concat(concat(epaw.art_work_name,'||',epaw.art_work_attachment)) art_work
        from `tab{doctype}` dt
        inner join `tab{doctype} Item` dti on dti.parent = dt.name
        inner join tabItem i on i.name = dti.item_code
        inner join `tabExisting Product Art Work` epaw on epaw.parent = i.name
        where dt.name = %s
    group by i.name
    """.format(
            doctype=doctype
        ),
        (docname,),
        as_dict=True,
        # debug=True,
    )

    columns = [COL_MAP.get(col) for col, _ in data[0].items()][1:]

    site_url = get_site_url(frappe.local.site)

    # set the existing artworks for each item
    art_work_columns = []
    for d in existing_art_works:
        for row in filter(lambda x: x.our_ref == d.item_code, data):
            for tup in d.art_work.split(","):
                parts = tup.split("||")
                row[parts[0]] = f"{site_url}{parts[1]}"
                if not parts[0] in art_work_columns:
                    art_work_columns.append(parts[0])

    column_widths = [20, 20, 30, 30, 30, 20, 20, 15, 15, 30]

    wb = openpyxl.Workbook()
    # new
    product = [columns] + [
        list(d.values())[1:] for d in data if not cint(d.is_existing_product_cf)
    ]
    write_xlsx(product, "New Product", wb, column_widths)

    # existing
    product = [columns + art_work_columns] + [
        list(d.values())[1:] for d in data if cint(d.is_existing_product_cf)
    ]
    write_xlsx(product, "Existing Product", wb, column_widths)

    # make attachment
    out = io.BytesIO()
    wb.save(out)
    _file = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": "{}.xlsx".format(docname),
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
            "is_private": 1,
            "content": out.getvalue(),
        }
    )
    _file.save()
    frappe.db.commit()


def __write_xlsx(data, sheet_name, wb=None, column_widths=None, file_path=None):
    wb = Workbook()
    ws1 = wb.active
    ws1.title = "range names"
    for row in range(1, 40):
        ws1.append(range(600))
    ws2 = wb.create_sheet(title="Pi")
    ws2["F5"] = 3.14
    ws3 = wb.create_sheet(title="Data")
    for row in range(10, 20):
        for col in range(27, 54):
            _ = ws3.cell(
                column=col, row=row, value="{0}".format(get_column_letter(col))
            )
    print(ws3["AA10"].value)
    wb.save(filename=dest_filename)


def write_xlsx(data, sheet_name, wb=None, column_widths=None, file_path=None):
    # from xlsx utils with changes
    column_widths = column_widths or []
    if wb is None:
        wb = openpyxl.Workbook(write_only=True)

    ws = wb.create_sheet(sheet_name, 0)

    for i, column_width in enumerate(column_widths):
        if column_width:
            ws.column_dimensions[get_column_letter(i + 1)].width = column_width

    row1 = ws.row_dimensions[1]
    row1.font = Font(name="Calibri", bold=True)

    for idx, row in enumerate(data):
        clean_row = []
        print(row)
        for col, item in enumerate(row):
            value = item
            if isinstance(item, str) and next(
                ILLEGAL_CHARACTERS_RE.finditer(value), None
            ):
                # Remove illegal characters from the string
                value = re.sub(ILLEGAL_CHARACTERS_RE, "", value)

            if value:
                if isinstance(value, str) and value.startswith("http"):
                    _ = ws.cell(
                        column=col + 1, row=idx + 1, value=value.rsplit("/")[-1]
                    )
                    _.hyperlink = value
                else:
                    _ = ws.cell(column=col + 1, row=idx + 1, value=value)
