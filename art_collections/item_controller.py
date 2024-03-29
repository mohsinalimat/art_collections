from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate,add_days,flt,cstr,date_diff
from art_collections.api import get_average_daily_outgoing_art,get_average_delivery_days_art
from frappe.utils import get_link_to_form
from art_collections.art_collections.doctype.photo_quotation.photo_quotation import make_barcode


def item_autoname(self, method):
	if self.get("lead_item_cf"):
		self.name = self.name.split("-")[-1]
		self.item_name = self.item_name or self.item_code

	if self.get("no_barcode_cf")==0:
		barcode_row=self.append("barcodes",{})	
		barcode_row.barcode=make_barcode(self.name.lstrip('ART-ITEM-'))
		barcode_row.barcode_type='EAN'

def item_custom_validation(self,method):
	set_uom_quantity_of_inner_in_outer(self)
	set_weight_for_stock_uom_of_packing_dimensions(self)
	# sync_catalogue_directory_universe_details(self)
	# set_custom_item_name(self)
	# fix : shopping_cart
	# sync_description_with_web_long_description(self)
	# update_flag_table(self)

@frappe.whitelist()
def sync_catalogue_directory_universe_details(self):
	#  add from item --> catalogue
	for item_universe in self.catalogue_directory_art_item_detail_cf:
		found=False
		catalogue=frappe.get_doc('Catalogue Directory Art',item_universe.universe)
		if catalogue.parent_catalogue_directory_art==item_universe.catalogue:
			for item in catalogue.get('items_in_universe'):
				if item.item==self.name:
					item_universe.page_no=item.item_page_no
					found=True
		if found==False:
			universe_item=catalogue.append("items_in_universe",{})
			universe_item.item=self.name
			catalogue.save(ignore_permissions=True)
			frappe.msgprint(_("Item {0} is added to universe {1} under catalogue {2}.")
					.format(self.name,get_link_to_form("Catalogue Directory Art",item_universe.universe),catalogue.parent_catalogue_directory_art), alert=True)	

	# add from catalogue --> item
	item_universe_list=frappe.db.get_list('Item Universe Page Art', filters={'item':self.name},fields=['parent','name','item_page_no'])
	for universe_row in item_universe_list:
			parent_catalogue_directory_art = frappe.db.get_value('Catalogue Directory Art', universe_row.parent, 'parent_catalogue_directory_art')	
			catalogue_type= frappe.db.get_value('Catalogue Directory Art', parent_catalogue_directory_art, 'catalogue_type')	or None
			catalogue_universe=universe_row.parent
			item_page_no=universe_row.item_page_no
			if self.get("catalogue_directory_art_item_detail_cf"):
				for item_universe in self.catalogue_directory_art_item_detail_cf:
					found=False			
					if item_universe.catalogue==parent_catalogue_directory_art and item_universe.universe==catalogue_universe:
						found=True
						break
				if found==False:
					row=self.append("catalogue_directory_art_item_detail_cf",{})
					row.catalogue=parent_catalogue_directory_art
					row.catalogue_type=catalogue_type
					row.universe=catalogue_universe
					row.page_no=item_page_no
					frappe.msgprint(_("Catalogue {0} is with universe {1} is added in item.").format(row.catalogue,row.universe), alert=True)	 

def set_weight_for_stock_uom_of_packing_dimensions(self):
	if self.weight_per_unit:
		for uom in self.product_packing_dimensions_art:
			if uom.uom==self.stock_uom:
				uom.weight=self.weight_per_unit

def set_uom_quantity_of_inner_in_outer(self):
	inner_carton_uom = frappe.db.get_single_value('Art Collections Settings', 'inner_carton_uom')
	outer_carton_uom = frappe.db.get_single_value('Art Collections Settings', 'outer_carton_uom')
	inner_carton_uom_conversion=None
	outer_carton_uom_conversion=None

	if inner_carton_uom and outer_carton_uom:
		for uom in self.uoms:
			if uom.uom==inner_carton_uom:
				inner_carton_uom_conversion=uom.conversion_factor
			elif uom.uom==outer_carton_uom:
				outer_carton_uom_conversion=uom.conversion_factor
	if inner_carton_uom_conversion and outer_carton_uom_conversion:
		self.nb_inner_in_outer_art=flt(outer_carton_uom_conversion/inner_carton_uom_conversion,1)


