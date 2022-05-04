from __future__ import unicode_literals
from locale import currency
import frappe
from frappe import _
import io
import openpyxl
from frappe.utils import cint, get_site_url, get_url
from art_collections.controllers.excel import write_xlsx, attach_file


def on_submit_purchase_order(doc, method=None):
    _make_excel_attachment(doc.doctype, doc.name)


@frappe.whitelist()
def _make_excel_attachment(doctype, docname):

    data, existing_art_works = [], []
    site_url = get_url()

    data = frappe.db.sql(
        """
        select 
            i.item_code, 
            poi.supplier_part_no ,
            tib.barcode,
            i.customs_tariff_number ,
            poi.qty,
            poi.stock_uom , 
            poi.rate , 
			poi.amount ,
            i.is_existing_product_cf ,
            case when i.image is null then ''
                when SUBSTR(i.image,1,4) = 'http' then i.image
                else concat('{}',i.image) end image            
        from `tabPurchase Order Item` poi
        inner join `tabPurchase Order` po on po.name = poi.parent
        inner join tabItem i on i.name = poi.item_code
        left outer join `tabItem Barcode` tib on tib.parent = i.name 
            and tib.idx  = (
                select min(idx) from `tabItem Barcode` tib2
                where parent = i.name
            )
        where poi.parent = %s
    """.format(
            get_url()
        ),
        (docname,),
        as_dict=True,
        # debug=True,
    )

    currency = frappe.db.get_value(doctype, docname, "currency")

    columns = [
        "Item Code",
        "Supplier items",
        "Barcode",
        "HSCode",
        "Quantity",
        "Stock UOM",
        f"Rate ({currency})",
        f"Amount ({currency})",
        "Photo",
    ]

    fields = [
        "item_code",
        "supplier_part_no",
        "barcode",
        "customs_tariff_number",
        "qty",
        "stock_uom",
        "rate",
        "amount",
        "image",
    ]

    wb = openpyxl.Workbook()

    # new art works
    excel_rows = [columns]
    for d in data:
        if not cint(d.is_existing_product_cf):
            excel_rows.append([d.get(f) for f in fields])
    write_xlsx(excel_rows, "New Product", wb, [20] * len(columns))

    # existing art works
    art_works = frappe.db.sql(
        """
    select 
        DISTINCT parent item_code, art_work_name , art_work_attachment
    from `tabExisting Product Art Work`
    where parent in (
    	select item_code from `tabPurchase Order Item` tpoi
    	where parent = %s
    )
    """,
        (docname,),
        as_dict=True,
    )
    art_work_names = frappe.utils.unique([d.art_work_name for d in art_works])
    excel_rows = [columns + art_work_names]
    # print(art_work_names, art_works, excel_rows)
    for d in data:
        if cint(d.is_existing_product_cf):
            excel_rows.append([d.get(f) for f in fields])
            for name in art_work_names:
                for aw in art_works:
                    if aw.item_code == d.item_code and aw.art_work_name == name:
                        excel_rows[-1].append(f"{site_url}{aw.art_work_attachment}")
    write_xlsx(excel_rows, "Existing Product", wb, [20] * len(excel_rows[0]))

    # make attachment
    out = io.BytesIO()
    wb.save(out)
    attach_file(
        out.getvalue(),
        doctype=doctype,
        docname=docname,
    )
