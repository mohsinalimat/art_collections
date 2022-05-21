# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import cint, cstr, flt,getdate,add_days,format_date


class ArtShipment(Document):
	def update_item_availability_date(self,item_code,required_by_date_with_buffer,item_availability_buffer_days):
		frappe.db.set_value("Item",item_code,"availability_date_art",required_by_date_with_buffer,)
		frappe.msgprint(_("Availability date for item {0} is changed to {1} based on latest shipping date with buffer of {2} days.".format(
					item_code,frappe.bold(format_date(required_by_date_with_buffer)),item_availability_buffer_days)),indicator="orage",alert=True,)

	def validate(self):
		if self.shipping_date:
			item_availability_buffer_days = frappe.db.get_single_value("Art Collections Settings", "item_availability_buffer_days")
			required_by_date_with_buffer = add_days(self.shipping_date, item_availability_buffer_days)

			po_from_spl_list=frappe.db.get_list('Supplier Packing List Detail Art', filters={'docstatus': 1, 'shipment':self.name},fields=['purchase_order', 'po_item_code','item_name','item_code'],as_dict=1)
			for po in po_from_spl_list:
				po_item = frappe.db.get_value('Purchase Order Item', po.po_item_code, ['shipping_date_art','received_qty'],as_dict=1)		
				# no shippment yet, so update latest date
				if not po_item.shipping_date_art:
					frappe.db.set_value('Purchase Order Item', po.po_item_code, 'shipping_date_art',self.shipping_date)
					frappe.msgprint(_('Purchase Order {0}, Item {1}. Shipping date was blank. \n So, now it is set to {2}'.format(
						po.purchase_order,po.item_name,format_date(self.shipping_date))),alert=1)
					self.update_item_availability_date(po.item_code,required_by_date_with_buffer,item_availability_buffer_days)
				#  earlier shippment arrived as their is received qty, so now change date to latest
				elif po_item.shipping_date_art and po_item.received_qty>0:
					frappe.db.set_value('Purchase Order Item', po.po_item_code, 'shipping_date_art',self.shipping_date)
					frappe.msgprint(_('Purchase Order {0}, Item {1}. Earlier shippment had arrived. \n So, now date is set to latest {2}'.format(
						po.purchase_order,po.item_name,format_date(self.shipping_date))),alert=1)
					self.update_item_availability_date(po.item_code,required_by_date_with_buffer,item_availability_buffer_days)					
				# we have shippment date, but no goods arrived. So set date which ever is earliest
				elif po_item.shipping_date_art and po_item.received_qty==0 and getdate(self.shipping_date) < getdate(po_item.shipping_date_art): 
					frappe.db.set_value('Purchase Order Item', po.po_item_code, 'shipping_date_art',self.shipping_date)
					frappe.msgprint(_('Purchase Order {0}, Item {1}. New shipping date being earliest. \n So, now date is set to latest {2}'.format(
						po.purchase_order,po.item_name,format_date(self.shipping_date))),alert=1)	
					self.update_item_availability_date(po.item_code,required_by_date_with_buffer,item_availability_buffer_days)			
				# no changes done to PO shipping date
				else:
					frappe.msgprint(_('Purchase Order {0}, Item {1}. Existing shipping date is retained. \n So, no changes done due to {2}'.format(
						po.purchase_order,po.item_name,format_date(self.shipping_date))),alert=1)					
		# update forecast date
		for container in self.art_shipment_container:
			po_from_spl_list=frappe.db.get_list('Supplier Packing List Detail Art', filters={'docstatus': 1, 'shipment':self.name,'container':container.container_name}
				,fields=['po_item_code','item_name'],as_dict=1)
			for po in po_from_spl_list:
				frappe.db.set_value('Purchase Order Item', po.po_item_code, 
				{'arrival_forecast_date_art': container.arrival_forecast_date,'arrival_forecast_hour_art': container.arrival_forecast_hour})			
				frappe.msgprint(_('Purchase Order {0}, Item {1}. Arrival forcast data is updated.'.format(
						po.purchase_order,po.item_name)),alert=1)	
