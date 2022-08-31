# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cstr, cint, today, now_datetime, getdate, format_date
from frappe.model.document import Document
from art_collections.controllers.excel import write_xlsx, attach_file, add_images
import io
import os
from frappe.modules import get_doc_path
import re
from erpnext.accounts.party import get_party_details
from frappe.utils.data import format_date
from openpyxl.styles.alignment import Alignment

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
    def email_supplier(self, show_email_dialog=1):
        content = get_items_xlsx(self.name, self.supplier)
        attach_file(
            content,
            doctype=self.doctype,
            docname=self.name,
            show_email_dialog=show_email_dialog,
            recipients="",
            callback=show_email_dialog and "supplier_email_callback" or 0,
        )

    @frappe.whitelist()
    def update_items_and_po(self):
        if not self.confirmation_date:
            msg += _("Confirmation Date is not set.")
        msg = ""
        for d in filter(lambda x: not x.is_verified, self.sales_confirmation_detail):
            msg += _("Please verify all items to update. ")
            break
        for d in filter(lambda x: not x.is_checked, self.sales_confirmation_detail):
            msg += _("Please check all items to update. ")
            break

        if msg:
            frappe.throw(msg)

        po = frappe.get_doc("Purchase Order", self.purchase_order)

        for d in self.sales_confirmation_detail:
            # update item
            item = frappe.get_doc("Item", d.item_code)
            item.update(
                {
                    field: d.get(field)
                    for field in [
                        "packing_type_art",
                        "qty_in_selling_pack_art",
                        "customs_tariff_number",
                    ]
                }
            )
            # update item child tables
            for cdn in item.supplier_items:
                if cdn.supplier == self.supplier:
                    cdn.supplier_part_description_art = d.supplier_item_description_ar
                    cdn.supplier_part_no = d.supplier_part_no

            # update uoms
            inner = frappe.db.get_single_value(
                "Art Collections Settings", "inner_carton_uom"
            )
            if inner:
                uom = next((cdt for cdt in item.uoms if cdt.uom == inner), None)
                if not uom:
                    uom = item.append(
                        "uoms",
                        {
                            "uom": inner,
                            "conversion_factor": cint(d.qty_per_inner),
                        },
                    )
                else:
                    uom.conversion_factor = cint(d.qty_per_inner)
            outer = frappe.db.get_single_value(
                "Art Collections Settings", "outer_carton_uom"
            )
            if outer:
                uom = next((cdt for cdt in item.uoms if cdt.uom == outer), None)
                if not uom:
                    uom = item.append(
                        "uoms",
                        {
                            "uom": outer,
                            "conversion_factor": cint(d.qty_per_outer),
                        },
                    )
                else:
                    uom.conversion_factor = cint(d.qty_per_outer)

            # update po items
            for poi in [x for x in po.items if x.item_code == d.item_code]:
                poi.update(
                    {
                        field: d.get(field)
                        for field in [
                            "total_outer_cartons_art",
                            "cbm_per_outer_art ",
                            "total_cbm",
                            "rate",
                            "qty",
                        ]
                    }
                )
            item.save()
        po.save()

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
        tscd.qty_per_inner , tucd.conversion_factor item_qty_per_inner
    from `tabSales Confirmation` tsc 
    inner join `tabSales Confirmation Detail` tscd on tscd.parent = tsc.name 
    left outer join `tabPurchase Order Item` tpoi on tpoi.item_code = tscd.item_code and tpoi.parent = tsc.purchase_order 
    and tpoi.parent = tsc.purchase_order 
    left outer join tabItem ti on ti.name = tscd.item_code
    left outer join `tabItem Barcode` tib on tib.parent = ti.item_code and tib.barcode_type = 'EAN'
    left outer join `tabUOM Conversion Detail` tucd on tucd.parent = ti.name 
    and tucd.uom = (select value from tabSingles ts 
        where doctype = 'Art Collections Settings' and field = 'inner_carton_uom')
    where tsc.name = %s and
    (
        tscd.supplier_part_no <> tpoi.supplier_part_no or
        tscd.barcode <> tib.barcode or
        tscd.item_name <> tpoi.item_name or
        tscd.packing_type_art <> ti.packing_type_art or
        tscd.qty <> tpoi.qty or
        tscd.rate <> tpoi.rate or
        tscd.qty_in_selling_pack_art <> ti.qty_in_selling_pack_art or
        tscd.qty_per_inner  <> tucd.conversion_factor
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
    frappe.db.set_value("Sales Confirmation", docname, "confirmation_date", None)


@frappe.whitelist()
def make_from_po(docname):
    po = frappe.get_doc("Purchase Order", docname)
    sc_name = frappe.db.exists("Sales Confirmation", {"purchase_order": docname})
    if sc_name:
        doc = frappe.get_doc("Sales Confirmation", sc_name)
        doc.sales_confirmation_detail = []
    else:
        doc = frappe.get_doc(
            {
                "doctype": "Sales Confirmation",
                "purchase_order": docname,
                "supplier": po.supplier,
                "contact_person": po.get("contact_person"),
                "contact_email": po.get("contact_email"),
                "transaction_date": po.get("transaction_date"),
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

        for item_details in frappe.db.sql(
            """
                select packing_type_art , qty_in_selling_pack_art , customs_tariff_number ,
                tis.supplier_part_no , tis.supplier_part_description_art supplier_item_description_ar, tib.barcode
                from tabItem ti
                inner join `tabItem Supplier` tis on tis.parent = ti.name and tis.supplier = %s
                inner join `tabItem Barcode` tib on tib.parent = ti.name and tib.barcode_type = 'EAN'
                where ti.item_code = %s
            """,
            (po.supplier, d.item_code),
            as_dict=True,
        ):
            child.update(item_details)

    doc.save()
    return doc.name


@frappe.whitelist()
def download_details(docname, supplier):
    frappe.response["filename"] = "Sales Confirmation-{}-{}.xlsx".format(
        docname, supplier
    )
    frappe.response["filecontent"] = get_items_xlsx(docname, supplier)
    frappe.response["type"] = "binary"


def get_items_xlsx(docname, supplier=None):
    SHEET_NAME = "Sales Confirmation Details"

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
        sheet_name=SHEET_NAME,
        file_path=file_path,
        column_widths=[20] * len(columns),
        skip_rows=skip_rows,
    )

    add_images(
        images,
        workbook=wb,
        worksheet=SHEET_NAME,
        image_col="C",
        skip_rows=skip_rows,
    )

    wb.active = wb[SHEET_NAME]

    if supplier:
        details = frappe.render_template(
            SUPPLIER_DISPLAY_TEMPLATE,
            get_party_details(supplier, party_type="Supplier"),
        )
        # set supplier details
        wb[SHEET_NAME]["E2"] = re.sub("<br>", "\n\n", details)
        wb[SHEET_NAME]["E2"].alignment = Alignment(horizontal="center")

        for d in frappe.db.sql(
            """
            select tpo.schedule_date , tpo.name
            from `tabPurchase Order` tpo 
            inner join `tabSales Confirmation` tsc on tsc.purchase_order = tpo.name
            where tsc.name = %s
        """,
            (docname,),
            as_dict=True,
        ):
            wb[SHEET_NAME]["Q2"] = "-"
            wb[SHEET_NAME]["Q3"] = format_date(today(), "dd/mm/yy")
            wb[SHEET_NAME]["Q4"] = d.name
            wb[SHEET_NAME]["Q5"] = format_date(d.schedule_date, "dd/mm/yy")

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


SUPPLIER_DISPLAY_TEMPLATE = """
{{supplier_name}}
{{address_display}}
{{contact_person}}
{{contact_mobile}}
{{contact_email}}
"""