def set_custom_item_name(self,method):
	list_of_item_name_values= [self.qty_in_selling_pack_art,self.item_group,self.main_design_color_art,self.length_art,self.width_art,self.thickness_art]
	custom_item_name = []
	for d in list_of_item_name_values:
		if d:
			custom_item_name.append(cstr(d))
	custom_item_name = " ".join(custom_item_name)	
	self.previous_suggested_item_name_art=custom_item_name
	if not self.item_name:
		self.item_name=custom_item_name
	elif self.item_name!=custom_item_name:
		self.item_name=custom_item_name


# def sync_description_with_web_long_description(self):
# 	self.web_long_description=self.description

# def update_flag_table(self):
# 	# get new flag values from shopping cart
# 	new_arrival_field=frappe.db.get_single_value('Shopping Cart Settings', 'new_arrival_field_arty')
# 	new_arrival_validity_days=frappe.db.get_single_value('Shopping Cart Settings', 'new_arrival_validity_days_arty')

# 	if self.published_in_website==0:
# 		return
		
# 	# check if existing
# 	if self.website_item_flag_icon_art:
# 		for image in self.website_item_flag_icon_art:
# 			if image.flag==new_arrival_field:
# 				return
# 	# new flag field not found
# 	row = self.append('website_item_flag_icon_art', {})
# 	row.flag=new_arrival_field
# 	row.valid_from=nowdate()
# 	row.valid_to=add_days(nowdate(), new_arrival_validity_days)


@frappe.whitelist()
def update_item_art_dashboard_data():
	days_after_shipping_date = frappe.db.get_single_value('Art Collections Settings', 'days_after_shipping_date') or 0
	items_list=frappe.db.get_list('Item',filters={'has_variants': 0,'is_fixed_asset':0,'is_stock_item':1,'disabled':0},pluck='name')
	for item_code in items_list:
		#  new change done for warehouse group
		total_virtual_stock=None
		total_in_stock=None
		total_salable_qty_for_warehouse_group_other_than_damage_or_reserved=get_total_salable_qty_for_warehouse_group_other_than_damage_or_reserved(item_code)
		if total_salable_qty_for_warehouse_group_other_than_damage_or_reserved and len(total_salable_qty_for_warehouse_group_other_than_damage_or_reserved)>0:
			total_in_stock=total_salable_qty_for_warehouse_group_other_than_damage_or_reserved[0]['saleable_qty']
	
		sold_qty_to_deliver=None
		result_sold_qty_to_deliver=frappe.db.sql("""select sum(so_item.stock_qty-so_item.delivered_qty) as sold_qty_to_deliver from `tabSales Order` so inner join `tabSales Order Item` so_item on so_item.parent =so.name 
		where so.status in ("To Deliver and Bill","To Deliver") and so_item.item_code =%s """,(item_code))
		if result_sold_qty_to_deliver and len(result_sold_qty_to_deliver)>0:
			sold_qty_to_deliver=result_sold_qty_to_deliver[0][0]


		expected_qty_from_po=frappe.db.sql("""SELECT
		sum(po_item.qty)
	FROM
		`tabPurchase Order` as po
	inner join `tabPurchase Order Item` po_item on
		po.name = po_item.parent
	where
		po.docstatus != 2
		and po_item.received_qty <> po_item.stock_qty
		and po.status in ('To Receive', 'To Receive and Bill')
		and po_item.item_code = %s
		and po_item.shipping_date_art is not NULL
		and datediff(po_item.shipping_date_art, CURDATE())<%s
	group by
		po_item.item_code""",(item_code,days_after_shipping_date))

		total_expected_qty_from_po_wo_shipping_date=frappe.db.sql("""SELECT
		sum(po_item.qty)
	FROM
		`tabPurchase Order` as po
	inner join `tabPurchase Order Item` po_item on
		po.name = po_item.parent
	where
		po.docstatus != 2
		and po_item.received_qty <> po_item.stock_qty
		and po.status in ('To Receive', 'To Receive and Bill')
		and po_item.item_code = %s
	group by
		po_item.item_code""",(item_code))

		if len(total_expected_qty_from_po_wo_shipping_date)>0:
			frappe.db.set_value('Item',item_code, 'total_qty_in_purchase_order_cf', flt(total_expected_qty_from_po_wo_shipping_date[0][0]))

		if sold_qty_to_deliver!=None:
			existing_qty_sold_to_deliver_cf=frappe.db.get_value('Item',item_code, 'qty_sold_to_deliver_cf')
			if existing_qty_sold_to_deliver_cf!=sold_qty_to_deliver:
				frappe.db.set_value('Item',item_code, 'qty_sold_to_deliver_cf', sold_qty_to_deliver)

		if total_in_stock!=None:
			existing_total_in_stock_cf = frappe.db.get_value('Item', item_code,'total_in_stock_cf')
			if existing_total_in_stock_cf!=total_in_stock:
				frappe.db.set_value('Item',item_code, 'total_in_stock_cf', total_in_stock)


		if total_in_stock!=None and sold_qty_to_deliver!=None:
			total_virtual_stock=flt(total_in_stock-sold_qty_to_deliver)
		elif total_in_stock!=None:
			total_virtual_stock=flt(total_in_stock)

		if len(expected_qty_from_po)>0 and total_virtual_stock!=None:
			total_virtual_stock=flt(total_virtual_stock+expected_qty_from_po[0][0])

		if total_virtual_stock!=None:
			existing_saleable_qty_cf=frappe.db.get_value('Item',item_code, 'saleable_qty_cf')
			if existing_saleable_qty_cf!=total_virtual_stock:
				frappe.db.set_value('Item',item_code, 'saleable_qty_cf', total_virtual_stock)

