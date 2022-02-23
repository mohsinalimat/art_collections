from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate,add_days,flt,cstr
from art_collections.api import get_average_daily_outgoing_art,get_average_delivery_days_art

def item_custom_validation(self,method):
	set_uom_quantity_of_inner_in_outer(self)
	# set_custom_item_name(self)
	# fix : shopping_cart
	# sync_description_with_web_long_description(self)
	# update_flag_table(self)
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


def sync_description_with_web_long_description(self):
	self.web_long_description=self.description

def update_flag_table(self):
	# get new flag values from shopping cart
	new_arrival_field=frappe.db.get_single_value('Shopping Cart Settings', 'new_arrival_field_arty')
	new_arrival_validity_days=frappe.db.get_single_value('Shopping Cart Settings', 'new_arrival_validity_days_arty')

	if self.published_in_website==0:
		return
		
	# check if existing
	if self.website_item_flag_icon_art:
		for image in self.website_item_flag_icon_art:
			if image.flag==new_arrival_field:
				return
	# new flag field not found
	row = self.append('website_item_flag_icon_art', {})
	row.flag=new_arrival_field
	row.valid_from=nowdate()
	row.valid_to=add_days(nowdate(), new_arrival_validity_days)


def set_item_code_for_pre_item(self,method):
	if self.is_pre_item_art==1:
		pre_item_naming_series_art= self.meta.get_field("pre_item_naming_series_art").options
		from frappe.model.naming import make_autoname
		self.name=make_autoname(pre_item_naming_series_art, "", self)
		self.item_code = self.name
		self.is_stock_item=1
		self.include_item_in_manufacturing=0
		self.is_sales_item=0	

@frappe.whitelist()
def get_item_art_dashboard_data(item_code):
	saleable_warehouse_type,reserved_warehouse_type = frappe.db.get_value('Art Collections Settings', 'Art Collections Settings', ['saleable_warehouse_type', 'reserved_warehouse_type'])
	conditions=" 1=1"
	print(saleable_warehouse_type,reserved_warehouse_type,'saleable_warehouse_type,reserved_warehouse_type')
	if saleable_warehouse_type and reserved_warehouse_type:
		conditions=" WH.warehouse_type in ('{0}','{1}')".format(saleable_warehouse_type,reserved_warehouse_type)
	elif saleable_warehouse_type and not reserved_warehouse_type:
		conditions=" WH.warehouse_type = '{0}'".format(saleable_warehouse_type)
	elif not saleable_warehouse_type and reserved_warehouse_type:
		conditions=" WH.warehouse_type = '{0}'".format(reserved_warehouse_type)
	else :
		frappe.throw(_('Saleable warehouse are not defined in Art Collections Settings'))
		return

	total_in_stock=frappe.db.sql("""select COALESCE(sum(B.actual_qty),0) from tabBin B inner join tabWarehouse WH on B.warehouse = WH.name 
	where {conditions} and B.item_code = '{item_code}'""".format(conditions=conditions,item_code=item_code))[0][0]
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
def get_stock_qty_for_saleable_warehouse(item_code):
	saleable_warehouse_type,reserved_warehouse_type = frappe.db.get_value('Art Collections Settings', 'Art Collections Settings', ['saleable_warehouse_type', 'reserved_warehouse_type'])
	conditions=" 1=1"
	if saleable_warehouse_type and reserved_warehouse_type:
		conditions=" WH.warehouse_type in ('{0}','{1}')".format(saleable_warehouse_type,reserved_warehouse_type)
	elif saleable_warehouse_type and not reserved_warehouse_type:
		conditions=" WH.warehouse_type = '{0}'".format(saleable_warehouse_type)
	elif not saleable_warehouse_type and reserved_warehouse_type:
		conditions=" WH.warehouse_type = '{0}'".format(reserved_warehouse_type)
	else :
		frappe.throw(_('Saleable warehouse are not defined in Art Collections Settings'))
		return

	total_in_stock=frappe.db.sql("""select COALESCE(sum(B.actual_qty),0) as saleable_qty from tabBin B inner join tabWarehouse WH on B.warehouse = WH.name 
	where {conditions} and B.item_code = '{item_code}'""".format(conditions=conditions,item_code=item_code),as_dict=1)
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