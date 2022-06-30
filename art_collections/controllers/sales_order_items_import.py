# -*- coding: utf-8 -*-
# Copyright (c) 2022, GreyCube Technologies and Contributors
# See license.txt

from email import message
import frappe
from frappe import _
from frappe.utils.csvutils import to_csv
from frappe.utils import flt, get_date_str
from frappe.core.doctype.data_import.importer import Importer, UPDATE
import os, io
from openpyxl import load_workbook
from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file


@frappe.whitelist()
def import_items(docname, file_url, delivery_date):

    file_url, upload_data = get_import_template(docname, file_url, delivery_date)

    if not file_url:
        frappe.msgprint("Items import was not successful.")
        return

    importer = Importer(
        "Sales Order", file_path=os.path.abspath(file_url), import_type=UPDATE
    )
    import_log = importer.import_data()

    if import_log and import_log[0].get("success"):
        frappe.msgprint(_("Items imported successfully."))

    elif not import_log or not import_log[0].get("success"):
        warnings = importer.import_file.get_warnings()
        if warnings:
            make_error_file(docname, warnings, upload_data)
        elif import_log[0].get("messages"):
            frappe.msgprint(import_log[0].get("messages"))
        else:
            frappe.msgprint(import_log[0].get("exception"))


def get_import_template(docname, file_url, delivery_date):
    upload_data, import_template = [], []

    import_file = frappe.get_doc("File", {"file_url": file_url})
    file_path = os.path.abspath(import_file.get_full_path())

    # with open(file_path, "r") as csvfile:
    #     upload_data = read_csv_content(csvfile.read())

    upload_data = read_xlsx_file_from_attached_file(file_url=file_url)

    # validate upload data
    warnings = []
    for idx, d in enumerate(upload_data):
        if not len([x for x in d if x]) in (3, 4):
            warnings.append(
                {
                    "row": idx + 1,
                    "message": "Invalid data. Please specify Item Code, UOM and Quantity.",
                }
            )

    if warnings:
        make_error_file(docname, warnings, upload_data)
        return "", upload_data

    HEADER = "ID,ID (Items),Item Code (Items),UOM (Items),Quantity (Items),Delivery Date (Items)"

    # modify file to add delivery date and SO#
    import_template.append(HEADER.split(","))

    # first row has SO name
    import_template.append(["%s" % docname, ""] + upload_data[1])
    for d in upload_data[2:]:
        import_template.append(["", ""] + d)

    for d in import_template[1:]:
        if not d[-1]:
            d[-1] = delivery_date

    # print(import_template)

    f = frappe.get_doc(
        doctype="File",
        content=to_csv(import_template),
        file_name="sales_order_items_import %s.csv" % frappe.generate_hash("", 6),
        is_private=1,
        # attached_to_doctype="Sales Order",
        # attached_to_name=docname,
    )

    f.save(ignore_permissions=True)

    frappe.db.commit()

    return f.file_url, upload_data


def make_error_file(docname, warnings, upload_data):

    message = _("Please check the error file.<br>") + "<br>".join(
        [m.get("message") for m in [d for d in warnings if d.get("col")]]
    )

    errors = [
        (d.get("row"), d.get("message", "").replace("<b>", "").replace("</b>", ""))
        for d in warnings
        if d.get("row")
    ]

    ERROR_HEADER = _("Error. Please remove this column before re-uploading.")

    HEADER = "Item Code (Items),UOM (Items),Quantity (Items),Delivery Date (Items)"

    upload_data = [HEADER.split(",") + [ERROR_HEADER]] + upload_data[1:]

    for idx, err in errors:
        upload_data[idx - 1] = upload_data[idx - 1] + [err]

    f = frappe.get_doc(
        doctype="File",
        attached_to_doctype="Sales Order",
        attached_to_name=docname,
        content=to_csv(upload_data),
        file_name="sales_order_items_import_errors.csv",
        is_private=1,
    )

    f.save(ignore_permissions=True)

    frappe.msgprint(message)


@frappe.whitelist()
def download_sales_order_items_upload_template():
    template_path = frappe.get_app_path(
        "art_collections", "controllers", "sales_order_item_import_template.xlsx"
    )

    template = load_workbook(template_path)

    out = io.BytesIO()
    template.save(out)
    frappe.response["filename"] = _("Sales Order Item Import Template") + ".xlsx"
    frappe.response["filecontent"] = out.getvalue()
    frappe.response["type"] = "binary"
