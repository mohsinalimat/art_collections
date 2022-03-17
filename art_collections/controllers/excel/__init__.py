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


ILLEGAL_CHARACTERS_RE = re.compile(r"[\000-\010]|[\013-\014]|[\016-\037]")


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


def sample_write_xlsx(data, sheet_name, wb=None, column_widths=None, file_path=None):
    wb = openpyxl.Workbook()
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
    wb.save(filename="dest_filename")


def attach_file(content, **args):
    _file = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": "{}.xlsx".format(args.get("docname")),
            "attached_to_doctype": args.get("doctype"),
            "attached_to_name": args.get("docname"),
            "is_private": 1,
            "content": content,
        }
    )
    _file.save()
    frappe.db.commit()
    frappe.publish_realtime(
        "show_sales_order_email_dialog", {"user": frappe.session.user}
    )
