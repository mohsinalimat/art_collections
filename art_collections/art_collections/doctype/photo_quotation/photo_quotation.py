# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now, cstr, cint, add_days, today, add_to_date, flt
import json
from art_collections.controllers.excel import write_xlsx, attach_file, add_images
from frappe.utils.data import getdate
import openpyxl
import io
from erpnext import get_default_company
from frappe.model.mapper import get_mapped_doc
from art_collections.ean import calc_check_digit, compact, is_valid
from art_collections.art_collections.doctype.photo_quotation.lead_items_excel import (
    get_lead_item_fields,
    get_items_xlsx,
)
from erpnext.e_commerce.doctype.website_item.website_item import (
    make_website_item,
)


class PhotoQuotation(Document):
    def validate(self):
        if frappe.db.exists(
            "Lead Item",
            {"photo_quotation": self.name, "is_disabled": 0, "is_sample_validated": 1},
        ):
            self.status = "Sample Validated"
        self.set_progress()

    def set_progress(self):
        for d in frappe.db.sql(
            """
                select 
                    sum(if(status='Item Created',1,0)) item_created_progress  , 
                    sum(if(status='PO Created',1,0)) po_created_progress  , 
                    sum(if(status='Sample Validated',1,0)) sample_validated_progress  , 
                    count(*) total_count
                    from `tabLead Item` tl 
                where photo_quotation = %s
                """,
            (self.name),
            as_dict=True,
        ):
            for f in [
                "item_created_progress"
                "po_created_progress"
                "sample_validated_progress"
            ]:
                if d.total_count and d.get(f):
                    self.set(f, 100 * d.get(f, 0) / d.total_count)

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
        meta = frappe.get_meta("Lead Item")
        fields = [d.fieldname for d in get_lead_item_fields()]
        for d in items:
            if not d[-1]:
                continue
            doc = frappe.get_doc(
                "Lead Item", {"name": d[-1], "photo_quotation": self.name}
            )
            for idx, f in enumerate(fields):
                value = d[idx]
                # in order to allow overwriting flag = 1 with 0
                is_flag = (
                    meta.get_field(f) and meta.get_field(f).get("fieldtype") == "Check"
                )
                if is_flag:
                    value = cint(value)
                if value or is_flag:
                    doc.update({f: value})

            doc.save()

    @frappe.whitelist()
    def create_items(self):
        items = frappe.db.sql(
            """
			select name , {}
			from `tabLead Item`
			where is_sample_validated = 1 and status <> 'Item Created' 
            and is_disabled = 0
			and photo_quotation = %s
		""".format(
                ",".join(LEAD_ITEM_MANDATORY_FIELDS)
            ),
            (self.name,),
            as_dict=True,
        )

        invalid_items = []
        for d in items:
            missing = list(filter(lambda x: not d.get(x), LEAD_ITEM_MANDATORY_FIELDS))
            if missing:
                invalid_items.append(d.name + ": " + ",".join(missing))

        if invalid_items:
            frappe.throw(
                _(
                    "Please complete details for these items: <br><br>{}".format(
                        "<br>".join(invalid_items),
                    )
                )
            )

        if not items:
            frappe.throw(_("No items to create."))

        for d in items:
            source = frappe.get_doc("Lead Item", d.name)
            self.make_item(source, self.supplier)
            source.db_set("status", "Item Created")
            source.db_set("is_item_created", 1)

        if len(items):
            self.db_set("status", "Item Created")
            self.set_progress()

        return len(items)

    def make_item(self, source, supplier):
        def postprocess(source, target, source_parent):
            target.naming_series = None
            target.sales_uom = "Inner Carton"

        FIELD_MAP = {
            "lead_item_name": "item_name",
            "is_need_photo_for_packaging": "need_photo_for_packaging_cf",
            "packaging_description_excel": "packaging_description_cf",
            "other_language": "other_language_cf",
            "description": "description",
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
            "racking_bag": "racking_bag_art",
            "min_order_qty": "min_order_qty",
            "name": "lead_item_cf",
            "item_photo": "image",
            "is_certificates_reqd": "certificates_required_art",
            "is_disabled": "disabled",
            "is_display_box": "display_box_art",
            "is_need_photo_for_packaging": "need_photo_for_packaging_cf",
            "is_special_mentions": "special_mentions_art",
            "item_group": "item_group",
            "minimum_order_qty": "min_order_qty",
        }

        target_doc = {}
        item = get_mapped_doc(
            "Lead Item",
            source.get("name"),
            {
                "Lead Item": {
                    "doctype": "Item",
                    "postprocess": postprocess,
                    "field_map": FIELD_MAP,
                },
            },
            target_doc,
        )

        if frappe.db.exists("Item", {"lead_item_cf": source.get("name")}):
            frappe.db.sql(
                """
                update tabItem set lead_item_cf = NULL
                where lead_item_cf = %s    
            """,
                (source.get("name")),
            )

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
                "supplier_part_description_art": source.get(
                    "supplier_item_description"
                ),
            },
        )

        # barcode is already created in item autoname. create only if not present
        if not [bc for bc in (item.barcodes or []) if bc.barcode_type == "EAN"]:
            item.append(
                "barcodes", {"barcode_type": "EAN", "barcode": make_barcode(item.name)}
            )

        default_warehouse = frappe.db.get_single_value(
            "Art Collections Settings", "default_lead_item_warehouse"
        )
        if default_warehouse:
            for d in item.item_defaults:
                d.default_warehouse = default_warehouse
                break

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

        if flt(source.get("unit_price")) > 0:
            frappe.get_doc(
                {
                    "doctype": "Item Price",
                    "item_code": item.item_code,
                    "uom": item.stock_uom,
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
                    "uom": item.stock_uom,
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
                    "is_volume_price_cf": 1,
                }
            )
            rule.append("items", {"item_code": item.item_code, "uom": "Selling Pack"})
            rule.insert()

        website_item = make_website_item(item)
        frappe.db.set_value("Website Item", website_item[0], "published", 0)
        frappe.db.set_value(
            "Website Item", website_item[0], "website_image", item.image
        )

    @frappe.whitelist()
    def delete_all_lead_items(self):
        for d in frappe.db.get_all("Lead Item", {"photo_quotation": self.name}):
            frappe.delete_doc("Lead Item", d.name)
        frappe.db.commit()

    @frappe.whitelist()
    def create_purchase_order(self):
        items = frappe.db.sql(
            """
			select ti.item_code , tli.uom , tli.selling_pack_qty , tli.minimum_order_qty ,
            tli.name lead_item
			from `tabLead Item` tli
			inner join tabItem ti on ti.lead_item_cf = tli.name  
			where is_po_created = 0 and status = 'Item Created' 
            and tli.photo_quotation = %s
		""",
            (self.name,),
            as_dict=True,
        )

        if not items:
            frappe.throw(_("No items in Photo Quotation to create Purchase Order"))

        po_name = frappe.db.exists("Purchase Order", {"photo_quotation_cf": self.name})

        if po_name:
            po = frappe.get_doc("Purchase Order", po_name)
        else:
            supplier_currency = frappe.db.get_value(
                "Supplier", self.supplier, "default_currency"
            )
            po = frappe.get_doc(
                {
                    "doctype": "Purchase Order",
                    "supplier": self.supplier,
                    "transaction_date": today(),
                    "photo_quotation_cf": self.name,
                    "currency": supplier_currency,
                    "schedule_date": self.required_by_date,
                }
            )

        for d in items:
            if list(
                filter(lambda x: x.item_code == d.item_code, po.get("items") or [])
            ):
                continue
            po.append(
                "items",
                {
                    "item_code": d.item_code,
                    "schedule_date": getdate(),
                    "stock_uom": d.uom,
                    "uom": d.uom,
                    "qty": d.minimum_order_qty,
                    "lead_item_cf": d.lead_item,
                },
            )

        po.save()
        self.db_set("status", "PO Created")
        self.set_progress()
        return po.name

    @frappe.whitelist()
    def get_supplier_email(self, template="", supplier=None, filters=None):
        # make supplier file and attach to PQ doc
        content = get_items_xlsx(
            self.name, template=template, supplier=supplier, filters=filters
        )

        callback = None
        if filters == "supplier_quotation":
            callback = "supplier_quotation_email_callback"
        elif filters == "supplier_sample_request":
            callback = "supplier_sample_request_email_callback"

        email_template = None

        if template == "lead_items_supplier_template":
            if filters == "supplier_quotation":
                email_template = frappe.db.get_single_value(
                    "Art Collections Settings", "photo_quotation_supplier_quotation"
                )
            elif filters == "supplier_sample_request":
                email_template = frappe.db.get_single_value(
                    "Art Collections Settings",
                    "photo_quotation_supplier_sample_request",
                )

        # create doc attachment and open email dialog in client
        attach_file(
            content,
            doctype=self.doctype,
            docname=self.name,
            file_name=get_file_name(self.name, template),
            email_template=email_template,
            show_email_dialog=1,
            callback=callback,
        )


