# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now, cstr, cint, add_days, today, add_to_date
import json
from art_collections.controllers.excel import write_xlsx, attach_file, add_images
import openpyxl
import io
import os
from openpyxl import load_workbook


def get_lead_item_fields():
    return [
        frappe._dict(
            {
                "fieldname": "name",
                "label": "Lead Item#",
                "fieldtype": "text",
            }
        )
    ] + frappe.db.sql(
        """
			select fieldname , label , 
			case 
				when fieldtype = 'Attach Image' then 'image'
				when fieldtype in ('Percent', 'Int', 'Currency') then 'numeric' 
				when fieldtype in ('Check') then 'checkbox'
				when fieldtype in ('Date') then 'calendar'
			else 'text' end fieldtype 
			from tabDocField tdf where parent = 'Lead Item' 
			and label is not null
			and fieldname not in ('naming_series' ,'amended_from')
			order by idx;
	""",
        as_dict=True,
    )


def get_items_xlsx(docname, template="", filters=None):
    SHEET_NAME = "Lead Items"

    template_file_path = os.path.join(os.path.dirname(__file__), template + ".xlsx")
    if not os.path.exists(template_file_path):
        frappe.throw("No xlsx template found for " + template)

    wb = load_workbook(template_file_path)
    ws = wb["configuration"]
    fields = [col.value for col in ws["B"]][1:]
    skip_rows = ws["C2"].value

    # print(ws.max_row, ws.max_column, fields, skip_rows)

    data = frappe.db.sql(
        """
    	select {} from `tabLead Item` where photo_quotation = %s {}""".format(
            ", ".join(fields), LEAD_ITEM_CONDITIONS.get(filters, "")
        ),
        (docname,),
        as_list=1,
    )

    excel_rows = list(data)
    images = [d[1] for d in data]

    wb = write_xlsx(
        excel_rows,
        sheet_name=SHEET_NAME,
        file_path=template_file_path,
        column_widths=[20] * len(fields),
        skip_rows=skip_rows,
    )

    add_images(
        images, workbook=wb, worksheet=SHEET_NAME, image_col="B", skip_rows=skip_rows
    )
    wb.active = wb[SHEET_NAME]

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


LEAD_ITEM_CONDITIONS = {
    "supplier_quotation": " and (disabled = 0 and is_quoted = 0)",
    "supplier_sample_request": " and (disabled = 0 and is_quoted = 1 and sample_validated = 0)",
    "create_lead_items": " and (disabled = 0 and sample_validated = 1)",
    "artyfetes": "",
}
