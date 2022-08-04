# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import json


class PhotoQuotation(Document):
    @frappe.whitelist()
    def get_lead_items(self):
        columns = get_lead_item_fields()

        data = frappe.db.sql(
            """
			select {}
			from `tabLead Item`
            where photo_quotation = %s
		""".format(
                ", ".join([d.fieldname for d in columns])
            ),
            (self.name,),
        )

        return {"columns": columns, "data": data}

    @frappe.whitelist()
    def update_lead_items(self, items=[]):
        fields = [d.fieldname for d in get_lead_item_fields()]
        for d in items:
            if not d[0]:
                continue
            doc = frappe.get_doc("Lead Item", d[0])
            doc.update(dict(zip(fields, d)))
            doc.save()


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
            else 'text' end fieldtype , `options` , `default` , description 
            from tabDocField tdf where parent = 'Lead Item' 
            and label is not null
            and fieldname not in ('naming_series' ,'amended_from')
            order by idx;
    """,
        as_dict=True,
    )


@frappe.whitelist()
def import_lead_item_photos():
    docname = frappe.form_dict.docname
    folder = frappe.form_dict.folder or "Home"

    doc = frappe.get_doc(
        {"doctype": "Lead Item", "uom": "Selling Pack", "photo_quotation": docname}
    )

    doc.insert(ignore_permissions=True)

    ret = frappe.get_doc(
        {
            "doctype": "File",
            "attached_to_doctype": doc.doctype,
            "attached_to_name": doc.name,
            "attached_to_field": "item_photo",
            "folder": folder,
            "file_name": frappe.local.uploaded_filename,
            "file_url": frappe.form_dict.file_url,
            "is_private": 0,
            "content": frappe.local.uploaded_file,
        }
    )
    ret.save(ignore_permissions=True)
    doc.db_set("item_photo", ret.get("file_url"))

    return ret
