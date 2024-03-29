from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cstr
from art_collections.item_controller import get_cbm_per_outer_carton
from art_collections.item_controller import get_qty_of_outer_cartoon

def request_for_quotation_custom_validation(self,method):
	fill_item_pack_details(self)
	

def fill_item_pack_details(self):
	total_cbm_art=0	
	for item in self.items:
		total_outer_cartons_art=0

		total_outer_cartons_art=flt(item.stock_qty/(get_qty_of_outer_cartoon(item.item_code))) if get_qty_of_outer_cartoon(item.item_code) else total_outer_cartons_art
		item.total_outer_cartons_art=total_outer_cartons_art
		
		item.cbm_per_outer_art=flt(get_cbm_per_outer_carton(item.item_code))

		if total_outer_cartons_art!=0 and item.cbm_per_outer_art:
			item.total_cbm=flt(total_outer_cartons_art*item.cbm_per_outer_art)
			total_cbm_art+=item.total_cbm

	self.total_cbm_art=total_cbm_art
	twenty_foot_filling_percentage=frappe.db.get_single_value('Art Collections Settings', 'filling_percentage_for_20_foot_container') or 28
	forty_foot_filling_percentage=frappe.db.get_single_value('Art Collections Settings', 'filling_percentage_for_40_foot_container') or 63	
	self.filling_percentage_of_20_foot_container_art=(total_cbm_art*100)/twenty_foot_filling_percentage
	self.filling_percentage_of_40_foot_container_art=(total_cbm_art*100)/forty_foot_filling_percentage				




@frappe.whitelist()
def get_pdf(doctype, name, supplier):
    from frappe.utils.print_format import download_pdf
    from erpnext.buying.doctype.request_for_quotation.request_for_quotation import get_rfq_doc
    doc = get_rfq_doc(doctype, name, supplier)
    if doc:
        download_pdf(doctype, name, format="RFQ Art Pdf", doc=doc)

