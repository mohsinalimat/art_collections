from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import nowdate,add_days

def item_custom_validation(self,method):
	sync_description_with_web_long_description(self)
	update_flag_table(self)

def sync_description_with_web_long_description(self):
	self.web_long_description=self.description

def update_flag_table(self):
	# get new flag values from shopping cart
	new_arrival_field=frappe.db.get_single_value('Shopping Cart Settings', 'new_arrival_field_arty')
	new_arrival_validity_days=frappe.db.get_single_value('Shopping Cart Settings', 'new_arrival_validity_days_arty')

	if self.show_in_website==0:
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