# @frappe.whitelist()
# def get_item_art_dashboard_data(item_code):
# 	total_in_stock=get_stock_qty_for_saleable_warehouse(item_code)[0]['saleable_qty']
# 	sold_qty_to_deliver=frappe.db.sql("""select sum(so_item.stock_qty-so_item.delivered_qty) as sold_qty_to_deliver from `tabSales Order` so inner join `tabSales Order Item` so_item on so_item.parent =so.name 
# where so.status in ("To Deliver and Bill","To Deliver") and so_item.item_code =%s """,(item_code))[0][0]
# # 	sold_qty_delivered=frappe.db.sql("""select sum(so_item.delivered_qty) as sold_qty_to_deliver from `tabSales Order` so inner join `tabSales Order Item` so_item on so_item.parent =so.name 
# # where so.status in ("To Deliver and Bill","To Deliver") and so_item.item_code =%s """,(item_code))[0][0]
# 	days_after_shipping_date = frappe.db.get_single_value('Art Collections Settings', 'days_after_shipping_date')

# 	expected_qty_from_po=frappe.db.sql("""SELECT
# 	sum(po_item.qty)
# FROM
# 	`tabPurchase Order` as po
# inner join `tabPurchase Order Item` po_item on
# 	po.name = po_item.parent
# where
# 	po.docstatus != 2
# 	and po_item.received_qty <> po_item.stock_qty
# 	and po.status in ('To Receive', 'To Receive and Bill')
# 	and po_item.item_code = %s
# 	and po_item.shipping_date_art is not NULL
# 	and datediff(po_item.shipping_date_art, CURDATE())<%s
# group by
# 	po_item.item_code""",(item_code,days_after_shipping_date))

# 	print('expected_qty_from_po',expected_qty_from_po,len(expected_qty_from_po))

# 	if sold_qty_to_deliver!=None:
# 		total_virtual_stock=flt(total_in_stock+sold_qty_to_deliver)
# 	else:
# 		total_virtual_stock=flt(total_in_stock)

# 	if len(expected_qty_from_po)>0:
# 		total_virtual_stock=flt(total_in_stock+expected_qty_from_po[0][0])
# 	# avg_daily_outgoing=get_average_daily_outgoing_art(item_code).average_daily_outgoing_art or 0.0
# 	# avg_qty_sold_per_month=flt(avg_daily_outgoing*30)
# 	# avg_delivery_days=flt(get_average_delivery_days_art(item_code))
# 	# day_remaining_with_the_stock=flt(total_in_stock/avg_daily_outgoing) if avg_daily_outgoing!=0.0 else 0.0

# 	data=frappe.render_template("""<ul>
# 	<li>Total in Stock : <b>{{ total_in_stock }}</b></li>
# 	<li>Qty Sold to Deliver : <b>{{ sold_qty_to_deliver | default('None')}}</b></li>
# 	<li>Saleable Qty : <b>{{ total_virtual_stock }}</b></li>
# 	<li>Breakup Date : <b>{{breakup_date}}</b></li>	
# 	</ul>
# """, dict(
# 	total_in_stock = total_in_stock,
# 	sold_qty_to_deliver=sold_qty_to_deliver,
# 	total_virtual_stock=total_virtual_stock,
# 	breakup_date=None
# 	))
# 	return	data	

