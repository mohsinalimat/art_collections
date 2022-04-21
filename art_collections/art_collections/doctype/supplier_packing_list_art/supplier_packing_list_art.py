# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, cstr, flt
import json
from frappe import _
from erpnext.controllers.accounts_controller import update_child_qty_rate
from frappe.utils.csvutils import getlink

class SupplierPackingListArt(Document):
	def validate(self):
		# self.remove_blank_row()
		self.calculate_taxes_and_totals()

	def remove_blank_row(self):
		for item in self.supplier_packing_list_detail:
			if not item.item_code:
				self.supplier_packing_list_detail.remove(item)

	def calculate_taxes_and_totals(self):
		total_qty_of_stock_uom=0
		total_outer_qty=0
		total_cbm=0
		for item in self.supplier_packing_list_detail:
			total_qty_of_stock_uom=(flt(item.qty_of_stock_uom) or 0)+total_qty_of_stock_uom
			total_outer_qty=(flt(item.qty_of_outer) or 0)+total_outer_qty
			total_cbm=(flt(item.total_cbm) or 0)+total_cbm
		self.total_qty_of_stock_uom=total_qty_of_stock_uom
		self.total_outer_qty=total_outer_qty
		self.total_cbm=total_cbm

	@frappe.whitelist()
	def validate_excel_uploaded_data(self,excel_data=None):
		to_remove= []
		import_log=[]
		self.set("import_log", '')
		self.set("spl_unknown_item", [])
		excel_id=8
		editable_fieldname=['supplier_item_code','inner_conversion_factor','outer_conversion_factor','qty_of_outer','qty_as_per_spl','outer_thickness','outer_width',
					'outer_height','cbm_per_outer','weight_per_outer','total_weight','total_cbm','shipment','container']		
		for excel_row in excel_data:
			import_row={"excel_id":0,"action":"success","message":""}
			found_excel_matching_row=False
			exists=frappe.db.exists("Item", excel_row.get('item_code'), cache=True)
			if exists==None:
				spl_unknown_item_row=self.append('spl_unknown_item',{})
				for x, y in excel_row.items():
					spl_unknown_item_row.update({x:y})

				import_row['excel_id']=excel_id
				import_row['action']=_('moved to unknown items')
				import_row['message']=_('Item Code(item_code): {item_code} doesnot exist'.format(item_code=excel_row.get('item_code')))
				import_log.append(import_row)
			else:
				for supplier_packing_row in self.supplier_packing_list_detail:
					if  supplier_packing_row.item_code==excel_row.get('item_code') and  supplier_packing_row.po_item_code==excel_row.get('po_item_code'):
						found_excel_matching_row=True
						if excel_row.get('qty_as_per_spl') and flt(supplier_packing_row.qty_of_stock_uom,2)!=flt(excel_row.get('qty_as_per_spl'),2):
							supplier_packing_row.qty_as_per_spl=excel_row.get('qty_as_per_spl')
							import_row['excel_id']=excel_id
							import_row['action']=_('qty alert')
							import_row['message']=_('excel(qty_as_per_spl): {qty_as_per_spl} v/s PO qty(qty_of_stock_uom): {qty_of_stock_uom}' \
							.format(qty_as_per_spl=excel_row.get('qty_as_per_spl'),qty_of_stock_uom=supplier_packing_row.qty_of_stock_uom))
							import_log.append(import_row)
							import_row={"excel_id":0,"action":"success","message":""}
						uom_inner_conversion=frappe.db.get_value('UOM Conversion Detail',{'parent':supplier_packing_row.item_code,'uom':'Inner Carton' }, 'conversion_factor')
						uom_outer_conversion=frappe.db.get_value('UOM Conversion Detail',{'parent':supplier_packing_row.item_code,'uom':'Outer Carton' }, 'conversion_factor')
						print(flt(uom_inner_conversion,2),flt(excel_row.get('inner_conversion_factor'),2),"flt(uom_inner_conversion,2)!=flt(excel_row.get('inner_conversion_factor'),2)")
						if uom_inner_conversion and flt(uom_inner_conversion,2)!=flt(excel_row.get('inner_conversion_factor'),2):
							import_row['excel_id']=excel_id
							import_row['action']=_('conversion factor alert')
							import_row['message']=_('excel (inner_conversion_factor) {inner_conversion_factor} v/s Item UOM {uom_inner_conversion}' \
							.format(inner_conversion_factor=excel_row.get('inner_conversion_factor') or None,uom_inner_conversion=uom_inner_conversion))
							import_log.append(import_row)
							import_row={"excel_id":0,"action":"success","message":""}	
						if uom_outer_conversion and flt(uom_outer_conversion,2)!=flt(excel_row.get('outer_conversion_factor'),2):
							import_row['excel_id']=excel_id
							import_row['action']=_('conversion factor alert')
							import_row['message']=_('excel (outer_conversion_factor) {outer_conversion_factor} v/s Item UOM {uom_outer_conversion}' \
							.format(outer_conversion_factor=excel_row.get('outer_conversion_factor') or None,uom_outer_conversion=uom_outer_conversion))
							import_log.append(import_row)
							import_row={"excel_id":0,"action":"success","message":""}	
						for supplier_packing_field in editable_fieldname:
							if excel_row.get(supplier_packing_field):
								supplier_packing_row.update({supplier_packing_field:excel_row.get(supplier_packing_field)})
					# else:
					# 	# self.remove(supplier_packing_row)
					# 	if supplier_packing_row.name not in to_remove:
					# 		to_remove.append(supplier_packing_row.name)
					# 	# self.supplier_packing_list_detail=[ d  for d in self.supplier_packing_list_detail if d.name!=supplier_packing_row.name ]
				if found_excel_matching_row==False:
					spl_unknown_item_row=self.append('spl_unknown_item',{})
					for x, y in excel_row.items():
						spl_unknown_item_row.update({x:y})
					import_row['excel_id']=excel_id
					import_row['action']=_('moved to unknown items')
					import_row['message']=_('non-matching PO#(po_item_code): {po_item_code}'.format(po_item_code=excel_row.get('po_item_code')))					
					import_log.append(import_row)
					# to_remove.append(supplier_packing_row)
					
					

			excel_id+=1
		self.set("import_log",json.dumps(import_log))
		# print('to_remove',to_remove)
		# if len(to_remove)>0:
		# 	self.supplier_packing_list_detail=[ d  for d in self.supplier_packing_list_detail if d.name not in to_remove ]
		for unknown_row in self.spl_unknown_item:
			self.supplier_packing_list_detail=[ d  for d in self.supplier_packing_list_detail if d.item_code!=unknown_row.item_code ]
		self.save()
		if (len(import_log)>0):
			frappe.msgprint(
				title=_('Excel Upload Status'),
				msg=_('Please check upload log below.'),
				indicator='yellow'
			)	
		else:
			frappe.msgprint(
				title=_('Excel Upload Status'),
				msg=_('No upload issue found'),
				indicator='green'
			)	

