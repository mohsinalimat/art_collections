# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

from attr import field, fields
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now
import json
from art_collections.controllers.excel import write_xlsx, attach_file, add_images
import openpyxl
import io


class PhotoQuotation(Document):
    @frappe.whitelist()
    def get_lead_items(self, conditions=None):
        columns = get_lead_item_fields()

        data = frappe.db.sql(
            """select {} from `tabLead Item` where photo_quotation = %s {}""".format(
                ", ".join([d.fieldname for d in columns]),
                conditions and " and %s" % conditions or "",
            ),
            (self.name,),
        )

        return {"columns": columns, "data": data}

    @frappe.whitelist()
    def update_lead_items(self, items=[]):
        fields = [d.fieldname for d in get_lead_item_fields()]
        for d in items:
            if not d[0]:
                continue
            doc = frappe.get_doc("Lead Item", d[0])
            doc.update(dict(zip(fields, d)))
            doc.save()

    @frappe.whitelist()
    def get_supplier_email(self, template="all"):
        items_xlsx = []
        # make supplier file and attach to PQ doc
        content = get_items_xlsx(self.name, template, with_xlsx_template=1)

        recipients = frappe.db.sql(
            """
        select 
            tce.email_id 
            from `tabContact Email` tce 
            inner join `tabDynamic Link` tdl on tdl.parent = tce.parent 
            and tdl.link_doctype = 'Supplier' and tce.is_primary = 1
            and tdl.link_name = %s
        """,
            (self.supplier,),
        )
        if not recipients:
            # supplier email ? create contact etc like rfq??
            frappe.throw("Please create a Contact for Supplier.")

        # create doc attachment and open email dialog in client

        attach_file(
            content,
            doctype=self.doctype,
            docname=self.name,
            recipients=recipients[0][0],
            file_name=get_file_name(self.name, template),
            email_template=EMAIL_TEMPLATES.get(template),
        )


def get_file_name(name, template):
    return "{}-{}-{}.xlsx".format(
        name,
        frappe.unscrub(template),
        now()[:16].replace(" ", "-").replace(":", ""),
    )


def get_lead_item_fields():
    return [
        frappe._dict(
            {
                "fieldname": "name",
                "label": "Lead Item#",
                "fieldtype": "text",
            }
        )
    ] + frappe.db.sql(
        """
            select fieldname , label , 
            case 
                when fieldtype = 'Attach Image' then 'image'
                when fieldtype in ('Percent', 'Int', 'Currency') then 'numeric' 
                when fieldtype in ('Check') then 'checkbox'
                when fieldtype in ('Date') then 'calendar'
            else 'text' end fieldtype 
            from tabDocField tdf where parent = 'Lead Item' 
            and label is not null
            and fieldname not in ('naming_series' ,'amended_from')
            order by idx;
    """,
        as_dict=True,
    )


@frappe.whitelist()
def import_lead_item_photos():
    docname = frappe.form_dict.docname
    folder = frappe.form_dict.folder or "Home"

    doc = frappe.get_doc(
        {"doctype": "Lead Item", "uom": "Selling Pack", "photo_quotation": docname}
    )

    doc.insert(ignore_permissions=True)

    ret = frappe.get_doc(
        {
            "doctype": "File",
            "attached_to_doctype": doc.doctype,
            "attached_to_name": doc.name,
            "attached_to_field": "item_photo",
            "folder": folder,
            "file_name": frappe.local.uploaded_filename,
            "file_url": frappe.form_dict.file_url,
            "is_private": 0,
            "content": frappe.local.uploaded_file,
        }
    )
    ret.save(ignore_permissions=True)
    doc.db_set("item_photo", ret.get("file_url"))

    return ret


