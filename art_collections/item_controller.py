from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate,add_days,flt,cstr
from art_collections.api import get_average_daily_outgoing_art,get_average_delivery_days_art
from frappe.utils import get_link_to_form



def item_autoname(self, method):
    if self.get("lead_item_cf"):
        self.name = self.name.split("-")[-1]
        self.item_name = self.item_name or self.item_code

def item_custom_validation(self,method):
	set_uom_quantity_of_inner_in_outer(self)
	set_weight_for_stock_uom_of_packing_dimensions(self)
	sync_catalogue_directory_universe_details(self)
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
def get_item_art_dashboard_data(item_code):
	total_in_stock=get_stock_qty_for_saleable_warehouse(item_code)[0]['saleable_qty']
	sold_qty_to_deliver=frappe.db.sql("""select sum(so_item.stock_qty-so_item.delivered_qty) as sold_qty_to_deliver from `tabSales Order` so inner join `tabSales Order Item` so_item on so_item.parent =so.name 
where so.status in ("To Deliver and Bill","To Deliver") and so_item.item_code =%s """,(item_code))[0][0]
	sold_qty_delivered=frappe.db.sql("""select sum(so_item.delivered_qty) as sold_qty_to_deliver from `tabSales Order` so inner join `tabSales Order Item` so_item on so_item.parent =so.name 
where so.status in ("To Deliver and Bill","To Deliver") and so_item.item_code =%s """,(item_code))[0][0]
	if sold_qty_to_deliver!=None:
		total_virtual_stock=flt(total_in_stock-sold_qty_to_deliver)
	else:
		total_virtual_stock=flt(total_in_stock)
	avg_daily_outgoing=get_average_daily_outgoing_art(item_code).average_daily_outgoing_art or 0.0
	avg_qty_sold_per_month=flt(avg_daily_outgoing*30)
	avg_delivery_days=flt(get_average_delivery_days_art(item_code))
	day_remaining_with_the_stock=flt(total_in_stock/avg_daily_outgoing) if avg_daily_outgoing!=0.0 else 0.0

	data=frappe.render_template("""<ul>
	<li>Total in Stock : <b>{{ total_in_stock }}</b></li>
	<li>Qty Sold to Deliver : <b>{{ sold_qty_to_deliver | default('None')}}</b></li>
	<li>Qty Sold Delivered : <b>{{ sold_qty_delivered | default('None')}}</b></li>
	<li>Total Virtual Stock OR Qty available : <b>{{ total_virtual_stock }}</b></li>
	<li>Avg. Qty sold per month : <b>{{ frappe.format(avg_qty_sold_per_month , {'fieldtype': 'Float'}) }}</b></li>
	<li>Avg. Daily Outgoing : <b>{{ avg_daily_outgoing }}</b></li>
	<li>Avg. Delivery Days : <b>{{ avg_delivery_days }}</b></li>	
	<li>Days Remaining With The Stock : <b>{{ frappe.format(day_remaining_with_the_stock , {'fieldtype': 'Float'}) }}</b></li>	
	</ul>
""", dict(
	total_in_stock = total_in_stock,
	sold_qty_to_deliver=sold_qty_to_deliver,
	sold_qty_delivered=sold_qty_delivered,
	total_virtual_stock=total_virtual_stock,
	avg_qty_sold_per_month=avg_qty_sold_per_month,
	avg_daily_outgoing=avg_daily_outgoing,
	avg_delivery_days=avg_delivery_days,
	day_remaining_with_the_stock=day_remaining_with_the_stock
	))
	return	data	

@frappe.whitelist()
def get_all_saleable_warehouse_list():
	warehouse_type=frappe.db.sql("""select DISTINCT(warehouse_type) as warehouse_type  from `tabArt Warehouse Types`  where parent = 'Art Collections Settings' and parentfield  in ('reserved_warehouse_type','saleable_warehouse_type')""", as_dict=1)
	if len(warehouse_type) <1:
		frappe.throw(_('Saleable warehouse are not defined in Art Collections Settings'))
		return
	warehouse_type = [d.warehouse_type for d in warehouse_type]
	return warehouse_type

@frappe.whitelist()
def get_saleable_warehouse_list():
	warehouse_type=frappe.db.sql("""select DISTINCT(warehouse_type) as warehouse_type  from `tabArt Warehouse Types`  where parent = 'Art Collections Settings' and parentfield  = 'saleable_warehouse_type'""", as_dict=1)
	if len(warehouse_type) <1:
		frappe.throw(_('Saleable warehouse are not defined in Art Collections Settings'))
		return
	warehouse_type = [d.warehouse_type for d in warehouse_type]
	return warehouse_type

@frappe.whitelist()
def get_reserved_warehouse_list():
	warehouse_type=frappe.db.sql("""select DISTINCT(warehouse_type) as warehouse_type  from `tabArt Warehouse Types`  where parent = 'Art Collections Settings' and parentfield  = 'reserved_warehouse_type'""", as_dict=1)
	if len(warehouse_type) <1:
		frappe.throw(_('Saleable warehouse are not defined in Art Collections Settings'))
		return
	warehouse_type = [d.warehouse_type for d in warehouse_type]
	return warehouse_type

@frappe.whitelist()
def get_stock_qty_for_saleable_warehouse(item_code):
	warehouse_type=frappe.db.sql("""select DISTINCT(warehouse_type) as warehouse_type  from `tabArt Warehouse Types`  where parent = 'Art Collections Settings' and parentfield  in ('reserved_warehouse_type','saleable_warehouse_type')""", as_dict=1)
	if len(warehouse_type) <1:
		frappe.throw(_('Saleable warehouse are not defined in Art Collections Settings'))
		return
	warehouse_type = [d.warehouse_type for d in warehouse_type]
	total_in_stock=frappe.db.sql("""select COALESCE(sum(B.actual_qty),0) as saleable_qty from tabBin B inner join tabWarehouse WH on B.warehouse = WH.name 
	where WH.warehouse_type in ({warehouse_type}) and B.item_code = '{item_code}' """
	.format(item_code=item_code,warehouse_type=(', '.join(['%s'] * len(warehouse_type)))),tuple(warehouse_type),as_dict=1)
	return total_in_stock 	

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
				total_saleable_qty=get_stock_qty_for_saleable_warehouse(item.name)
				if len(total_saleable_qty)>0:
					if total_saleable_qty[0].saleable_qty==0:
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