def set_missing_values(source, target):
	target.run_method("calculate_taxes_and_totals")

@frappe.whitelist()
def make_supplier_packing_list(source_name, target_doc=None):
	def update_item(obj, target, source_parent):
		target.qty_of_stock_uom = flt(obj.qty) - flt(obj.received_qty)
		target.po_item_code=obj.name

	doc = get_mapped_doc(
		"Purchase Order",
		source_name,
		{
			"Purchase Order": {
				"doctype": "Supplier Packing List Art",
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Purchase Order Item": {
				"doctype": "Supplier Packing List Detail Art",
				"field_map": {
					"name": "purchase_order_item",
					"parent": "purchase_order",
					"supplier_item_code":"supplier_part_no",
				},
				"postprocess": update_item,
				"condition": lambda doc: abs(doc.received_qty) < abs(doc.qty)
				and doc.delivered_by_supplier != 1,
			},
		},
		target_doc,
		set_missing_values,
	)

	return doc

@frappe.whitelist()
def update_po_item_qty_based_on_qty_as_per_spl(spl_packing_list):
	spl=frappe.get_doc('Supplier Packing List Art',spl_packing_list)
	found_for_qty_update=False
	for spl_packing_item in spl.supplier_packing_list_detail:
		if spl_packing_item.qty_of_stock_uom!=spl_packing_item.qty_as_per_spl and spl_packing_item.po_item_code and spl_packing_item.qty_as_per_spl>0:
			qty = frappe.db.get_value('Purchase Order Item', spl_packing_item.po_item_code,'qty')
			if qty!=spl_packing_item.qty_as_per_spl :
				trans_item = json.dumps(
					[
						{
							"item_code": spl_packing_item.item_code,
							"qty": flt(spl_packing_item.qty_as_per_spl),
							"docname": spl_packing_item.po_item_code,
						},
					]
				)
				update_child_qty_rate("Purchase Order", trans_item, spl_packing_item.purchase_order)
				frappe.msgprint(_("Purchase Order:{0} , Item {1}, qty is updated to {2}." \
				.format(getlink("Purchase Order", spl_packing_item.purchase_order),spl_packing_item.item_name,spl_packing_item.qty_as_per_spl)), indicator="green")
				found_for_qty_update=True
	if found_for_qty_update==False:
		frappe.msgprint(_("No Eligible item found for qty update."), indicator="yellow")
