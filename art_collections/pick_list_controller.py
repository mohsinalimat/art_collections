from __future__ import unicode_literals
import frappe
from frappe import throw, _
from erpnext.stock.doctype.pick_list.pick_list import get_available_item_locations_for_serial_and_batched_item,get_available_item_locations_for_serialized_item,get_available_item_locations_for_batched_item,get_available_item_locations_for_other_item
from frappe.utils import today,flt, getdate
from collections import OrderedDict
from frappe.utils.nestedset import get_descendants_of
from frappe.model.mapper import get_mapped_doc

# @frappe.whitelist()
# def get_user_with_picker_role(doctype, txt, searchfield, start, page_length, filters, as_dict):
# 	valid_user_list=[]
# 	picker_role=frappe.db.get_value('Art Collections Settings', 'Art Collections Settings', 'picker_role')
# 	user_lists = frappe.db.get_list('User')
# 	for user in user_lists:
# 		user = frappe.get_doc('User', user.name)
# 		if picker_role:
# 			user_roles=user.get("roles")
# 			for user_role in user_roles:
# 				if user_role.role==picker_role:
# 					valid_user_list.append( (user.name,))
# 		else:
# 			valid_user_list.append( (user.name,))
# 	return valid_user_list


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_user_with_picker_role(doctype, txt, searchfield, start, page_len, filters, as_dict):
	picker_role=frappe.db.get_value('Art Collections Settings', 'Art Collections Settings', 'picker_role')
	valid_user_list= frappe.db.sql("""
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
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace('%', ''),
			'start': start,
			'page_len': frappe.utils.cint(page_len),
			'picker_role': picker_role
		}, as_dict=as_dict)
	return valid_user_list	


@frappe.whitelist()
def update_item_breakup_date(self):
		items,item_count_map = aggregate_item_qty(self)
		from_warehouses = None
		if self.parent_warehouse:
			from_warehouses = get_descendants_of("Warehouse", self.parent_warehouse)


		for item_doc in items:
			item_code = item_doc.item_code
			get_available_item_locations(
					item_code, from_warehouses, item_count_map.get(item_code), self.company
				),


def get_available_item_locations(item_code, from_warehouses, required_qty, company):
	locations = []
	has_serial_no = frappe.get_cached_value("Item", item_code, "has_serial_no")
	has_batch_no = frappe.get_cached_value("Item", item_code, "has_batch_no")

	if has_batch_no and has_serial_no:
		locations = get_available_item_locations_for_serial_and_batched_item(
			item_code, from_warehouses, required_qty, company
		)
	elif has_serial_no:
		locations = get_available_item_locations_for_serialized_item(
			item_code, from_warehouses, required_qty, company
		)
	elif has_batch_no:
		locations = get_available_item_locations_for_batched_item(
			item_code, from_warehouses, required_qty, company
		)
	else:
		locations = get_available_item_locations_for_other_item(
			item_code, from_warehouses, required_qty, company
		)

	total_qty_available = sum(location.get("qty") for location in locations)

	remaining_qty = required_qty - total_qty_available
	if remaining_qty > 0 :
		frappe.db.set_value('Item',item_code, 'breakup_date_cf', today())
		frappe.msgprint(
			_("Item {0} remaining qty is {1} and hence break up date is set to {2}.").format(
				item_code,remaining_qty, today()
			),
			alert=True
		)

	return	

def aggregate_item_qty(self):
	locations = self.get("locations")
	item_count_map = {}
	# aggregate qty for same item
	item_map = OrderedDict()
	for item in locations:
		if not item.item_code:
			frappe.throw("Row #{0}: Item Code is Mandatory".format(item.idx))
		item_code = item.item_code
		reference = item.sales_order_item or item.material_request_item
		key = (item_code, item.uom, reference)

		# item.idx = None
		# item.name = None

		if item_map.get(key):
			item_map[key].qty += item.qty
			item_map[key].stock_qty += item.stock_qty
		else:
			item_map[key] = item

		# maintain count of each item (useful to limit get query)
		item_count_map.setdefault(item_code, 0)
		item_count_map[item_code] += item.stock_qty

	return item_map.values(),item_count_map

@frappe.whitelist()
def create_pick_list_with_update_breakup_date(source_name, target_doc=None):
	from erpnext.stock.doctype.packed_item.packed_item import is_product_bundle

	def update_item_quantity(source, target, source_parent) -> None:
		picked_qty = flt(source.picked_qty) / (flt(source.conversion_factor) or 1)
		qty_to_be_picked = flt(source.qty) - max(picked_qty, flt(source.delivered_qty))

		target.qty = qty_to_be_picked
		target.stock_qty = qty_to_be_picked * flt(source.conversion_factor)

	def update_packed_item_qty(source, target, source_parent) -> None:
		qty = flt(source.qty)
		for item in source_parent.items:
			if source.parent_detail_docname == item.name:
				picked_qty = flt(item.picked_qty) / (flt(item.conversion_factor) or 1)
				pending_percent = (item.qty - max(picked_qty, item.delivered_qty)) / item.qty
				target.qty = target.stock_qty = qty * pending_percent
				return

	def should_pick_order_item(item) -> bool:
		return (
			abs(item.delivered_qty) < abs(item.qty)
			and item.delivered_by_supplier != 1
			and not is_product_bundle(item.item_code)
		)

	doc = get_mapped_doc(
		"Sales Order",
		source_name,
		{
			"Sales Order": {"doctype": "Pick List", "validation": {"docstatus": ["=", 1]}},
			"Sales Order Item": {
				"doctype": "Pick List Item",
				"field_map": {"parent": "sales_order", "name": "sales_order_item"},
				"postprocess": update_item_quantity,
				"condition": should_pick_order_item,
			},
			"Packed Item": {
				"doctype": "Pick List Item",
				"field_map": {
					"parent": "sales_order",
					"name": "sales_order_item",
					"parent_detail_docname": "product_bundle_item",
				},
				"field_no_map": ["picked_qty"],
				"postprocess": update_packed_item_qty,
			},
		},
		target_doc,
	)

	doc.purpose = "Delivery"
	update_item_breakup_date(doc)
	doc.set_item_locations()
	return doc