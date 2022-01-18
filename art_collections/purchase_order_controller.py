from __future__ import unicode_literals
from operator import add
import frappe
from frappe import _
from frappe.utils import flt, cstr
from frappe.utils import getdate,format_date
from frappe.utils import nowdate,add_days
from frappe.utils.data import today

def purchase_order_custom_validation(self,method):
	fill_item_pack_details(self)

def fill_item_pack_details(self):
	total_cbm_art=0	
	for item in self.items:
		total_outer_cartons_art=0
		if item.total_selling_packs_art and item.nb_selling_packs_in_inner_art>0:
			item.total_inner_cartons_art=flt(item.total_selling_packs_art/item.nb_selling_packs_in_inner_art)

		if item.total_selling_packs_art and item.nb_selling_packs_in_outer_art>0: 
			total_outer_cartons_art=flt(item.total_selling_packs_art/item.nb_selling_packs_in_outer_art)
			item.total_outer_cartons_art=total_outer_cartons_art

		if total_outer_cartons_art!=0 and item.cbm_per_outer_art:
			item.total_cbm=flt(total_outer_cartons_art*item.cbm_per_outer_art)
			total_cbm_art+=item.total_cbm

	self.total_cbm_art=total_cbm_art
	self.filling_percentage_of_20_foot_container_art=(total_cbm_art*100)/33
	self.filling_percentage_of_40_foot_container_art=(total_cbm_art*100)/67			

def purchase_order_custom_on_submit(self,method):
	purchase_order_convert_preorder_item(self,method)

	# previous logic based on expected_delivery_date
	# purchase_order_update_delivery_date_of_item(self,method)

	# previous logic based on schedule_date i.e. required_by_date
	# purchase_order_update_schedule_date_of_item(self,method) 

	# new logic based on schedule_date(i.e. required_by_date) + buffer from settings 
	# new logic doesn't consider expected_delivery_date
	update_availability_date_of_item_based_on_po_required_by_date(self,method)

def purchase_order_convert_preorder_item(self,method):
	purchase_order_items=self.get("items")
	for item in purchase_order_items:	
		item_doc=frappe.get_doc('Item',item.item_code)
		if item_doc.is_pre_item_art==1:
			from art_collections.ean import calc_check_digit,compact
			from stdnum import ean
			from frappe.model.rename_doc import rename_doc
			# id = frappe.db.sql("""SELECT (max(t1.item_code) + 1) id FROM `tabItem` t1 WHERE  cast(t1.item_code AS UNSIGNED)!=0""")[0][0]
			id = frappe.db.sql("""SELECT (max(t1.item_code) + 1) id FROM `tabItem` t1 WHERE  cast(t1.item_code AS UNSIGNED)!=0 and t1.item_code like '79%'""")[0][0] or 79000
			if id:
				id=str(int(id))
				new=rename_doc('Item',old=item_doc.name,new=id, merge=False)
				# new
				item_doc=frappe.get_doc('Item',new)
				item_doc.is_pre_item_art=0
				item_doc.is_stock_item=1
				item_doc.is_sales_item=1
				domain='3700091'
				code_brut=compact(domain+item_doc.item_code)
				key=calc_check_digit(code_brut)
				barcode=code_brut+key
				if (ean.is_valid(str(barcode))==True):
					row = item_doc.append('barcodes', {})
					row.barcode=barcode
					row.barcode_type='EAN'
					item_doc.save(ignore_permissions=True)
			else:
				frappe.throw(_('Conversion failed for Pre Item. New id not found.'))	

def purchase_order_update_delivery_date_of_item(self,method):
	from frappe.utils import add_days
	for item in self.get("items"):
		if item.expected_delivery_date:
			lag_days=45
			availability_date=add_days(item.expected_delivery_date, lag_days)
			frappe.db.set_value('Item', item.item_code, 'availability_date_art', availability_date)				


def purchase_order_update_schedule_date_of_item(self,method):
	if (method=='on_update_after_submit' and self.docstatus==1 ) or method=='on_submit':
		for po_item in self.get("items"):
			availability_date =frappe.db.get_value('Item',po_item.item_code, 'availability_date_art')
			if availability_date==None or getdate(availability_date) < getdate(po_item.schedule_date):
				frappe.db.set_value('Item', po_item.item_code, 'availability_date_art', po_item.schedule_date)
				frappe.msgprint(_("Availability date for item {0} is changed to {1} based on latest required by date."
				.format(po_item.item_name,frappe.bold(format_date(po_item.schedule_date)))), indicator='orage',alert=True)


def update_availability_date_of_item_based_on_po_required_by_date(self,method):
	item_availability_buffer_days=frappe.db.get_single_value('Art Collections Settings', 'item_availability_buffer_days')
	for po_item in self.get("items"):
		old_item_required_by_date=check_previous_po_item_is_not_received(po_item.item_code)
		availability_date =frappe.db.get_value('Item',po_item.item_code, 'availability_date_art')
		required_by_date_with_buffer=add_days(po_item.schedule_date,item_availability_buffer_days)		

		if old_item_required_by_date :
			# previous po is pending
			old_item_required_by_date_with_buffer=add_days(old_item_required_by_date,item_availability_buffer_days)
			if getdate(old_item_required_by_date_with_buffer) < getdate(today()):
				#  previous po required by date with buffer has passed, so set new availability date
				if getdate(required_by_date_with_buffer) > getdate(availability_date):
					# new calculated required by date is greater than availability date , hence change it
					frappe.db.set_value('Item', po_item.item_code, 'availability_date_art', required_by_date_with_buffer)
					frappe.msgprint(_("Availability date for item {0} is changed to {1} based on latest required by date with buffer of {2} days."
					.format(po_item.item_name,frappe.bold(format_date(required_by_date_with_buffer)),item_availability_buffer_days)), indicator='orage',alert=True)				
			else:
				# previous po required by date is futuristic , so nothing
				pass
		else:
			# no previous po pending
			if getdate(required_by_date_with_buffer) > getdate(availability_date):
				# new calculated required by date is greater than availability date , hence change it
				frappe.db.set_value('Item', po_item.item_code, 'availability_date_art', required_by_date_with_buffer)
				frappe.msgprint(_("Availability date for item {0} is changed to {1} based on latest required by date with buffer of {2} days."
				.format(po_item.item_name,frappe.bold(format_date(required_by_date_with_buffer)),item_availability_buffer_days)), indicator='orage',alert=True)		

def check_previous_po_item_is_not_received(item_code)	:
	check_previous_po_item_is_not_received = frappe.db.sql("""SELECT  POI.schedule_date as required_by_date
	FROM  `tabPurchase Order` PO inner join `tabPurchase Order Item` POI 
	on PO.name=POI.parent
	where PO.status in ('To Receive and Bill','To Receive')
	and POI.received_qty =0	and POI.item_code = %s""",(item_code),as_dict=True)
	if len(check_previous_po_item_is_not_received)>0:
		return check_previous_po_item_is_not_received[0].required_by_date
	else:
		return None