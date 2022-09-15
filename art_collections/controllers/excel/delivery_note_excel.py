from __future__ import unicode_literals
from locale import currency
import frappe
from frappe import _
import io
import openpyxl
from frappe.utils import cint, get_site_url, get_url
from art_collections.controllers.excel import write_xlsx, attach_file, add_images


def on_submit_delivery_note(doc, method=None):
    _make_excel_attachment(doc.doctype, doc.name)


@frappe.whitelist()
def _make_excel_attachment(doctype, docname):
    currency = frappe.db.get_value(doctype, docname, "currency")

    data = frappe.db.sql(
        """
        select 
            i.item_code, 
            i.item_name, 
            tib.barcode,
            i.customs_tariff_number ,
            tdni.weight_per_unit ,
            tppd.`length` , 
            tppd.width , 
            tppd.thickness , 
            tdni.qty, 
            tdni.uom ,
            tdni.stock_uom , 
            tdni.conversion_factor , 
            tdni.stock_qty , 
            tdni.base_amount ,
            tdni.base_net_rate ,
            tdni.stock_uom_rate ,
            case when i.image is null then ''
                when SUBSTR(i.image,1,4) = 'http' then i.image
                else concat('{}/',i.image) end image ,
            i.image image_url
            from `tabDelivery Note` tdn 
       	inner join `tabDelivery Note Item` tdni on tdni.parent = tdn.name 
       	inner join tabItem i on i.name = tdni.item_code
        left outer join `tabItem Barcode` tib on tib.parent = i.name 
            and tib.idx  = (
                select min(idx) from `tabItem Barcode` tib2
                where parent = i.name
            )
        left outer join `tabProduct Packing Dimensions` tppd on tppd.parent = i.name 
	        and tppd.uom = tdni.stock_uom
        where tdn.name = %s
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

    write_xlsx(excel_rows, "Delivery Note Items", wb, [20] * len(columns))
    add_images(images, workbook=wb, worksheet="Delivery Note Items", image_col="O")

    # make attachment
    out = io.BytesIO()
    wb.save(out)
    attach_file(
        out.getvalue(),
        doctype=doctype,
        docname=docname,
        show_email_dialog=1,
    )
