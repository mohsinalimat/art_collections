# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cstr, cint
from frappe.model.document import Document
from art_collections.controllers.excel import write_xlsx, attach_file, add_images
import io
import os
from frappe.modules import get_doc_path

FIELDS_TO_VALIDATE_WITH_PO = [
    "item_code",
    "supplier_part_no",
    "barcode",
    "item_name",
    "packing_type_art",
    "qty",
    "rate",
    "qty_in_selling_pack_art",
    "qty_per_inner",
]


class SalesConfirmation(Document):
    def validate(self):
        pass

    @frappe.whitelist()
    def email_supplier(self):
        content = get_items_xlsx(self.name)
        attach_file(
            content,
            doctype=self.doctype,
            docname=self.name,
            show_email_dialog=1,
            recipients="",
        )

    @frappe.whitelist()
    def update_items_and_po(self):
        if not self.confirmation_date:
            frappe.throw(_("Confirmation Date is not set."))

        po = frappe.get_doc("Purchase Order", self.purchase_order)

        update_po_fields = [
            "packing_type_art",
            "qty_in_selling_pack_art",
            "customs_tariff_number",
        ]
        update_poi_fields = [
            "total_outer_cartons_art",
            "cbm_per_outer_art ",
            "total_cbm",
            "rate",
            "qty",
        ]

        for d in self.sales_confirmation_detail:
            if not cint(d.is_verified):
                continue
            item = frappe.get_doc("Item", d.item_code)
            item.update({field: d.get(field) for field in update_po_fields})
            for poi in [x for x in po.items if x.item_code == d.item_code]:
                if not cint(d.is_checked):
                    continue
                poi.update({field: d.get(field) for field in update_poi_fields})

        self.db_set("status", "Validated")

    @frappe.whitelist()
    def verify_with_po(self):
        invalid_items, msg = [], 0
        po = frappe.get_doc("Purchase Order", self.purchase_order)

        for d in self.sales_confirmation_detail:
            for po_item in list(filter(lambda x: x.item_code == x.item_code, po.items)):
                for field in FIELDS_TO_VALIDATE_WITH_PO:
                    if not d.get(field) == po_item.get(field):
                        invalid_items.append((po_item, d))
                        break

        if invalid_items:
            self.db_set("Status", "To be Treated")
            # TODO: create table field-wise
            msg = ", ".join(x[0].item_code for x in invalid_items)
            frappe.msgprint(
                _(
                    "Purchase Order items and Sales Confirmation do not match. Please check the errors"
                )
            )
        return msg


@frappe.whitelist()
def make_from_po(self):
    po = frappe.get_doc("Purchase Order", self.purchase_order)
    docname = frappe.db.exists(
        "Sales Confirmation", {"purchase_order": self.purchase_order}
    )
    if docname:
        doc = frappe.get_doc("Sales Confirmation", docname)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Sales Confirmation",
                "purchase_order": self.purchase_order,
                "supplier": po.supplier,
                # "transaction_date": "",
                # "confirmation_date": "",
            }
        )

    for d in po.items:
        child = doc.append(
            "sales_confirmation_detail",
            {
                "item_code": d.item_code,
                "supplier_part_no": d.supplier_part_no,
                "image": d.image,
                "item_name": d.item_name,
                "qty_per_inner": d.nb_selling_packs_in_inner_art,
                "qty_per_outer": d.nb_selling_packs_in_outer_art,
                "qty": d.qty,
                "rate": d.rate,
                "amount": d.amount,
                "total_outer_cartons_art": d.total_outer_cartons_art,
                "cbm_per_outer_art": d.cbm_per_outer_art,
                "total_cbm": d.total_cbm,
            },
        )
        values = frappe.db.get_value(
            "Item",
            {"parent": d.item_code},
            [
                "packing_type_art",
                "qty_in_selling_pack_art",
                "customs_tariff_number",
            ],
            as_dict=1,
        )
        for k in values or {}:
            child.update({k: values.get(k)})
        values = frappe.db.get_value(
            "Item Supplier",
            {"parent": d.item_code, "supplier": po.supplier},
            ["supplier_part_no", "supplier_part_description_art"],
            as_dict=1,
        )
        for k in values or {}:
            child.update({k: values.get(k)})
        values = frappe.db.get_value(
            "Item Barcode",
            {"parent": d.item_code, "barcode_type": "EAN"},
            [
                "barcode",
            ],
            as_dict=1,
        )
        for k in values or {}:
            child.update({k: values.get(k)})
    doc.save()
    return doc.name


@frappe.whitelist()
def download_details(docname):
    frappe.response["filename"] = "Sales Confirmation-{name}-{supplier}.xlsx".format(
        **frappe.db.get_value(
            "Sales Confirmation", docname, ["name", "supplier"], as_dict=True
        )
    )
    frappe.response["filecontent"] = get_items_xlsx(docname)
    frappe.response["type"] = "binary"


def get_items_xlsx(docname):

    data = frappe.db.sql(
        """
		select
            item_code , supplier_part_no , image , barcode ,  supplier_item_description_ar ,
            item_name , packing_type_art , qty_in_selling_pack_art , qty_per_inner , qty_per_outer , qty ,
            rate , 0 grand_total , total_outer_cartons_art , cbm_per_outer_art , total_cbm , customs_tariff_number 
            from `tabSales Confirmation Detail` tscd 
            where parent = %s
        """,
        (docname,),
        as_list=1,
    )

    columns = [_(frappe.unscrub(cstr(c[0]))) for c in frappe.db.get_description()]

    excel_rows = [columns] + list(data)
    images = [""] + [d[1] for d in data]

    file_path, skip_rows = None, 5

    file_path = os.path.join(
        get_doc_path("art_collections", "doctype", "Sales Confirmation"),
        "sales_confirmation.xlsx",
    )

    wb = write_xlsx(
        excel_rows,
        sheet_name="Sales Confirmation Details",
        file_path=file_path,
        column_widths=[20] * len(columns),
        skip_rows=skip_rows,
    )

    add_images(
        images,
        workbook=wb,
        worksheet="Sales Confirmation Details",
        image_col="C",
        skip_rows=skip_rows,
    )

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()
