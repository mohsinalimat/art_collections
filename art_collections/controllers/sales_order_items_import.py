# -*- coding: utf-8 -*-
# Copyright (c) 2022, GreyCube Technologies and Contributors
# See license.txt

import frappe
from frappe import _
from frappe.utils.csvutils import read_csv_content, to_csv
from frappe.utils import flt, get_date_str
from frappe.core.doctype.data_import.importer import Importer, UPDATE
import os


@frappe.whitelist()
def import_items(docname, file_url, delivery_date):

    import_file = frappe.get_doc("File", {"file_url": file_url})
    file_path = os.path.abspath(import_file.get_full_path())

    upload_data, import_template = [], []

    import_template.append(
        [
            "ID",
            "ID (Items)",
            "Item Code (Items)",
            "UOM (Items)",
            "Quantity (Items)",
            "Delivery Date (Items)",
        ]
    )

    # modify file to add delivery date and so name
    with open(file_path, "r") as csvfile:
        upload_data = read_csv_content(csvfile.read())
        import_template.append(["%s" % docname, ""] + upload_data[1])
        for d in upload_data[2:]:
            import_template.append(["", ""] + d)

    for d in import_template:
        if len(d) == 5:
            d.append(delivery_date)

    f = frappe.get_doc(
        doctype="File",
        # attached_to_doctype="Sales Order",
        # attached_to_name=docname,
        content=to_csv(import_template),
        file_name="sales_order_items_import %s.csv" % frappe.generate_hash("", 6),
        is_private=1,
    )

    f.save(ignore_permissions=True)

    importer = Importer(
        "Sales Order", file_path=os.path.abspath(f.file_url), import_type=UPDATE
    )
    import_log = importer.import_data()

    if import_log and import_log[0].get("success"):
        frappe.msgprint(_("Items imported successfully."))

    elif not import_log or import_log[0].get("success"):
        message = _("Please check the error file.")
        warnings = importer.import_file.get_warnings()
        for d in warnings:
            if d.get("row"):
                if len(upload_data[d.get("row") - 1]) == 3:
                    upload_data[d.get("row") - 1] = upload_data[d.get("row") - 1] + [
                        "",
                        d.get("message"),
                    ]
                else:
                    upload_data[d.get("row") - 1] = upload_data[d.get("row") - 1] + [
                        d.get("message")
                    ]
            else:
                message = message + d.get("message") + "<br>"

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

    return ""
