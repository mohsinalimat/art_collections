# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now, cstr, cint, add_days, today, add_to_date
import json
from art_collections.controllers.excel import write_xlsx, attach_file, add_images
import openpyxl
from openpyxl.styles.alignment import Alignment
import io
import os
from openpyxl import load_workbook
from erpnext.accounts.party import get_party_details
import re


LEAD_ITEM_FIELDS = """
'item_photo',
'supplier_part_no',
'supplier_item_description',
'product_material1',
'percentage1',
'product_material2',
'percentage2',
'product_material3',
'percentage3',
'customs_tariff_number',
'item_length',
'item_width',
'item_thickness',
'packing_type',
'racking_bag',
'minimum_order_qty',
'unit_price',
'item_price',
'item_price_valid_from',
'pricing_rule_qty',
'pricing_rule_price',
'pricing_rule_valid_from',
'inner_qty',
'is_display_box',
'is_special_mentions',
'is_certificates_reqd',
'test_report',
'lead_item_name',
'item_group',
'description',
'uom',
'selling_pack_qty',
'is_disabled',
'is_quoted',
'is_abandoned',
'is_sample_validated',
'is_po_created',
'designation',
'description1',
'description2',
'description3',
'other_language',
'is_need_photo_for_packaging',
'packaging_description_excel',
'name',
'photo_quotation'
"""


def get_lead_item_fields():

    fields = frappe.db.sql(
        """
			select fieldname , label , 
			case 
				when fieldtype = 'Attach Image' then 'text'
				when fieldtype in ('Percent', 'Int', 'Currency') then 'numeric' 
				when fieldtype in ('Check') then 'checkbox'
				when fieldtype in ('Date') then 'calendar'
			else 'text' end fieldtype 
			from tabDocField tdf where parent = 'Lead Item' 
			and label is not null
			and fieldname in ({fields})
			ORDER BY FIELD (fieldname,{fields})
	""".format(
            fields=LEAD_ITEM_FIELDS
        ),
        as_dict=True,
        # debug=True,
    )

    return fields + [
        frappe._dict(
            {
                "fieldname": "name",
                "label": "Lead Item#",
                "fieldtype": "text",
            }
        )
    ]


def get_items_xlsx(docname, template="", supplier=None, filters=None):
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

    photo_index = "item_photo" in fields and fields.index("item_photo") or 0

    excel_rows = list(data)
    images = [d[photo_index] for d in data]

    wb = write_xlsx(
        excel_rows,
        sheet_name=SHEET_NAME,
        file_path=template_file_path,
        column_widths=[20] * len(fields),
        skip_rows=skip_rows,
    )

    add_images(
        images,
        workbook=wb,
        worksheet=SHEET_NAME,
        image_col=chr(65 + photo_index),
        skip_rows=skip_rows,
    )
    wb.active = wb[SHEET_NAME]

    # set supplier details
    if template == "lead_items_supplier_template" and supplier:
        wb[SHEET_NAME]["R1"] = re.sub(
            "<br>",
            "\n\n",
            frappe.render_template(
                SUPPLIER_DISPLAY_TEMPLATE,
                get_party_details(supplier, party_type="Supplier"),
            ),
        )
        wb[SHEET_NAME]["R1"].alignment = Alignment(horizontal="left")

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


LEAD_ITEM_CONDITIONS = {
    "supplier_quotation": " and (is_disabled = 0 and is_quoted = 0)",
    "supplier_sample_request": " and (is_disabled = 0 and is_quoted = 1 and is_sample_validated = 0)",
    "create_lead_items": " and (is_disabled = 0 and is_sample_validated = 1)",
    "artyfetes": "",
}

SUPPLIER_DISPLAY_TEMPLATE = """
{{supplier_name}}
{{address_display}}
{{contact_person}}
{{contact_mobile}}
{{contact_email}}
"""
