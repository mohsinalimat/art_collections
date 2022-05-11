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
from frappe.model.meta import get_field_precision
from art_collections.item_controller import get_qty_of_inner_cartoon,get_qty_of_outer_cartoon

class SupplierPackingListArt(Document):
	def validate(self):
		self.compute_calculated_fields()
		self.calculate_taxes_and_totals()

	def compute_calculated_fields(self):
		if self.supplier_packing_list_detail:
			cbm_precision = get_field_precision(frappe.get_meta("Product Packing Dimensions").get_field("cbm")) or 3
			for item in self.supplier_packing_list_detail:
				item.cbm_per_outer=flt((flt(item.outer_height)*flt(item.outer_width)*flt(item.outer_thickness))/1000000,cbm_precision)
				item.total_weight=flt(flt(item.weight_per_outer)*flt(item.qty_of_outer),cbm_precision)
				item.total_cbm=flt(flt(item.cbm_per_outer)*flt(item.qty_of_outer),cbm_precision)

	def on_submit(self):
		for item in self.supplier_packing_list_detail:
			if not item.shipment:
				frappe.throw(title=_('Missing value in supplier packing list'),msg=_('Row #{0} : shipment is required.'.format(item.idx)))
			if not item.container:
				frappe.throw(title=_('Missing value in supplier packing list'),msg=_('Row #{0} : container is required.'.format(item.idx)))

	def calculate_taxes_and_totals(self):
		total_qty_of_stock_uom=0
		total_outer_qty=0
		total_cbm=0
		if self.supplier_packing_list_detail!=None:
			for item in self.supplier_packing_list_detail:
				total_qty_of_stock_uom=(flt(item.qty_of_stock_uom) or 0)+total_qty_of_stock_uom
				total_outer_qty=(flt(item.qty_of_outer) or 0)+total_outer_qty
				total_cbm=(flt(item.total_cbm) or 0)+total_cbm
		self.total_qty_of_stock_uom=total_qty_of_stock_uom
		self.total_outer_qty=total_outer_qty
		self.total_cbm=total_cbm

	@frappe.whitelist()
	def validate_excel_uploaded_data_with_po(self,excel_data=None):
		to_remove= []
		import_log=[]
		supplier_packing_list_detail=[]
		self.set("import_log", '')
		self.set("spl_unknown_item", [])
		self.set("supplier_packing_list_detail", [])
		excel_id=8
		editable_fieldname=['supplier_item_code','inner_conversion_factor','outer_conversion_factor','qty_of_outer','qty_as_per_spl','outer_thickness','outer_width',
					'outer_height','weight_per_outer','shipment','container']	
		non_editable_fieldname=['item_code','item_name','purchase_order','po_item_code','stock_uom','qty_of_stock_uom','cbm_per_outer']	

		for excel_row in excel_data:
			import_row={"excel_id":0,"action":"success","message":""}
			found_excel_matching_row=False
			exists_item_code=frappe.db.exists("Item", excel_row.get('item_code'), cache=True)
			exists_po=frappe.db.exists("Purchase Order", excel_row.get('purchase_order'), cache=True)
			exists_po_item=frappe.db.exists("Purchase Order Item", excel_row.get('po_item_code'), cache=True)
			if exists_item_code==None:
				spl_unknown_item_row=self.append('spl_unknown_item',{})
				for x, y in excel_row.items():
					spl_unknown_item_row.update({x:y})
				import_row['excel_id']=excel_id
				import_row['action']=_('moved to unknown items')
				import_row['message']=_('Item Code(item_code): {item_code} doesnot exist'.format(item_code=excel_row.get('item_code')))
				import_log.append(import_row)
			elif exists_po==None:
				spl_unknown_item_row=self.append('spl_unknown_item',{})
				for x, y in excel_row.items():
					spl_unknown_item_row.update({x:y})
				import_row['excel_id']=excel_id
				import_row['action']=_('moved to unknown items')
				import_row['message']=_('Purchase Order(purchase_order): {purchase_order} doesnot exist'.format(purchase_order=excel_row.get('purchase_order')))
				import_log.append(import_row)
			elif exists_po_item==None:
				spl_unknown_item_row=self.append('spl_unknown_item',{})
				for x, y in excel_row.items():
					spl_unknown_item_row.update({x:y})
				import_row['excel_id']=excel_id
				import_row['action']=_('moved to unknown items')
				import_row['message']=_('PO Item Code(po_item_code): {po_item_code} doesnot exist'.format(po_item_code=excel_row.get('po_item_code')))
				import_log.append(import_row)
			else:
				supplier_packing_row=frappe.db.sql("""SELECT po_item.item_code,po_item.item_name,po_item.parent as purchase_order,po_item.name as po_item_code,po_item.stock_uom,
									(po_item.qty-po_item.received_qty)  as qty_of_stock_uom FROM `tabPurchase Order` po inner join `tabPurchase Order Item` po_item
									on po.name=po_item.parent where po.docstatus=1 and po_item.received_qty < po_item.qty and po_item.delivered_by_supplier !=1
										and po_item.name =%s""",(excel_row.get('po_item_code')),as_dict=1,debug=1)
				if len(supplier_packing_row)>0:
					supplier_packing_row=supplier_packing_row[0]									
					if excel_row.get('qty_as_per_spl') and flt(supplier_packing_row.qty_of_stock_uom,2)!=flt(excel_row.get('qty_as_per_spl'),2):
						supplier_packing_row.qty_as_per_spl=excel_row.get('qty_as_per_spl')
						import_row['excel_id']=excel_id
						import_row['action']=_('qty alert')
						import_row['message']=_('{item_code} :: excel(qty_as_per_spl): {qty_as_per_spl} v/s PO qty(qty_of_stock_uom): {qty_of_stock_uom}' \
						.format(item_code=supplier_packing_row.item_code,qty_as_per_spl=excel_row.get('qty_as_per_spl'),qty_of_stock_uom=supplier_packing_row.qty_of_stock_uom))
						import_log.append(import_row)
						import_row={"excel_id":0,"action":"success","message":""}
					uom_inner_conversion=get_qty_of_inner_cartoon(supplier_packing_row.item_code) 
					uom_outer_conversion=get_qty_of_outer_cartoon(supplier_packing_row.item_code)
					if uom_inner_conversion and flt(uom_inner_conversion,3)!=flt(excel_row.get('inner_conversion_factor'),3):
						import_row['excel_id']=excel_id
						import_row['action']=_('conversion factor alert')
						import_row['message']=_('{item_code} :: excel (inner_conversion_factor) {inner_conversion_factor} v/s Item UOM {uom_inner_conversion}' \
						.format(item_code=supplier_packing_row.item_code,inner_conversion_factor=excel_row.get('inner_conversion_factor') or None,uom_inner_conversion=uom_inner_conversion))
						import_log.append(import_row)
						import_row={"excel_id":0,"action":"success","message":""}	
					if uom_outer_conversion and flt(uom_outer_conversion,3)!=flt(excel_row.get('outer_conversion_factor'),3):
						import_row['excel_id']=excel_id
						import_row['action']=_('conversion factor alert')
						import_row['message']=_('{item_code} :: excel (outer_conversion_factor) {outer_conversion_factor} v/s Item UOM {uom_outer_conversion}' \
						.format(item_code=supplier_packing_row.item_code,outer_conversion_factor=excel_row.get('outer_conversion_factor') or None,uom_outer_conversion=uom_outer_conversion))
						import_log.append(import_row)
						import_row={"excel_id":0,"action":"success","message":""}	
					outer_details=get_details_of_outer_carton(supplier_packing_row.item_code)	
					if outer_details:
						for name,value in outer_details.items():
							if excel_row.get(name) !=value:
								import_row['excel_id']=excel_id
								import_row['action']=_('outer carton alert')
								import_row['message']=_('{item_code} :: excel ({excel_outer_field_name}) {excel_outer_carton} v/s Item Product Dimension : {system_outer_carton}' \
								.format(item_code=supplier_packing_row.item_code,excel_outer_field_name=name,excel_outer_carton=excel_row.get(name) or None,system_outer_carton=value))
								import_log.append(import_row)
								import_row={"excel_id":0,"action":"success","message":""}					
					for supplier_packing_field in editable_fieldname:
						if excel_row.get(supplier_packing_field):
							supplier_packing_row.update({supplier_packing_field:excel_row.get(supplier_packing_field)})
					supplier_packing_list_detail.append(supplier_packing_row)
				else:
					# unkown due to criteria
					spl_unknown_item_row=self.append('spl_unknown_item',{})
					for x, y in excel_row.items():
						spl_unknown_item_row.update({x:y})
					import_row['excel_id']=excel_id
					import_row['action']=_('moved to unknown items')
					import_row['message']=_('{po_item_code} : not matching cond: po.docstatus=1 and po_item.received_qty < po_item.qty and po_item.delivered_by_supplier !=1'.format(po_item_code=excel_row.get('po_item_code')))					
					import_log.append(import_row)						
			excel_id+=1
		self.set("import_log",json.dumps(import_log))
		self.set("supplier_packing_list_detail",supplier_packing_list_detail)
		# for unknown_row in self.spl_unknown_item:
		# 	self.supplier_packing_list_detail=[ d  for d in self.supplier_packing_list_detail if d.item_code!=unknown_row.item_code ]
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