# @frappe.whitelist()
# def get_all_saleable_warehouse_list():
# 	warehouse_type=frappe.db.sql("""select DISTINCT(warehouse_type) as warehouse_type  from `tabArt Warehouse Types`  where parent = 'Art Collections Settings' and parentfield  in ('reserved_warehouse_type','saleable_warehouse_type')""", as_dict=1)
# 	if len(warehouse_type) <1:
# 		frappe.throw(_('Saleable warehouse are not defined in Art Collections Settings'))
# 		return
# 	warehouse_type = [d.warehouse_type for d in warehouse_type]
# 	return warehouse_type

# @frappe.whitelist()
# def get_saleable_warehouse_list():
# 	warehouse_type=frappe.db.sql("""select DISTINCT(warehouse_type) as warehouse_type  from `tabArt Warehouse Types`  where parent = 'Art Collections Settings' and parentfield  = 'saleable_warehouse_type'""", as_dict=1)
# 	if len(warehouse_type) <1:
# 		frappe.throw(_('Saleable warehouse are not defined in Art Collections Settings'))
# 		return
# 	warehouse_type = [d.warehouse_type for d in warehouse_type]
# 	return warehouse_type

# @frappe.whitelist()
# def get_reserved_warehouse_list():
# 	warehouse_type=frappe.db.sql("""select DISTINCT(warehouse_type) as warehouse_type  from `tabArt Warehouse Types`  where parent = 'Art Collections Settings' and parentfield  = 'reserved_warehouse_type'""", as_dict=1)
# 	if len(warehouse_type) <1:
# 		frappe.throw(_('Saleable warehouse are not defined in Art Collections Settings'))
# 		return
# 	warehouse_type = [d.warehouse_type for d in warehouse_type]
# 	return warehouse_type

# @frappe.whitelist()
# def get_stock_qty_for_saleable_warehouse(item_code):
# 	warehouse_type=frappe.db.sql("""select DISTINCT(warehouse_type) as warehouse_type  from `tabArt Warehouse Types`  where parent = 'Art Collections Settings' and parentfield  in ('reserved_warehouse_type','saleable_warehouse_type')""", as_dict=1)
# 	if len(warehouse_type) <1:
# 		frappe.throw(_('Saleable warehouse are not defined in Art Collections Settings'))
# 		return
# 	warehouse_type = [d.warehouse_type for d in warehouse_type]
# 	total_in_stock=frappe.db.sql("""select COALESCE(sum(B.actual_qty),0) as saleable_qty from tabBin B inner join tabWarehouse WH on B.warehouse = WH.name 
# 	where WH.warehouse_type in ({warehouse_type}) and B.item_code = '{item_code}' """
# 	.format(item_code=item_code,warehouse_type=(', '.join(['%s'] * len(warehouse_type)))),tuple(warehouse_type),as_dict=1)
# 	return total_in_stock 	

@frappe.whitelist()
def allow_order_still_stock_last():
		in_stock_item_list=frappe.db.get_list('Item', filters={
	'is_purchase_item': ['=', 0],
	'is_sales_item': ['=', 1],
	'is_stock_item': ['=', 1],
	'has_variants': ['=', 0],
	'disabled': ['=', 0]
	})
		if len(in_stock_item_list)>0:
			for item in in_stock_item_list:
				saleable_qty_cf=frappe.db.get_value('Item', item.name, 'saleable_qty_cf')
				if saleable_qty_cf:
					if saleable_qty_cf==0:
						eligible_item=frappe.get_doc('Item',item.name)
						eligible_item.is_sales_item=0
						eligible_item.save(ignore_permissions=True)
						print(eligible_item.name,eligible_item.is_sales_item)

@frappe.whitelist()
def get_qty_of_inner_cartoon(item_code):
	inner_carton_uom = frappe.db.get_single_value('Art Collections Settings', 'inner_carton_uom')
	inner_carton_uom_conversion=None
	item=frappe.get_doc('Item',item_code)
	if item and inner_carton_uom:
		for uom in item.uoms:
			if uom.uom==inner_carton_uom:
				inner_carton_uom_conversion=uom.conversion_factor
				break
	return inner_carton_uom_conversion
	
@frappe.whitelist()
def get_qty_of_outer_cartoon(item_code):
	outer_carton_uom = frappe.db.get_single_value('Art Collections Settings', 'outer_carton_uom')
	outer_carton_uom_conversion=None
	item=frappe.get_doc('Item',item_code)
	if item  and outer_carton_uom:
		for uom in item.uoms:
			if uom.uom==outer_carton_uom:
				outer_carton_uom_conversion=uom.conversion_factor
				break
	return outer_carton_uom_conversion		


