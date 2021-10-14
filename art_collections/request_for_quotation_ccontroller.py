from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cstr

def request_for_quotation_custom_validation(self,method):
	fill_item_pack_details(self)

def fill_item_pack_details(self):
	for item in self.items:
		total_outer_cartons_art=0
		if item.total_selling_packs_art and item.nb_selling_packs_in_inner_art>0:
			item.total_inner_cartons_art=flt(item.total_selling_packs_art/item.nb_selling_packs_in_inner_art)

		if item.total_selling_packs_art and item.nb_selling_packs_in_outer_art>0:
			total_outer_cartons_art=flt(item.total_selling_packs_art/item.nb_selling_packs_in_outer_art)
			item.total_outer_cartons_art=total_outer_cartons_art

		if total_outer_cartons_art!=0 and item.cbm_per_outer_art:
			item.total_cbm=flt(total_outer_cartons_art*item.cbm_per_outer_art)