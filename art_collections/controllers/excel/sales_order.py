from __future__ import unicode_literals
import frappe
from frappe import _
import io
import openpyxl
from frappe.utils import cint, get_site_url, get_url, cstr
from art_collections.controllers.excel import write_xlsx, attach_file
from openpyxl.drawing.image import Image
from io import BytesIO
from openpyxl.utils import get_column_letter


def on_submit_sales_order(doc, method=None):
    _make_excel_attachment(doc.doctype, doc.name)


def add_images(data, workbook, worksheet=""):
    ws = workbook.get_sheet_by_name(worksheet)
    image_col = get_column_letter(len(data[0]) - 2)
    for row, d in enumerate(data):
        if d.image_url:
            try:
                item_file = frappe.get_doc("File", {"file_url": d.image_url})
                image = openpyxl.drawing.image.Image(
                    io.BytesIO(item_file.get_content())
                )
                image.height = 100
                image.width = 100
                ws.add_image(image, f"{image_col}{cstr(row+2)}")
                ws.row_dimensions[row + 2].height = 100
            except:
                pass


@frappe.whitelist()
def _make_excel_attachment(doctype, docname):

    data = frappe.db.sql(
        """
        select 
            i.item_code, 
            tib.barcode,
            i.customs_tariff_number ,
            tsoi.weight_per_unit ,
            tppd.`length` , 
            tppd.width , 
            tppd.thickness , 
            tsoi.qty, 
            tsoi.uom ,
            tsoi.base_net_rate ,     
            tsoi.stock_uom , 
            ucd.conversion_factor , 
            tsoi.stock_qty , 
            tsoi.stock_uom_rate , 
            tpr.min_qty  pricing_rule_min_qty , 
            tpr.rate pricing_rule_rate ,
            i.is_existing_product_cf ,
            tsoi.total_saleable_qty_cf ,
            case when i.image is null then ''
                when SUBSTR(i.image,1,4) = 'http' then i.image
                else concat('{}',i.image) end image ,
            i.image image_url
        from `tabSales Order` tso 
        inner join `tabSales Order Item` tsoi on tsoi.parent = tso.name
        inner join tabItem i on i.name = tsoi.item_code
        left outer join `tabItem Barcode` tib on tib.parent = i.name 
            and tib.idx  = (
                select min(idx) from `tabItem Barcode` tib2
                where parent = i.name
            )
        left outer join `tabProduct Packing Dimensions` tppd on tppd.parent = i.name 
	        and tppd.uom = (
	                select value from tabSingles
	                where doctype like 'Art Collections Settings' 
	                and field = 'inner_carton_uom' 
	            )        
        left outer join `tabUOM Conversion Detail` ucd on ucd.parent = i.name 
            and ucd.parenttype='Item' and ucd.uom = (
                select value from tabSingles
                where doctype like 'Art Collections Settings' 
                and field = 'inner_carton_uom' 
            )
        left outer join `tabPricing Rule Detail` tprd on tprd.parenttype = 'Sales Order' 
       		and tprd.parent = tso.name 
       	left outer join `tabPricing Rule` tpr on tpr.name = tprd.pricing_rule 
       		and tpr.selling = 1 and exists (
       			select 1 from `tabPricing Rule Item Code` x 
       			where x.parent = tpr.name and x.uom = tsoi.stock_uom)            
        where tso.name = %s
    """.format(
            get_url()
        ),
        (docname,),
        as_dict=True,
        # debug=True,
    )

    columns = [
        _("Item Code"),
        _("Barcode"),
        _("HSCode"),
        _("Weight per unit"),
        _("Length (of stock_uom)"),
        _("Width (of stock_uom)"),
        _("Thickness (of stock_uom)"),
        _("Quantity"),
        _("UOM"),
        _("Rate (EUR)"),
        _("Stock UOM"),
        _("UOM Conversion Factor"),
        _("Qty as per stock UOM"),
        _("Rate of Stock UOM (EUR)"),
        _("Pricing rule > Min Qty*"),
        _("Pricing rule > Rate*	"),
        _("Photo Link"),
        _("Photo"),
    ]

    fields = [
        "item_code",
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
        "pricing_rule_min_qty",
        "pricing_rule_rate",
        "image",
    ]

    wb = openpyxl.Workbook()
    excel_rows = [columns]
    for d in data:
        if d.total_saleable_qty_cf <= d.stock_qty:
            excel_rows.append([d.get(f) for f in fields])
    write_xlsx(excel_rows, "In Stock Items", wb, [20] * len(columns), index=0)
    add_images(data, workbook=wb, worksheet="In Stock Items")

    excel_rows = [columns]
    for d in data:
        if d.total_saleable_qty_cf > d.stock_qty:
            excel_rows.append([d.get(f) for f in fields])
    write_xlsx(excel_rows, "Out of Stock Items", wb, [20] * len(excel_rows[0]), index=1)
    add_images(data, workbook=wb, worksheet="Out of Stock Items")

    discontinued_items = frappe.db.sql(
        """
        select 
            i.item_code, 
            tib.barcode,
            i.customs_tariff_number ,
            tppd.`length` , 
            tppd.width , 
            tppd.thickness , 
            tsoi.qty, 
            ucd.conversion_factor , 
            0  pricing_rule_min_qty , 
            0 pricing_rule_rate ,
            i.is_existing_product_cf ,
            i.image image_url
        from `tabSales Order` tso 
        inner join `tabSales Order Discountinued Items CT` tsoi on tsoi.parent = tso.name
        inner join tabItem i on i.name = tsoi.item_code
        left outer join `tabItem Barcode` tib on tib.parent = i.name 
            and tib.idx  = (
                select min(idx) from `tabItem Barcode` tib2
                where parent = i.name
            )
        left outer join `tabProduct Packing Dimensions` tppd on tppd.parent = i.name 
        left outer join `tabUOM Conversion Detail` ucd on ucd.parent = i.name 
            and ucd.parenttype='Item' and ucd.uom = (
                select value from tabSingles
                where doctype like 'Art Collections Settings' 
                and field = 'inner_carton_uom' 
            )
        where tso.name = %s
    """,
        (docname,),
        as_dict=True,
    )

    columns = [
        _("Item Code"),
        _("Barcode"),
        _("HSCode"),
        _("Length (of stock_uom)"),
        _("Width (of stock_uom)"),
        _("Thickness (of stock_uom)"),
        _("Quantity"),
        _("UOM Conversion Factor"),
        _("Pricing rule > Min Qty*"),
        _("Pricing rule > Rate*	"),
    ]

    fields = [
        "item_code",
        "barcode",
        "customs_tariff_number",
        "length",
        "width",
        "thickness",
        "qty",
        "conversion_factor",
        "pricing_rule_min_qty",
        "pricing_rule_rate",
    ]

    excel_rows = [columns]
    for d in discontinued_items[:]:
        excel_rows.append([d.get(f) for f in fields])
    write_xlsx(excel_rows, "Discontinued Items", wb, [20] * len(excel_rows[0]), index=2)
    add_images(data, workbook=wb, worksheet="Discontinued Items")

    # existing art works
    # art_works = frappe.db.sql(
    #     """
    # select
    #     DISTINCT parent item_code, art_work_name , art_work_attachment
    # from `tabExisting Product Art Work`
    # where parent in (
    # 	select item_code from `tabPurchase Order Item` tpoi
    # 	where parent = %s
    # )
    # """,
    #     (docname,),
    #     as_dict=True,
    # )
    # art_work_names = frappe.utils.unique([d.art_work_name for d in art_works])

    # excel_rows = [columns + art_work_names]

    # # print(art_work_names, art_works, excel_rows)
    # site_url = get_url()
    # for d in data:
    #     if cint(d.is_existing_product_cf):
    #         row = list(d.values())
    #         row = row[: len(row) - 1]
    #         for name in art_work_names:
    #             for aw in art_works:
    #                 if aw.item_code == d.item_code and aw.art_work_name == name:
    #                     row.append(f"{site_url}{aw.art_work_attachment}")
    #         excel_rows.append(row)
    # write_xlsx(excel_rows, "Existing Product", wb, [20] * len(excel_rows[0]))

    # make attachment
    out = io.BytesIO()
    wb.save(out)
    attach_file(
        out.getvalue(),
        doctype=doctype,
        docname=docname,
    )
