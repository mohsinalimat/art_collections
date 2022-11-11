from __future__ import unicode_literals
import frappe
from frappe import throw, _
import math
from collections import OrderedDict
from frappe.utils.nestedset import get_descendants_of
from frappe.model.mapper import get_mapped_doc

from erpnext.stock.doctype.pick_list.pick_list import PickList


class CustomPickList(PickList):
    @frappe.whitelist()
    def set_item_locations(self, save=False):
        # set flag for use in get_available_item_locations_for_other_item to sort by priority
        for d in self.locations or []:
            frappe.flags.is_commercial_operation_cf = frappe.db.get_value(
                "Sales Order", d.sales_order, "is_commercial_operation_cf"
            )
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

    if frappe.flags.is_commercial_operation_cf:
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