@frappe.whitelist()
def get_cbm_per_outer_carton(item_code):
	outer_carton_uom = frappe.db.get_single_value('Art Collections Settings', 'outer_carton_uom')
	cbm_per_outer_carton=None
	item=frappe.get_doc('Item',item_code)
	if item  and outer_carton_uom:
		for uom in item.product_packing_dimensions_art:
			if uom.uom==outer_carton_uom:
				cbm_per_outer_carton=uom.cbm
				break
	return cbm_per_outer_carton		

@frappe.whitelist()
def set_default_warehouse_based_on_stock_entry(self,method)	:
	if self.stock_entry_type=='Material Transfer':
		for item in self.get('items'):
			if item.t_warehouse:
				warehouse_type = frappe.db.get_value('Warehouse', item.t_warehouse, 'warehouse_type')
				company = frappe.db.get_value('Warehouse', item.t_warehouse, 'company')
				if warehouse_type=='Picking' and company==self.company:
					item_details=frappe.get_doc('Item',item.item_code)
					for item_default in item_details.get('item_defaults'):
						old_warehouse=item_default.default_warehouse or None
						if item_default.company==self.company and (old_warehouse!=item.t_warehouse or old_warehouse==None):
							# update default warehouse
							frappe.db.set_value('Item Default', item_default.name, 'default_warehouse', item.t_warehouse)
							frappe.msgprint(_("Item {0}: Default warehouse changed from {1} to {2}.".format(item_details.item_name,old_warehouse,frappe.bold(item.t_warehouse))), alert=True)
					if len(item_details.item_defaults)<1:
						# add row
						frappe.msgprint(_("Item {0}: has no item default entry. Hence  warehouse not set to {1}. Please do it manually".format(item_details.item_name,frappe.bold(item.t_warehouse))), alert=True)


def reset_breakup_date(self,method):
	if self.purpose=="Material Receipt":
		for d in self.get("items"):
			breakup_date_cf=frappe.db.get_value('Item',d.item_code, 'breakup_date_cf')
			if breakup_date_cf!=None:
				frappe.db.set_value('Item',d.item_code, 'breakup_date_cf', None)		
				frappe.msgprint(_("Item {0} break up date is set to blank.").format(d.item_code),alert=True)	

@frappe.whitelist()
def get_total_salable_qty_for_warehouse_group_other_than_damage_or_reserved(item_code):
	from frappe.utils.nestedset import get_descendants_of
	reserved_warehouse_group = frappe.db.get_single_value('Art Collections Settings', 'reserved_warehouse_group')
	damage_warehouse_group = frappe.db.get_single_value('Art Collections Settings', 'damage_warehouse_group')

	reserved_warehouse_list = get_descendants_of("Warehouse", reserved_warehouse_group, ignore_permissions=True, order_by="lft")
	damage_warehouse_list = get_descendants_of("Warehouse", damage_warehouse_group, ignore_permissions=True, order_by="lft")
	ignore_warehouse_list = reserved_warehouse_list + damage_warehouse_list
	if ignore_warehouse_list:
		result = frappe.db.sql("""SELECT  COALESCE(sum(bin.actual_qty),0) as saleable_qty from `tabBin` as bin
		inner join `tabWarehouse` as warehouse on warehouse.name=bin.warehouse
		where bin.item_code = '{item_code}' and bin.warehouse not in ({warehouses})  and warehouse.is_group=0
		group by bin.item_code """
		.format(item_code=item_code,warehouses=' ,'.join(['%s']*len(ignore_warehouse_list))),tuple(ignore_warehouse_list),as_dict=1,debug=1)
		return result			

# @frappe.whitelist()
# def get_total_salable_qty_based_on_set_warehouse(item_code,set_warehouse):
# 	from erpnext.stock.doctype.warehouse.warehouse import get_child_warehouses
# 	warehouse_list=get_child_warehouses(set_warehouse)
# 	result = frappe.db.sql("""SELECT  COALESCE(sum(actual_qty),0) as saleable_qty from `tabBin` where item_code = '{item_code}' and warehouse in ({warehouses})  group by item_code """
# 	.format(item_code=item_code,warehouses=' ,'.join(['%s']*len(warehouse_list))),tuple(warehouse_list),as_dict=1,debug=1)
# 	return result		

@frappe.whitelist()
def get_linked_photo_quotation(name):
    for d in frappe.db.sql("""
        select tpq.name 
        from tabItem ti
        inner join `tabLead Item` tli on tli.name = ti.lead_item_cf 
        inner join `tabPhoto Quotation` tpq on tpq.name = tli.photo_quotation 
        where ti.name = %s
        limit 1
    """,(name,)):
        return d[0]