def get_items_xlsx(docname, template_for="all", with_xlsx_template=False):
    fields = TEMPLATES.get(template_for) or TEMPLATES.get("all")
    data = frappe.db.sql(
        """
        select {} from `tabLead Item` where photo_quotation = %s {}""".format(
            ", ".join([f for _, f in fields]), CONDITIONS.get(template_for) or ""
        ),
        (docname,),
        as_list=1,
    )

    excel_rows = [[d for d, f in fields]] + list(data)
    images = [""] + [d[1] for d in data]

    from frappe.modules import get_doc_path
    import os

    file_path, skip_rows = None, 0

    if with_xlsx_template and template_for in XLSX_TEMPLATES:
        file_path = os.path.join(
            get_doc_path("art_collections", "doctype", "Photo Quotation"),
            XLSX_TEMPLATES.get(template_for)["filename"],
        )
        skip_rows = XLSX_TEMPLATES.get(template_for)["skip_rows"]

        if XLSX_TEMPLATES.get(template_for, {}).get("skip_header"):
            excel_rows = excel_rows[1:]
            images = images[1:]

    wb = write_xlsx(
        excel_rows,
        sheet_name="Items",
        file_path=file_path,
        column_widths=[20] * len(fields),
        skip_rows=skip_rows,
    )

    add_images(
        images, workbook=wb, worksheet="Items", image_col="B", skip_rows=skip_rows
    )

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


@frappe.whitelist()
def download_lead_items_template(docname, template):
    frappe.response["filename"] = get_file_name(docname, template)
    frappe.response["filecontent"] = get_items_xlsx(docname, template)
    frappe.response["type"] = "binary"


XLSX_TEMPLATES = {
    "supplier_quotation": {
        "filename": "photo_quotation_to_supplier_template.xlsx",
        "skip_rows": 6,
        "skip_header": 1,
    }
}

EMAIL_TEMPLATES = {
    "supplier_quotation": "Photo Quotation Supplier Notification",
    "supplier_sample_request": "Photo Quotation Supplier Request for Sample Notification",
}

CONDITIONS = {
    "all": "",
    "supplier_quotation": " and (disabled = 0 and is_quoted = 0)",
    "supplier_sample_request": " and (disabled = 0 and is_quoted = 1 and sample_validated = 0)",
}

TEMPLATES = {
    "all": [(d.label, d.fieldname) for d in get_lead_item_fields()],
    "supplier_quotation": [
        ("Item #", "name"),
        ("Photo", "item_photo"),
        ("Description", "description"),
        ("Product Material", "product_material1"),
        ("Pourcentage", "percentage1"),
        ("Product Material 2", "product_material2"),
        ("Pourcentage 2", "percentage2"),
        ("Product Material 3", "product_material3"),
        ("Pourcentage 3", "percentage3"),
        ("HS CODES", "customs_tariff_number"),
        ("Item length (in cm)", "item_length"),
        ("Item width (in cm)", "item_width"),
        ("Item thickness (in cm)", "item_thickness"),
        ("Packaging type", "packing_type"),
        ("MOQ", "moq"),
        ("Unit price (in $)", "unit_price"),
        ("Inner Qty", "inner_qty"),
        ("Display box?", "is_display_box"),
        ("Special mentions?", "is_special_mentions"),
        ("Test Report", "test_report"),
        ("Abandoned?", "is_abandoned"),
        ("Quoted", "is_quoted"),
        ("Samples Validated?", "sample_validated"),
        ("PO Created?", "is_po_created"),
    ],
    "supplier_sample_request": [
        ("Item #", "name"),
        ("Photo", "item_photo"),
        ("Disabled", "disabled"),
        ("Quoted", "is_quoted"),
        ("Samples validated", "sample_validated"),
        ("PO created", "is_po_created"),
        ("Your Item code", "supplier_part_no"),
        ("Your description", "supplier_item_description"),
        ("Product Material 1", "product_material1"),
        ("Pourcentage 1", "percentage1"),
        ("Product Material 2", "product_material2"),
        ("Pourcentage 2", "percentage2"),
        ("Product Material 3", "product_material3"),
        ("Pourcentage 3", "percentage3"),
        ("HS CODES", "customs_tariff_number"),
        ("Item length", "item_length"),
        ("item width", "item_width"),
        ("Item thickness", "item_thickness"),
        ("Packaging Type", "packing_type"),
        ("Racking bag", "is_racking_bag"),
        ("MOQ", "moq"),
        ("Unit Price (in $)", "unit_price"),
        ("Inner Qty", "inner_qty"),
        ("Display box ?", "is_display_box"),
        ("Spécial mentions ?", "is_special_mentions"),
        ("Certificates Required", "is_certificates_reqd"),
        ("Port Of Loading", "port_of_loading"),
    ],
}
