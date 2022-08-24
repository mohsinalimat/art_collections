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
            callback="supplier_email_callback",
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
        invalid_items = frappe.db.sql(
            """
    select 
        tscd.item_code, ti.item_name ,
        tscd.supplier_part_no, tpoi.supplier_part_no poi_supplier_part_no,
        tscd.barcode, tib.barcode item_barcode,
        tscd.packing_type_art, ti.packing_type_art item_packing_type_art,
        tscd.qty, tpoi.qty poi_qty,
        tscd.rate, tpoi.rate poi_rate,
        tscd.qty_in_selling_pack_art, ti.qty_in_selling_pack_art item_qty_in_selling_pack_art,
        tscd.qty_per_inner , ti.nb_inner_in_outer_art item_qty_per_inner
    from `tabSales Confirmation` tsc 
    inner join `tabSales Confirmation Detail` tscd on tscd.parent = tsc.name 
    left outer join `tabPurchase Order Item` tpoi on tpoi.item_code = tscd.item_code and tpoi.parent = tsc.purchase_order 
    left outer join tabItem ti on ti.name = tscd.item_code
    left outer join `tabItem Barcode` tib on tib.parent = ti.item_code and tib.barcode_type = 'EAN'
    and tpoi.parent = tsc.purchase_order 
    where tsc.name = %s and
    (
        tscd.supplier_part_no <> tpoi.supplier_part_no or
        tscd.barcode <> tib.barcode or
        tscd.item_name <> tpoi.item_name or
        tscd.packing_type_art <> ti.packing_type_art or
        tscd.qty <> tpoi.qty or
        tscd.rate <> tpoi.rate or
        tscd.qty_in_selling_pack_art <> ti.qty_in_selling_pack_art or
        tscd.qty_per_inner  <> ti.nb_inner_in_outer_art
    ) 
        """,
            (self.name),
        )

        if invalid_items:
            self.db_set("Status", "To be Treated")
            # create excel attachment with differences
            wb = write_xlsx(
                invalid_items,
                "Invalid Items",
                file_path=os.path.join(
                    os.path.dirname(__file__),
                    "invalid_items_in_sales_confirmation" + ".xlsx",
                ),
                skip_rows=1,
            )

            out = io.BytesIO()
            wb.save(out)

            error_file = attach_file(
                out.getvalue(),
                doctype=self.doctype,
                docname=self.name,
                file_name="%s Invalid items.xlsx" % (self.name + frappe.utils.today()),
                show_email_dialog=0,
            )
            frappe.msgprint(
                _(
                    "Purchase Order items and Sales Confirmation do not match. Please check the errors"
                )
            )
            return error_file.file_url


@frappe.whitelist()
def supplier_email_callback(docname):
    frappe.db.set_value("Sales Confirmation", docname, "status", "Replied")


@frappe.whitelist()
def make_from_po(docname):
    po = frappe.get_doc("Purchase Order", docname)
    sc_name = frappe.db.exists("Sales Confirmation", {"purchase_order": docname})
    if sc_name:
        doc = frappe.get_doc("Sales Confirmation", sc_name)
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Sales Confirmation",
                "purchase_order": docname,
                "supplier": po.supplier,
                "contact_person": po.get("contact_person"),
                "contact_email": po.get("contact_email"),
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