def get_details_of_outer_carton(item_code):
	outer_carton_uom = frappe.db.get_single_value('Art Collections Settings', 'outer_carton_uom')
	outer_carton_details=None
	item=frappe.get_doc('Item',item_code)
	if item  and outer_carton_uom:
		for uom in item.product_packing_dimensions_art:
			if uom.uom==outer_carton_uom:
				outer_carton_details={'outer_thickness':uom.thickness,'outer_width': uom.width,'outer_height':uom.length,'weight_per_outer':uom.weight}
				break
	return outer_carton_details	

def set_missing_values(source, target):
	target.run_method("calculate_taxes_and_totals")

@frappe.whitelist()
def make_supplier_packing_list(source_name, target_doc=None):
	def update_item(obj, target, source_parent):
		target.qty_of_stock_uom = flt(obj.qty) - flt(obj.received_qty)
		target.po_item_code=obj.name
		target.inner_conversion_factor=get_qty_of_inner_cartoon(obj.item_code) or 0
		target.outer_conversion_factor=get_qty_of_outer_cartoon(obj.item_code) or 0

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
				"condition": lambda doc: abs(doc.received_qty) < abs(doc.qty) and doc.delivered_by_supplier != 1,
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
	unique_po_item_code=[]
	po_item_alert_msg=[]
	#po_details= [{"name": "PUR-ORD-2022-00021", "items": [{"item_code": "81287", "qty": 10.0, "docname": "a99206b395"}, {"item_code": "10865", "qty": 2.0, "docname": "be95649d5e"}]}]
	po_details=[]
	po_item_qty={}
	for spl_packing_item in spl.supplier_packing_list_detail:
		# get sum qty_as_per_spl of all submitted Supplier Packing List Detail
		supplier_packing_row=frappe.db.sql("""SELECT  sum(packing_list_detail.qty_as_per_spl) as qty_as_per_spl from `tabSupplier Packing List Detail Art` as packing_list_detail
							where packing_list_detail.docstatus =1 and packing_list_detail.qty_as_per_spl > 0 and packing_list_detail.purchase_order=%s and packing_list_detail.po_item_code=%s
							group by packing_list_detail.po_item_code""",(spl_packing_item.purchase_order,spl_packing_item.po_item_code),as_dict=1,debug=1)	
		if spl_packing_item.po_item_code not in unique_po_item_code	:				
			if len(supplier_packing_row)>0:
				qty_as_per_spl=supplier_packing_row[0].qty_as_per_spl
				if spl_packing_item.qty_of_stock_uom!=qty_as_per_spl and spl_packing_item.po_item_code and qty_as_per_spl>0:
					if qty_as_per_spl>0:
						po_found=False
						for po in po_details:
							if po['name'] == spl_packing_item.purchase_order:
								po_item_qty.update({spl_packing_item.po_item_code:flt(qty_as_per_spl)})
								po_found=True
						if po_found==False:
							po_details.append({'name':spl_packing_item.purchase_order,'items':[]})
							po_item_qty.update({spl_packing_item.po_item_code:flt(qty_as_per_spl)})
								
						po_item_alert_msg.append(_("Purchase Order:{0} , Item {1}, qty is updated to {2}." \
						.format(getlink("Purchase Order", spl_packing_item.purchase_order),spl_packing_item.item_name,qty_as_per_spl)))
						found_for_qty_update=True
		unique_po_item_code.append(spl_packing_item.po_item_code)

	if len(po_item_alert_msg)>0:
		if len(po_details)>0:
			#  add all po items of PO and ensure qty change for impcated docname
			for po in po_details:
				po["items"] = []
				original_po_items = frappe.get_doc("Purchase Order", po["name"]).get("items")
				for d in original_po_items:
					item_found=False
					for name,qty in po_item_qty.items():
						if name==d.name:
							item_found=True
							# qty change for impcated docname
							po["items"].append({"item_code": d.item_code, "qty": flt(qty), "docname": d.name})
							break
					if item_found==False:
						po["items"].append({"item_code": d.item_code, "qty": d.qty, "docname": d.name})	
						
		for po in po_details:
			trans_item = json.dumps(
				po['items']
			)
			update_child_qty_rate("Purchase Order", trans_item, po['name'])
		msg='<br>'.join(po_item_alert_msg)
		frappe.msgprint(msg, indicator="green")
	if found_for_qty_update==False:
		frappe.msgprint(_("No Eligible item found for qty update."), indicator="yellow")