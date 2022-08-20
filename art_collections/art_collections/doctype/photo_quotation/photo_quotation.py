# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

from distutils.log import debug
from attr import field, fields
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, cstr, cint, add_days, today, add_to_date
import json
from art_collections.controllers.excel import write_xlsx, attach_file, add_images
import openpyxl
import io
from erpnext import get_default_company
from frappe.model.mapper import get_mapped_doc
from art_collections.ean import calc_check_digit, compact, is_valid


class PhotoQuotation(Document):
    def validate(self):
        if frappe.db.exists(
            "Lead Item",
            {"photo_quotation": self.name, "is_disabled": 0, "is_sample_validated": 1},
        ):
            self.status = "Sample Validated"

    @frappe.whitelist()
    def get_lead_items(self, conditions=None):
        columns = get_lead_item_fields()

        data = frappe.db.sql(
            """select {} from `tabLead Item` where photo_quotation = %s {}""".format(
                ", ".join([d.fieldname for d in columns]),
                conditions and " and %s" % conditions or "",
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

    @frappe.whitelist()
    def create_items(self):
        items = frappe.db.sql(
            """
			select name , {}
			from `tabLead Item`
			where is_sample_validated = 1 and status <> 'Item Created' 
			and photo_quotation = %s
		""".format(
                ",".join(LEAD_ITEM_MANDATORY_FIELDS)
            ),
            (self.name,),
            as_dict=True,
        )

        invalid_items = [
            d for d in items if [x for x in LEAD_ITEM_MANDATORY_FIELDS if not d.get(x)]
        ]
        if invalid_items:
            frappe.throw(
                _(
                    "Please complete {} for these items: {}".format(
                        ", ".join(LEAD_ITEM_MANDATORY_FIELDS),
                        ", ".join([d.name for d in invalid_items]),
                    )
                )
            )

        if not items:
            frappe.throw(_("No items to create."))

        for d in items:
            source = frappe.get_doc("Lead Item", d.name)
            self.make_item(source, self.supplier)
            source.db_set("status", "Item Created")

        if len(items):
            self.db_set("status", "Item Created")

        return len(items)

    def make_item(self, source, supplier):
        def postprocess(source, target, source_parent):
            # target.nb_inner_in_outer_art = 120
            pass

        # TODO: remove in release
        # frappe.delete_doc("Item", source.get("name"))

        uom = frappe.db.get_single_value("Art Collections Settings", "inner_carton_uom")
        target_doc = {}
        item = get_mapped_doc(
            "Lead Item",
            source.get("name"),
            {
                "Lead Item": {
                    "doctype": "Item",
                    "postprocess": postprocess,
                    "field_map": {
                        "name": "item_code",
                        "lead_item_name": "item_name",
                        "is_need_photo_for_packaging": "need_photo_for_packaging_cf",
                        "packaging_description_excel": "packaging_description_cf",
                        "other_language": "other_language_cf",
                        "description1": "description_1_cf",
                        "description2": "description_2_cf",
                        "description3": "description_3_cf",
                        "designation": "excel_designation_cf",
                        "selling_pack_qty": "qty_in_selling_pack_art",
                        "uom": "stock_uom",
                        "item_length": "length_art",
                        "item_width": "width_art",
                        "item_thickness": "thickness_art",
                        "packing_type": "packing_type_art",
                        "is_racking_bag": "racking_bag_art",
                        "min_order_qty": "min_order_qty",
                    },
                },
            },
            target_doc,
        )

        from frappe.model.naming import make_autoname

        item.item_code = make_autoname("#####.")

        item.insert()

        uom = frappe.db.get_single_value("Art Collections Settings", "inner_carton_uom")
        item.append(
            "uoms",
            {
                "uom": uom,
                "conversion_factor": source.get("inner_qty"),
            },
        )

        item.append(
            "supplier_items",
            {
                "supplier": supplier,
                "supplier_part_no": source.get("supplier_part_no"),
                # "supplier_item_description":"supplier_item_description"
            },
        )

        item.append(
            "barcodes", {"barcode_type": "EAN", "barcode": make_barcode(item.item_code)}
        )

        for d in range(1, 4):
            if source.get("product_material" + cstr(d)):
                item.append(
                    "item_components_art",
                    {
                        "matiere": source.get("product_material" + cstr(d)),
                        "percentage": source.get("percentage" + cstr(d)),
                    },
                )
        item.save()

        if cint(source.get("unit_price")):
            frappe.get_doc(
                {
                    "doctype": "Item Price",
                    "item_code": item.item_code,
                    "valid_from": source.get("valid_from"),
                    "price_list_rate": source.get("unit_price"),
                    "price_list": frappe.db.get_single_value(
                        "Buying Settings", "buying_price_list"
                    ),
                }
            ).insert()

        if cint(source.get("item_price")):
            frappe.get_doc(
                {
                    "doctype": "Item Price",
                    "item_code": item.item_code,
                    "price_list_rate": source.get("item_price"),
                    "valid_from": source.get("item_price_valid_from"),
                    "price_list": frappe.db.get_single_value(
                        "Selling Settings", "selling_price_list"
                    ),
                }
            ).insert()

        # insert pricing rules
        if cint(source.get("pricing_rule_price")):
            rule = frappe.get_doc(
                {
                    "doctype": "Pricing Rule",
                    "title": "{} Pricing Rule".format(item.item_code),
                    "apply_on": "Item Code",
                    "price_or_product_discount": "Price",
                    "selling": 1,
                    "min_qty": source.get("pricing_rule_qty"),
                    "rate_or_discount": "Rate",
                    "rate": source.get("pricing_rule_price"),
                    "valid_from": source.get("pricing_rule_valid_from"),
                }
            )
            rule.append("items", {"item_code": item.item_code, "uom": "Selling Pack"})
            rule.insert()

    @frappe.whitelist()
    def delete_all_lead_items(self):
        for d in frappe.db.get_all("Lead Item", {"photo_quotation": self.name}):
            frappe.delete_doc("Lead Item", d.name)
        frappe.db.commit()

    @frappe.whitelist()
    def create_purchase_order(self):

        items = frappe.db.sql(
            """
			select name , uom , selling_pack_qty 
			from `tabLead Item`
			where is_po_created = 0 and status = 'Item Created' 
		""",
            as_dict=True,
        )

        if not items:
            frappe.throw(_("No items in Photo Quotation to create Purchase Order"))

        po_name = frappe.db.exists("Purchase Order", {"photo_quotation_cf": self.name})

        if po_name:
            po = frappe.get_doc("Purchase Order", po_name)
        else:
            po = frappe.get_doc(
                {
                    "doctype": "Purchase Order",
                    "supplier": self.supplier,
                    "transaction_date": today(),
                }
            )

        default_warehouse = frappe.db.get_single_value(
            "Stock Settings", "default_warehouse"
        )

        for d in items:
            po.append(
                "items",
                {
                    "item_code": d.name,
                    "schedule_date": add_to_date(today(), days=7),
                    "warehouse": default_warehouse,
                    "stock_uom": d.uom,
                    "uom": d.uom,
                    "qty": 1,
                },
            )
        po.save()
        self.db_set("status", "PO Created")
        return po.name

    @frappe.whitelist()
    def create_sales_confirmation(self):
        for d in frappe.db.sql(
            """
			select 
				tpo.name purchase_order , tsc.name sales_confirmation
			from `tabPurchase Order` tpo 
			inner join `tabPhoto Quotation` tpq on tpq.name = tpo.photo_quotation_cf and tpq.name = %s
			left outer join `tabSales Confirmation` tsc on tsc.purchase_order = tpo.name;
		""",
            (self.name,),
            as_dict=True,
        ):
            if d.sales_confirmation:
                doc = frappe.get_doc("Sales Confirmation", d.sales_confirmation)
            else:
                doc = frappe.get_doc(
                    {
                        "doctype": "Sales Confirmation",
                        "purchase_order": d.purchase_order,
                        "supplier": self.supplier,
                        "transaction_date": "",
                        "confirmation_date": "",
                        # item_code
                        # supplier_part_no
                        # image
                        # barcode
                        # supplier_item_description_ar
                        # item_name
                        # packing_type_art
                        # qty_in_selling_pack_art
                        # qty_per_inner
                        # qty_per_outer
                        # qty
                        # rate
                        # amount
                        # total_outer_cartons_art
                        # cbm_per_outer_art
                        # total_cbm
                        # customs_tariff_number
                    }
                )

        return []

    @frappe.whitelist()
    def get_supplier_email(self, template="all"):
        # make supplier file and attach to PQ doc
        content = get_items_xlsx(self.name, template, with_xlsx_template=1)

        # create doc attachment and open email dialog in client
        attach_file(
            content,
            doctype=self.doctype,
            docname=self.name,
            file_name=get_file_name(self.name, template),
            email_template=EMAIL_TEMPLATES.get(template),
            show_email_dialog=1,
            callback="supplier_quotation_email_callback",
        )


def get_file_name(name, template):
    return "{}-{}-{}.xlsx".format(
        name,
        frappe.unscrub(template),
        now()[:16].replace(" ", "-").replace(":", ""),
    )


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


@frappe.whitelist()
def import_lead_item_photos():
    docname = frappe.form_dict.docname
    folder = frappe.form_dict.folder or "Home"

    doc = frappe.get_doc(
        {"doctype": "Lead Item", "uom": "Selling Pack", "photo_quotation": docname}
    )
    filename = docname + "_" + frappe.local.uploaded_filename

    doc.insert(ignore_permissions=True)

    ret = frappe.get_doc(
        {
            "doctype": "File",
            "attached_to_doctype": doc.doctype,
            "attached_to_name": doc.name,
            "attached_to_field": "item_photo",
            "folder": folder,
            "file_name": filename,
            "file_url": frappe.form_dict.file_url,
            "is_private": 0,
            "content": frappe.local.uploaded_file,
        }
    )
    ret.save(ignore_permissions=True)

    doc.db_set("item_photo", ret.get("file_url"))

    return ret


def get_items_xlsx(docname, template_for="all", with_xlsx_template=False):
    fields = TEMPLATES.get(template_for) or TEMPLATES.get("all")
    data = frappe.db.sql(
        """
		select {} from `tabLead Item` where photo_quotation = %s {}""".format(
            ", ".join([f for _, f in fields]), CONDITIONS.get(template_for) or ""
        ),
        (docname,),
        as_list=1,
    )

    excel_rows = [[d for d, f in fields]] + list(data)
    images = [""] + [d[1] for d in data]

    from frappe.modules import get_doc_path
    import os

    file_path, skip_rows = None, 0

    if with_xlsx_template and template_for in XLSX_TEMPLATES:
        file_path = os.path.join(
            get_doc_path("art_collections", "doctype", "Photo Quotation"),
            XLSX_TEMPLATES.get(template_for)["filename"],
        )
        skip_rows = XLSX_TEMPLATES.get(template_for)["skip_rows"]

        if XLSX_TEMPLATES.get(template_for, {}).get("skip_header"):
            excel_rows = excel_rows[1:]
            images = images[1:]

    wb = write_xlsx(
        excel_rows,
        sheet_name="Lead Items",
        file_path=file_path,
        column_widths=[20] * len(fields),
        skip_rows=skip_rows,
    )

    add_images(
        images, workbook=wb, worksheet="Lead Items", image_col="B", skip_rows=skip_rows
    )

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


@frappe.whitelist()
def download_lead_items_template(docname, template):
    frappe.response["filename"] = get_file_name(docname, template)
    frappe.response["filecontent"] = get_items_xlsx(docname, template)
    frappe.response["type"] = "binary"


def make_barcode(item_code):
    barcode_domain = frappe.db.get_single_value(
        "Art Collections Settings", "barcode_domain"
    )
    code_brut = compact(barcode_domain + item_code)
    barcode = code_brut + calc_check_digit(code_brut)
    return is_valid(barcode) and barcode or None


@frappe.whitelist()
def supplier_quotation_email_callback(docname):
    frappe.db.set_value("Photo Quotation", docname, "status", "Replied")


XLSX_TEMPLATES = {
    "supplier_quotation": {
        "filename": "photo_quotation_to_supplier_template.xlsx",
        "skip_rows": 6,
        "skip_header": 1,
    }
}

EMAIL_TEMPLATES = {
    "supplier_quotation": "Photo Quotation Supplier Notification",
    "supplier_sample_request": "Photo Quotation Supplier Request for Sample Notification",
}

CONDITIONS = {
    "all": "",
    "supplier_quotation": " and (disabled = 0 and is_quoted = 0)",
    "supplier_sample_request": " and (disabled = 0 and is_quoted = 1 and sample_validated = 0)",
}

TEMPLATES = {
    "all": [(d.label, d.fieldname) for d in get_lead_item_fields()],
    "supplier_quotation": [
        ("Item #", "name"),
        ("Photo", "item_photo"),
        ("Description", "description"),
        ("Product Material", "product_material1"),
        ("Pourcentage", "percentage1"),
        ("Product Material 2", "product_material2"),
        ("Pourcentage 2", "percentage2"),
        ("Product Material 3", "product_material3"),
        ("Pourcentage 3", "percentage3"),
        ("HS CODES", "customs_tariff_number"),
        ("Item length (in cm)", "item_length"),
        ("Item width (in cm)", "item_width"),
        ("Item thickness (in cm)", "item_thickness"),
        ("Packaging type", "packing_type"),
        ("MOQ", "moq"),
        ("Unit price (in $)", "unit_price"),
        ("Inner Qty", "inner_qty"),
        ("Display box?", "is_display_box"),
        ("Special mentions?", "is_special_mentions"),
        ("Test Report", "test_report"),
        ("Abandoned?", "is_abandoned"),
        ("Quoted", "is_quoted"),
        ("Samples Validated?", "sample_validated"),
        ("PO Created?", "is_po_created"),
    ],
    "supplier_sample_request": [
        ("Item #", "name"),
        ("Photo", "item_photo"),
        ("Disabled", "disabled"),
        ("Quoted", "is_quoted"),
        ("Samples validated", "sample_validated"),
        ("PO created", "is_po_created"),
        ("Your Item code", "supplier_part_no"),
        ("Your description", "supplier_item_description"),
        ("Product Material 1", "product_material1"),
        ("Pourcentage 1", "percentage1"),
        ("Product Material 2", "product_material2"),
        ("Pourcentage 2", "percentage2"),
        ("Product Material 3", "product_material3"),
        ("Pourcentage 3", "percentage3"),
        ("HS CODES", "customs_tariff_number"),
        ("Item length", "item_length"),
        ("item width", "item_width"),
        ("Item thickness", "item_thickness"),
        ("Packaging Type", "packing_type"),
        ("Racking bag", "is_racking_bag"),
        ("MOQ", "moq"),
        ("Unit Price (in $)", "unit_price"),
        ("Inner Qty", "inner_qty"),
        ("Display box ?", "is_display_box"),
        ("Spécial mentions ?", "is_special_mentions"),
        ("Certificates Required", "is_certificates_reqd"),
        ("Port Of Loading", "port_of_loading"),
    ],
}

LEAD_ITEM_MANDATORY_FIELDS = [
    "supplier_part_no",
    "unit_price",
    "item_price",
    "item_price_valid_from",
    # "pricing_rule_qty",
    # "pricing_rule_price",
    # "pricing_rule_valid_from",
    "inner_qty",
    "lead_item_name",
    "item_group",
    "description",
    "uom",
    "selling_pack_qty",
    "designation",
    "description1",
    "description2",
    "description3",
]