from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate,add_days,flt,cstr
from art_collections.api import get_average_daily_outgoing_art,get_average_delivery_days_art

def item_custom_validation(self,method):
	pass
	# set_custom_item_name(self)
	# fix : shopping_cart
	# sync_description_with_web_long_description(self)
	# update_flag_table(self)

def set_custom_item_name(self,method):
	list_of_item_name_values= [self.qty_in_selling_pack_art,self.item_group,self.main_design_color_art,self.length_art,self.width_art,self.thickness_art]
	custom_item_name = []
	for d in list_of_item_name_values:
		if d:
			custom_item_name.append(cstr(d))
	custom_item_name = " ".join(custom_item_name)	
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
	total_in_stock=frappe.db.sql("""select COALESCE(sum(actual_qty),0) from tabBin where item_code = %s """,(item_code))[0][0]
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