def get_file_name(name, template):
    return "{}-{}-{}.xlsx".format(
        name,
        frappe.unscrub(template),
        now()[:16].replace(" ", "-").replace(":", ""),
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

    duplicate_count = frappe.db.sql(
        """
       select count(*) from tabFile tf where content_hash = %s and name <> %s""",
        (ret.content_hash, ret.name),
    )
    if duplicate_count and cint(duplicate_count[0][0]):
        ret.content_hash = _("Duplicate photo. {0} is already used.").format(
            frappe.local.uploaded_filename
        )

    return ret


@frappe.whitelist()
def download_lead_items_template(docname, template, supplier=None):
    xl_template = "lead_items_art_template"
    if template in ("supplier_quotation", "supplier_sample_request"):
        xl_template = "lead_items_supplier_template"

    frappe.response["filename"] = get_file_name(docname, template)
    frappe.response["filecontent"] = get_items_xlsx(
        docname, template=xl_template or template, filters=template, supplier=supplier
    )
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


@frappe.whitelist()
def supplier_sample_request_email_callback(docname):
    frappe.db.set_value("Photo Quotation", docname, "is_sample_requested", 1)


LEAD_ITEM_MANDATORY_FIELDS = [
    "name",
    "item_photo",
    "description",
    "product_material1",
    "percentage1",
    # "product_material2",
    # "percentage2",
    # "product_material3",
    # "percentage3",
    "customs_tariff_number",
    "item_length",
    "item_width",
    "item_thickness",
    "packing_type",
    "minimum_order_qty",
    "unit_price",
]


def make_items():
    doc = frappe.get_doc("Photo Quotation", "PQ17")
    doc.create_items()
