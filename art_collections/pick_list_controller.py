from __future__ import unicode_literals

import math
import frappe
from frappe.utils import cint, now
from erpnext.stock.doctype.pick_list.pick_list import PickList
from frappe import _, throw
from openpyxl import Workbook, load_workbook
import openpyxl
import io
from art_collections.controllers.excel import add_images, attach_file, write_xlsx
from erpnext.stock.doctype.pick_list import pick_list


class CustomPickList(PickList):
    def __init__(self, *args, **kwargs):
        super(CustomPickList, self).__init__(*args, **kwargs)
        pick_list.get_available_item_locations_for_other_item = (
            get_available_item_locations_for_other_item
        )

    @frappe.whitelist()
    def set_item_locations(self, save=False):
        # set flag for use in get_available_item_locations_for_other_item to sort by priority
        for d in self.locations or []:
            if d.get("sales_order"):
                frappe.flags.pick_list_sales_order = d.sales_order
                break
        super(CustomPickList, self).set_item_locations(save)


def get_available_item_locations_for_other_item(
    item_code, from_warehouses, required_qty, company
):
    """
    Override erpnext pick_list fn to implement priority in warehouse locations.
    Handles only non serial, non batch items
    """

    conditions = [
        "tw.company = %s",
        "item_code = %s",
        "actual_qty > 0",
    ]

    if from_warehouses:
        conditions += [
            "tw.name in ({})".format(",".join(["'%s'"] * len(from_warehouses)))
        ]

    sales_order = frappe.flags.pick_list_sales_order
    is_commercial_operation_cf = sales_order and frappe.db.get_value(
        "Sales Order", sales_order, "is_commercial_operation_cf"
    )

    if not sales_order:
        # order by creation , as per erpnext original fn
        order_by = "creation"
    # custom ordering priority_wise
    elif is_commercial_operation_cf:
        # commercial: order by -ve first then +ve
        order_by = "if(tw.picklist_priority_cf < 0, -10000 * tw.picklist_priority_cf,tw.picklist_priority_cf) DESC"
    else:
        # basic: ignore -ve priority and order by priority
        conditions += ["tw.picklist_priority_cf > 0 "]
        order_by = "tw.picklist_priority_cf DESC"

    conditions = " and ".join(conditions)

    item_locations = frappe.db.sql(
        """
        select 
            warehouse , actual_qty as qty 
        from tabBin tb
        inner join tabWarehouse tw on tb.warehouse = tw.name 
        where {conditions}
        order by {order_by}
        limit %s
    """.format(
            conditions=conditions,
            order_by=order_by,
        ),
        tuple(
            [company, item_code] + (from_warehouses or []) + [math.ceil(required_qty)]
        ),
        as_dict=True,
    )

    return item_locations


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_user_with_picker_role(
    doctype, txt, searchfield, start, page_len, filters, as_dict
):
    picker_role = frappe.db.get_value(
        "Art Collections Settings", "Art Collections Settings", "picker_role"
    )
    valid_user_list = frappe.db.sql(
        """
    select user.name,user.full_name from  `tabUser` user
inner join `tabHas Role` role
on user.name=role.parent
where role.role = %(picker_role)s
            AND user.`name` like %(txt)s
        ORDER BY
            if(locate(%(_txt)s, user.name), locate(%(_txt)s, user.name), 99999), user.name
        LIMIT
            %(start)s, %(page_len)s""",
        {
            "txt": "%%%s%%" % txt,
            "_txt": txt.replace("%", ""),
            "start": start,
            "page_len": frappe.utils.cint(page_len),
            "picker_role": picker_role,
        },
        as_dict=as_dict,
    )
    return valid_user_list


def validate_pick_list(doc, name):
    if doc.is_new():
        doc.flags.create_insufficient_items_excel = 1


def on_update_pick_list(doc, name):
    if cint(doc.flags.create_insufficient_items_excel):
        create_insufficient_items(doc.name)


@frappe.whitelist()
def create_insufficient_items(docname):
    """make excel with items where Qty to pick as per Stock UOM  >  item doctype. saleable_qty_cf
    Qty to pick as per Stock UOM  = from  SO item : Qty as per Stock UOM - Picked Qty (in Stock UOM)
    """
    from art_collections.controllers.excel.sales_order import get_excel_data

    so_name = frappe.db.get_value("Pick List Item", {"parent": docname}, "sales_order")

    data, columns, fields, currency = get_excel_data("Sales Order", so_name)

    if not data:
        frappe.msgprint("Insuffucient Items excel not created.")

    excel_rows, images = [columns], [""]
    for d in data:
        if d.saleable_qty_cf < d.stock_qty:
            excel_rows.append([d.get(f) for f in fields])
            images.append(d.get("image_url"))

    wb = openpyxl.Workbook()
    write_xlsx(
        excel_rows, "Insufficient Items", wb, [20] * len(excel_rows[0]), write_0=1
    )
    add_images(images, workbook=wb, worksheet="Insufficient Items", image_col="U")

    def _get_file_name():
        return "Insufficient_Items_SO_{}_{}.xlsx".format(
            docname,
            now()[:16].replace(" ", "-").replace(":", ""),
        )

    # make attachment
    out = io.BytesIO()
    wb.save(out)
    attach_file(
        out.getvalue(),
        doctype="Pick List",
        file_name=_get_file_name(),
        docname=docname,
        show_email_dialog=0,
    )

    return
