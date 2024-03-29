from __future__ import unicode_literals
import frappe
from frappe import _
import io
import openpyxl
from frappe.utils import cint, get_site_url, get_url
from art_collections.controllers.excel import write_xlsx, attach_file, add_images


def on_submit_quotation(doc, method=None):
    _make_excel_attachment(doc.doctype, doc.name)


@frappe.whitelist()
def _make_excel_attachment(doctype, docname):
    from art_collections.controllers.excel import write_xlsx

    currency = frappe.db.get_value(doctype, docname, "currency")

    data = frappe.db.sql(
        """
        select 
            i.item_code, 
            i.item_name, 
            tib.barcode,
            i.customs_tariff_number ,
            tqi.weight_per_unit ,
            tppd.`length` , 
            tppd.width , 
            tppd.thickness , 
            tqi.qty, 
            tqi.uom ,
            tqi.base_net_rate ,     
            tqi.stock_uom , 
            tqi.conversion_factor , 
            tqi.stock_qty , 
            tqi.stock_uom_rate ,
            tqi.base_amount ,
            tip.price_list_rate , 
            tpr.min_qty  pricing_rule_min_qty , 
            tpr.rate pricing_rule_rate ,
            i.is_existing_product_cf ,
            case when i.image is null then ''
                when SUBSTR(i.image,1,4) = 'http' then i.image
                else concat('{}/',i.image) end image ,
            i.image image_url 
        from tabQuotation tq
        inner join `tabQuotation Item` tqi on tqi.parent = tq.name
        inner join tabItem i on i.name = tqi.item_code
        left outer join `tabItem Barcode` tib on tib.parent = i.name 
            and tib.idx  = (
                select min(idx) from `tabItem Barcode` tib2
                where parent = i.name
            )
        left outer join `tabProduct Packing Dimensions` tppd on tppd.parent = i.name 
            and tppd.uom = tqi.stock_uom
        left outer join `tabPricing Rule` tpr on tpr.is_volume_price_cf = 1
            and tpr.selling = 1 and exists (
                select 1 from `tabPricing Rule Item Code` x 
                where x.parent = tpr.name and x.uom = tqi.stock_uom and x.item_code = i.item_code) 
        left outer join `tabItem Price` tip 
        on tip.item_code = tqi.item_code and tip.uom = tqi.stock_uom 
        and tip.price_list = (
            select value from tabSingles ts
            where doctype = 'Selling Settings' 
            and field = 'selling_price_list'
        )
        where tq.name = %s
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
        _("Price List Rate ({})").format(currency),
        _("Pricing rule > Min Qty*"),
        _("Pricing rule > Rate*	"),
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
        "price_list_rate",
        "pricing_rule_min_qty",
        "pricing_rule_rate",
        "image",
    ]

    wb = openpyxl.Workbook()

    excel_rows, images = [columns], [""]
    for d in data:
        excel_rows.append([d.get(f) for f in fields])
        images.append(d.get("image_url"))

    write_xlsx(excel_rows, "Quotation Items", wb, [20] * len(columns))
    add_images(images, workbook=wb, worksheet="Quotation Items", image_col="T")

    # make attachment
    out = io.BytesIO()
    wb.save(out)
    attach_file(
        out.getvalue(),
        doctype=doctype,
        docname=docname,
        show_email_dialog=1,
    )
