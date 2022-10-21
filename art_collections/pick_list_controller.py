from __future__ import unicode_literals
import frappe
from frappe import throw, _
from frappe.utils import today,flt, getdate
from collections import OrderedDict
from frappe.utils.nestedset import get_descendants_of
from frappe.model.mapper import get_mapped_doc

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
def create_pick_list_with_update_breakup_date(source_name, target_doc=None):
	from erpnext.stock.doctype.packed_item.packed_item import is_product_bundle
	from frappe.utils import cint, floor, flt, today
	from erpnext.stock.doctype.pick_list.pick_list import ( 
	get_items_with_location_and_quantity,
	get_available_item_locations_for_serial_and_batched_item,
	get_available_item_locations_for_serialized_item,
	get_available_item_locations_for_batched_item,
	get_available_item_locations_for_other_item
	)

	def get_available_item_locations(
		item_code, from_warehouses, required_qty, company, ignore_validation=False
	):
		# global send_out_of_stock_email
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

		if remaining_qty > 0 and not ignore_validation:
			# set break up date
			frappe.db.set_value('Item',item_code, 'breakup_date_cf', today())
			
			# send_out_of_stock_email=True
			frappe.msgprint(
				_("Item {0} remaining qty is {1} and hence break up date is set to {2}.").format(
					item_code,remaining_qty, today()
				),
				alert=True
			)			
			frappe.msgprint(
				_("{0} units of Item {1} is not available.").format(
					remaining_qty, frappe.get_desk_link("Item", item_code)
				),
				title=_("Insufficient Stock"),
			)

		return locations	

	#  no change
	def aggregate_item_qty(self):
		locations = self.get("locations")
		self.item_count_map = {}
		# aggregate qty for same item
		item_map = OrderedDict()
		for item in locations:
			if not item.item_code:
				frappe.throw("Row #{0}: Item Code is Mandatory".format(item.idx))
			item_code = item.item_code
			reference = item.sales_order_item or item.material_request_item
			key = (item_code, item.uom, reference)

			item.idx = None
			item.name = None

			if item_map.get(key):
				item_map[key].qty += item.qty
				item_map[key].stock_qty += item.stock_qty
			else:
				item_map[key] = item

			# maintain count of each item (useful to limit get query)
			self.item_count_map.setdefault(item_code, 0)
			self.item_count_map[item_code] += item.stock_qty

		return item_map.values()	

	@frappe.whitelist()
	def set_item_locations(self, save=False):
		items = aggregate_item_qty(self)
		self.item_location_map = frappe._dict()

		from_warehouses = None
		if self.parent_warehouse:
			from_warehouses = get_descendants_of("Warehouse", self.parent_warehouse)
		
		#  pass a list of saleable warehouse only
		saleable_warehouse_type=frappe.db.sql("""select DISTINCT(warehouse_type) as warehouse_type  from `tabArt Warehouse Types`  where parent = 'Art Collections Settings' and parentfield  = 'saleable_warehouse_type'""", as_dict=1)
		if len(saleable_warehouse_type) >0:
					saleable_warehouse_type_list = [d.warehouse_type for d in saleable_warehouse_type]	
					from_warehouses = [x.get("name") for x in frappe.get_all("Warehouse", filters={"company": self.company, "warehouse_type" : ["in",saleable_warehouse_type_list]}, fields=["name"])]	
		
		# Create replica before resetting, to handle empty table on update after submit.
		locations_replica = self.get("locations")

		# reset
		self.delete_key("locations")
		for item_doc in items:
			item_code = item_doc.item_code

			self.item_location_map.setdefault(
				item_code,
				get_available_item_locations(
					item_code, from_warehouses, self.item_count_map.get(item_code), self.company
				),
			)

			locations = get_items_with_location_and_quantity(
				item_doc, self.item_location_map, self.docstatus
			)

			item_doc.idx = None
			item_doc.name = None

			for row in locations:
				location = item_doc.as_dict()
				location.update(row)
				self.append("locations", location)

	# no change
	def update_item_quantity(source, target, source_parent) -> None:
		picked_qty = flt(source.picked_qty) / (flt(source.conversion_factor) or 1)
		qty_to_be_picked = flt(source.qty) - max(picked_qty, flt(source.delivered_qty))

		target.qty = qty_to_be_picked
		target.stock_qty = qty_to_be_picked * flt(source.conversion_factor)

	# no change
	def update_packed_item_qty(source, target, source_parent) -> None:
		qty = flt(source.qty)
		for item in source_parent.items:
			if source.parent_detail_docname == item.name:
				picked_qty = flt(item.picked_qty) / (flt(item.conversion_factor) or 1)
				pending_percent = (item.qty - max(picked_qty, item.delivered_qty)) / item.qty
				target.qty = target.stock_qty = qty * pending_percent
				return

	# no change
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

	set_item_locations(doc)
	# doc.save(ignore_permissions=True)
	# print('send_out_of_stock_email',send_out_of_stock_email)
	# if send_out_of_stock_email==True:
	# 	#  send out email, based on calling of breakup date
	# 	make__and_send_so_email_for_out_of_stock_items('Sales Order',source_name,doc.name)
	# 	frappe.msgprint(_("Please send out of stock email for pick list {0}.").format(doc.name), alert=True) 


	return doc

