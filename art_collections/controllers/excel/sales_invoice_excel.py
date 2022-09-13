from __future__ import unicode_literals
import frappe
from frappe import _
import io
import openpyxl
from frappe.utils import cint, get_site_url, get_url, today
from art_collections.controllers.excel import write_xlsx, attach_file, add_images
from frappe.utils.file_manager import MaxFileSizeReachedError


def on_submit_sales_invoice(doc, method=None):
    _make_excel_attachment(doc.doctype, doc.name)
    # attach_print_pdf(doc.doctype, doc.name)


@frappe.whitelist()
def _make_excel_attachment(doctype, docname):
    attach_print_pdf(doctype, docname)
    currency = frappe.db.get_value(doctype, docname, "currency")

    data = frappe.db.sql(
        """
        select 
            i.item_code, 
            i.item_name, 
            tib.barcode,
            i.customs_tariff_number ,
            tsii.weight_per_unit ,
            tppd.`length` , 
            tppd.width , 
            tppd.thickness , 
            tsii.qty, 
            tsii.uom ,
            tsii.stock_uom , 
            tsii.conversion_factor , 
            tsii.stock_qty , 
            tsii.stock_uom_rate , 
            tsii.base_net_rate , 
            tsii.base_amount , 
            case when i.image is null then ''
                when SUBSTR(i.image,1,4) = 'http' then i.image
                else concat('{}/',i.image) end image ,
            i.image image_url
            from `tabSales Invoice` tsi 
       	inner join `tabSales Invoice Item` tsii on tsii.parent = tsi.name 
       	inner join tabItem i on i.name = tsii.item_code
        left outer join `tabItem Barcode` tib on tib.parent = i.name 
            and tib.idx  = (
                select min(idx) from `tabItem Barcode` tib2
                where parent = i.name
            )
        left outer join `tabProduct Packing Dimensions` tppd on tppd.parent = i.name 
	        and tppd.uom = tsii.stock_uom
        where tsi.name = %s
    """.format(
            get_url()
        ),
        (docname,),
        as_dict=True,
    )

    columns = [
        _("Item Code"),
        _("Item Name"),
        _("Barcode"),
        _("HSCode"),
        _("Weight per unit (kg)"),
        _("Length in cm (of stock_uom)"),
        _("Width in cm (of stock_uom)"),
        _("Thickness in cm (of stock_uom)"),
        _("Qté Inner (SPCB)"),
        _("UOM"),
        _("Prix Inner ({})").format(currency),
        _("Stock UOM"),
        _("Qté colisage (UV)"),
        _("Qté totale"),
        _("Prix unité ({})").format(currency),
        _("Amount ({})").format(currency),
        _("Photo"),
    ]

    fields = [
        "item_code",
        "item_name",
        "barcode",
        "customs_tariff_number",
        "weight_per_unit",
        "length",
        "width",
        "thickness",
        "qty",
        "uom",
        "base_net_rate",
        "stock_uom",
        "conversion_factor",
        "stock_qty",
        "stock_uom_rate",
        "base_amount",
        "image",
    ]

    wb = openpyxl.Workbook()

    excel_rows, images = [columns], [""]
    for d in data:
        excel_rows.append([d.get(f) for f in fields])
        images.append(d.get("image_url"))
    write_xlsx(excel_rows, "Sales Invoice Items", wb, [20] * len(columns))
    add_images(images, workbook=wb, worksheet="Sales Invoice Items", image_col="Q")

    # make attachment
    out = io.BytesIO()
    wb.save(out)
    attach_file(
        out.getvalue(),
        doctype=doctype,
        docname=docname,
        show_email_dialog=1,
    )


def attach_print_pdf(doctype, name):
    doc = frappe.get_doc(doctype, name)
    print_formats = ["Art Sales invoice"]
    mode_of_payment_art = frappe.db.get_value(
        "Sales Invoice", name, ["mode_of_payment_art"]
    )

    if mode_of_payment_art and (
        mode_of_payment_art == "Traite" or "LCR" in mode_of_payment_art
    ):
        print_formats.append("Art SI")

    try:
        for fmt in print_formats:
            out = frappe.attach_print(
                doctype,
                name,
                file_name="Invoice-{}_{}_{}".format(name, today(), fmt),
                print_format=fmt,
            )
            _file = frappe.get_doc(
                {
                    "doctype": "File",
                    "file_name": out["fname"],
                    "attached_to_doctype": doc.doctype,
                    "attached_to_name": doc.name,
                    "is_private": 0,
                    "content": out["fcontent"],
                }
            )
            _file.save(ignore_permissions=True)
        frappe.db.commit()
    except MaxFileSizeReachedError:
        # WARNING: bypass max file size exception
        pass
    except frappe.FileAlreadyAttachedException:
        pass
    except frappe.DuplicateEntryError:
        # same file attached twice??
        pass
    # except Exception:
    #     frappe.throw(frappe.get_traceback())
