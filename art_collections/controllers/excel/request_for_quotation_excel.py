from __future__ import unicode_literals
import frappe
from frappe import _
import io
import openpyxl
from frappe.utils import cint, get_site_url, get_url
from art_collections.controllers.excel import write_xlsx, attach_file, add_images


def on_submit_request_for_quotation(doc, method=None):
    _make_excel_attachment(doc.doctype, doc.name)


@frappe.whitelist()
def _make_excel_attachment(doctype, docname, attach=False):
    from art_collections.controllers.excel import write_xlsx

    data = frappe.db.sql(
        """
 select 
            i.item_code, 
            i.item_name , 
            trfqi.supplier_part_no ,
            tib.barcode,
            i.customs_tariff_number ,
            trfqi.qty,
            trfqi.stock_uom , 
            0 base_net_rate , 
			0 base_net_amount ,
            case when i.image is null then ''
                when SUBSTR(i.image,1,4) = 'http' then i.image
                else concat('{}/',i.image) end image ,
            i.image image_url
            from `tabRequest for Quotation` trfq 
            inner join `tabRequest for Quotation Item` trfqi on trfqi.parent = trfq.name
            inner join tabItem i on i.name = trfqi.item_code
        left outer join `tabItem Barcode` tib on tib.parent = i.name 
            and tib.idx  = (
                select min(idx) from `tabItem Barcode` tib2
                where parent = i.name
            )
        where trfq.name = %s
    """.format(
            get_url()
        ),
        (docname,),
        as_dict=True,
    )

    columns = [
        _("Item Code"),
        _("Item Name"),
        _("Supplier items"),
        _("Barcode"),
        _("HSCode"),
        _("Quantity"),
        _("Stock UOM"),
        _("Photo"),
    ]

    fields = [
        "item_code",
        "item_name",
        "supplier_part_no",
        "barcode",
        "customs_tariff_number",
        "qty",
        "stock_uom",
        "image",
    ]

    wb = openpyxl.Workbook()

    excel_rows, images = [columns], [""]
    for d in data:
        excel_rows.append([d.get(f) for f in fields])
        images.append(d.get("image_url"))

    write_xlsx(excel_rows, "RFQ Items", wb, [20] * len(columns))
    add_images(images, workbook=wb, worksheet="RFQ Items", image_col="I")

    # make attachment
    out = io.BytesIO()
    wb.save(out)

    if cint(attach):
        attach_file(
            out.getvalue(),
            doctype=doctype,
            docname=docname,
            show_email_dialog=1,
        )
    else:
        frappe.response["filename"] = _("Product Excel") + ".xlsx"
        frappe.response["filecontent"] = out.getvalue()
        frappe.response["type"] = "binary"