def make__and_send_so_email_for_out_of_stock_items(doctype, docname,picklist_name):
	import io
	import openpyxl
	from frappe.utils import cint, get_site_url, get_url, cstr
	from art_collections.controllers.excel import write_xlsx, attach_file, add_images
	from openpyxl.drawing.image import Image
	from io import BytesIO		

	currency = frappe.db.get_value(doctype, docname, "currency")

	data = frappe.db.sql(
		"""
		select 
			i.item_code , 
			i.item_name ,
			tib.barcode,
			i.customs_tariff_number ,
			tsoi.weight_per_unit ,
			tppd.`length` , 
			tppd.width , 
			tppd.thickness , 
			tsoi.qty, 
			tsoi.uom ,
			tsoi.base_net_rate ,     
			tsoi.stock_uom ,
			tsoi.stock_uom_rate ,
			tsoi.conversion_factor , 
			tsoi.stock_qty , 
			tsoi.base_amount ,
			tip.price_list_rate , 
			tpr.min_qty  pricing_rule_min_qty , 
			tpr.rate pricing_rule_rate ,
			i.is_existing_product_cf ,
			tsoi.total_saleable_qty_cf ,
			case when i.image is null then ''
				when SUBSTR(i.image,1,4) = 'http' then i.image
				else concat('{}',i.image) end image ,
			i.image image_url
		from `tabSales Order` tso 
		inner join `tabSales Order Item` tsoi on tsoi.parent = tso.name
		inner join tabItem i on i.name = tsoi.item_code
		left outer join `tabItem Barcode` tib on tib.parent = i.name 
			and tib.idx  = (
				select min(idx) from `tabItem Barcode` tib2
				where parent = i.name
			)
		left outer join `tabProduct Packing Dimensions` tppd on tppd.parent = i.name 
			and tppd.uom = tsoi.stock_uom
		left outer join `tabPricing Rule` tpr on tpr.is_volume_price_cf = 1
			and tpr.selling = 1 and exists (
				select 1 from `tabPricing Rule Item Code` x 
				where x.parent = tpr.name and x.uom = tsoi.stock_uom and x.item_code = i.item_code)   
		left outer join `tabItem Price` tip 
		on tip.item_code = tsoi.item_code and COALESCE(tip.uom,tsoi.stock_uom) = tsoi.stock_uom 
		and tip.price_list = (
			select value from tabSingles ts
			where doctype = 'Selling Settings' 
			and field = 'selling_price_list'
		)
		where tso.name = %s
	""".format(
			get_url()
		),
		(docname,),
		as_dict=True,
		# debug=True,
	)

	columns = [
		_("Item Code"),
		_("Item Name"),
		_("Barcode"),
		_("HSCode"),
		_("Weight per unit (kg)"),
		_("Length in cm (of stock_uom)"),
		_("Width in cm (of stock_uom)"),
		_("Thickness in cm (of stock_uom)"),
		_("Qté Inner (SPCB)"),
		_("UOM"),
		_("Prix Inner ({})").format(currency),
		_("Stock UOM"),
		_("Qté colisage (UV)"),
		_("Qté totale"),
		_("Prix unité ({})").format(currency),
		_("Amount ({})").format(currency),
		_("Price List Rate ({})").format(currency),
		_("Pricing rule > Min Qty*"),
		_("Pricing rule > Rate*	"),
		_("Photo Link"),
		_("Photo"),
	]

	fields = [
		"item_code",
		"item_name",
		"barcode",
		"customs_tariff_number",
		"weight_per_unit",
		"length",
		"width",
		"thickness",
		"qty",
		"uom",
		"base_net_rate",
		"stock_uom",
		"conversion_factor",
		"stock_qty",
		"stock_uom_rate",
		"base_amount",
		"price_list_rate",
		"pricing_rule_min_qty",
		"pricing_rule_rate",
		"image",
	]

	wb = openpyxl.Workbook()
	excel_rows, images = [columns], [""]
	for d in data:
		if d.total_saleable_qty_cf < d.stock_qty:
			excel_rows.append([d.get(f) for f in fields])
			images.append(d.get("image_url"))
	write_xlsx(excel_rows, "Out of Stock Items", wb, [20] * len(excel_rows[0]), index=1)
	add_images(images, workbook=wb, worksheet="Out of Stock Items", image_col="T")

	out = io.BytesIO()
	wb.save(out)
	attach_file(
		out.getvalue(),
		doctype='Pick List',
		docname=picklist_name,
		show_email_dialog=1,
	)