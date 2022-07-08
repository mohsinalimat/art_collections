from __future__ import unicode_literals
import frappe
from frappe import _
import io
import openpyxl
from frappe.utils import cint, get_site_url, get_url
from art_collections.controllers.excel import write_xlsx, attach_file


def on_submit_sales_invoice(doc, method=None):
    _make_excel_attachment(doc.doctype, doc.name)


@frappe.whitelist()
def _make_excel_attachment(doctype, docname):

    data = frappe.db.sql(
        """
        select 
            i.item_code, 
            tib.barcode,
            i.customs_tariff_number ,
            tsii.weight_per_unit ,
            tppd.`length` , 
            tppd.width , 
            tppd.thickness , 
            tsii.qty, 
            tsii.uom ,
            tsii.stock_uom , 
            ucd.conversion_factor , 
            tsii.stock_qty , 
            case when i.image is null then ''
                when SUBSTR(i.image,1,4) = 'http' then i.image
                else concat('{}/',i.image) end image
            from `tabSales Invoice` tsi 
       	inner join `tabSales Invoice Item` tsii on tsii.parent = tsi.name 
       	inner join tabItem i on i.name = tsii.item_code
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
        where tsi.name = %s
    """.format(
            get_url()
        ),
        (docname,),
        as_dict=True
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
        _("Stock UOM"),
        _("UOM Conversion Factor"),
        _("Qty as per stock UOM"),
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
        "stock_uom",
        "conversion_factor",
        "stock_qty",
        "image",
    ]

    wb = openpyxl.Workbook()

    excel_rows = [columns]
    for d in data:
        excel_rows.append([d.get(f) for f in fields])
    write_xlsx(excel_rows, "Sales Invoice Items", wb, [20] * len(columns))

    # make attachment
    out = io.BytesIO()
    wb.save(out)
    attach_file(
        out.getvalue(),
        doctype=doctype,
        docname=docname,
    )
