from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cstr
from art_collections.item_controller import get_cbm_per_outer_carton
from art_collections.item_controller import get_qty_of_outer_cartoon

def supplier_quotation_custom_validation(self,method):
	fill_item_pack_details(self)

def fill_item_pack_details(self):
	total_cbm_art=0
	
	for item in self.items:
		item.total_outer_cartons_art=flt(item.stock_qty*(get_qty_of_outer_cartoon(item.item_code)))
		item.cbm_per_outer_art=flt(get_cbm_per_outer_carton(item.item_code))

		if item.total_outer_cartons_art!=0 and item.cbm_per_outer_art:
			item.total_cbm=flt(item.total_outer_cartons_art*item.cbm_per_outer_art)
			total_cbm_art+=item.total_cbm

	self.total_cbm_art=total_cbm_art
	self.filling_percentage_of_20_foot_container_art=(total_cbm_art*100)/33
	self.filling_percentage_of_40_foot_container_art=(total_cbm_art*100)/67