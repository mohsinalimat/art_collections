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
from frappe.utils.xlsxutils import make_xlsx
from frappe.utils.csvutils import read_csv_content


@frappe.whitelist()
def import_items(docname, file_url, delivery_date):
    file_url, upload_data = get_import_template(docname, file_url, delivery_date)

    if not file_url:
        frappe.msgprint("Items import was not successful.")
        return

    # return

    import_log = None

    try:
        importer = Importer(
            "Sales Order", file_path=os.path.abspath(file_url), import_type=UPDATE
        )
        import_log = importer.import_data()
    except Exception:
        pass

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
    # file_path = os.path.abspath(import_file.get_full_path())
    # with open(file_path, "r") as csvfile:
    #     upload_data = read_csv_content(csvfile.read())

    upload_data = read_xlsx_file_from_attached_file(file_url=file_url)

    uoms = set([d[1] for d in upload_data[1:]])
    valid_uoms = [
        d[0]
        for d in frappe.db.sql(
            """select name from `tabUOM` where name in ({})""".format(
                ",".join(["%s"] * len(uoms))
            ),
            tuple(uoms),
        )
    ]

    # validate upload data
    warnings = []
    for idx, d in enumerate(upload_data[1:]):
        message = ""
        if not len([x for x in d if x]) in (3, 4):
            message = "Invalid data. Please specify Item Code, UOM and Quantity."
        if not d[1] in valid_uoms:
            message += "Invalid UOM: %s" % d[1]
        if message:
            warnings.append(
                {
                    "row": idx + 1,
                    "message": message,
                }
            )

    if warnings:
        print(warnings)
        make_error_file(docname, warnings, upload_data)
        return "", upload_data

    import_template = []

    HEADER = [
        "ID",
        "ID (Items)",
        "Item Code (Items)",
        "UOM (Items)",
        "Quantity (Items)",
        "Delivery Date (Items)",
        "ID (Sales Order Discountinued Items)",
        "Item Code (Sales Order Discountinued Items)",
        "Item Name (Sales Order Discountinued Items)",
        "Quantity (Sales Order Discountinued Items)",
        "Description (Sales Order Discountinued Items)",
    ]

    for d in frappe.db.sql(
        """
        select ti.item_code , ti.item_name, ti.description , ti.is_sales_item
        from tabItem ti where name in ({})
    """.format(
            ",".join(["%s"] * len(upload_data))
        ),
        tuple([d[0] for d in upload_data]),
        as_dict=True,
    ):
        line = [x for x in upload_data if frappe.utils.cstr(x[0]) == d.item_code]
        if line:
            line = line[0]
            if frappe.utils.cint(d.is_sales_item):
                import_template.append(
                    ["", ""] + line[0:3] + [line[3] or delivery_date] + [""] * 5
                )
            else:
                import_template.append(
                    [""] * 6 + ["", line[0], d.item_name, line[2], d.description]
                )

    if not import_template:
        frappe.throw("No valid Items to import.")

    import_template = [HEADER] + import_template

    import_template[1][0] = docname

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

    xlsx = make_xlsx(upload_data, "Errors")

    f = frappe.get_doc(
        doctype="File",
        attached_to_doctype="Sales Order",
        attached_to_name=docname,
        content=xlsx.getvalue(),
        file_name="sales_order_items_import_errors.xlsx",
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
