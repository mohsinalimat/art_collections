from __future__ import unicode_literals
import frappe
from frappe import _
import functools
from frappe.utils import nowdate,add_days
from frappe.utils import getdate,format_date
import json
from frappe.desk.notifications import get_filters_for
from frappe.desk.reportview import get_match_cond

@frappe.whitelist()
def get_sales_person_based_on_address(address=None):
    if address:
        sales_person=frappe.db.sql("""select territory.territory_manager as sales_person
from `tabAddress` as address
inner join `tabTerritory` as territory
on address.territory=territory.name
where address.name=%s""",address,as_dict=True)
        return sales_person[0] if sales_person else None
    else:
        return None


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_filtered_address_list(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql(
		"""SELECT
				parent
			FROM
				`tabDynamic Link`
			WHERE
				parenttype = 'Address'and
				link_doctype =%(doctype)s and 
				link_name = %(name)s
		limit {start}, {page_len}""".format(
			match_cond=get_match_cond(doctype), start=start, page_len=page_len
		),
		{"txt": "%{0}%".format(txt), "_txt": txt.replace("%", ""), "name": filters["name"], "doctype": filters["doctype"]},
	)


@frappe.whitelist()
def get_address_list(name,doctype):
        filters = [
                ["Dynamic Link", "link_doctype", "=", doctype],
                ["Dynamic Link", "link_name", "=", name],
                ["Dynamic Link", "parenttype", "=", "Address"],
        ]
        address_list = frappe.get_all("Address", filters=filters, fields=["*"])

        address_list = sorted(address_list,
                key = functools.cmp_to_key(lambda a, b:
                        (int(a.is_primary_address - b.is_primary_address)) or
                        (1 if a.modified - b.modified else 0)), reverse=True)
        return address_list if address_list else None


@frappe.whitelist(allow_guest=True)
def get_value(parent=None):
        # from frappe.desk.treeview import get_children,get_all_nodes
        # parent='All Catalogue'
        # parent='2019'
        # parent='nos_collections_festives'
        catalogue =get_children("Catalogue Directory Art",parent)
        print(catalogue)
        return catalogue
        # universe=[]
        # for x in catalogue:
        #         print('YYY',x.get('title'))
        #         title=x.get('image')
        #         universe.append(title)
        # return universe	


@frappe.whitelist()
def get_all_nodes(doctype, parent, tree_method, **filters):
	'''Recursively gets all data from tree nodes'''

	if 'cmd' in filters:
		del filters['cmd']

	filters.pop('data', None)

	tree_method = frappe.get_attr(tree_method)

	if not tree_method in frappe.whitelisted:
		frappe.throw(_("Not Permitted"), frappe.PermissionError)

	data = tree_method(doctype, parent, **filters)
	out = [dict(parent=parent, data=data)]

	if 'is_root' in filters:
		del filters['is_root']
	to_check = [d.get('value') for d in data if d.get('expandable')]

	while to_check:
		parent = to_check.pop()
		data = tree_method(doctype, parent, is_root=False, **filters)
		out.append(dict(parent=parent, data=data))
		for d in data:
			if d.get('expandable'):
				to_check.append(d.get('value'))

	return out

@frappe.whitelist()
def get_children(doctype, parent='', **filters):
	parent_field = 'parent_' + doctype.lower().replace(' ', '_')
	filters=[['ifnull(`{0}`,"")'.format(parent_field), '=', parent],
		['docstatus', '<' ,'2']]

	doctype_meta = frappe.get_meta(doctype)
	data = frappe.get_list(doctype, fields=[
		'name as value',
                'website_image as image',
		'{0} as title'.format(doctype_meta.get('title_field') or 'name'),
		'is_group as expandable'],
		filters=filters,
		order_by='name')

	return data

#not used
@frappe.whitelist()
def get_wish_list_names():
	from erpnext.e_commerce.shopping_cart.cart import get_party
	# from erpnext.shopping_cart.cart import get_party
	party = get_party()
	return frappe.db.get_all('Wish List Name',filters={'customer':party.name},fields='wish_list_name', order_by='wish_list_name asc',as_list=True)

@frappe.whitelist()
def update_cart(item_code, qty, additional_notes=None, with_items=False):
	# from erpnext.shopping_cart.cart import apply_cart_settings,set_cart_count,get_cart_quotation,_get_cart_quotation,get_shopping_cart_menu
	from erpnext.e_commerce.shopping_cart.cart import apply_cart_settings,set_cart_count,get_cart_quotation,_get_cart_quotation,get_shopping_cart_menu
	from frappe.utils import cint, flt
	quotation = _get_cart_quotation()

	empty_card = False
	qty = flt(qty)
	if qty == 0:
		quotation_items = quotation.get("items", {"item_code": ["!=", item_code]})
		if quotation_items:
			quotation.set("items", quotation_items)
		else:
			empty_card = True

	else:
		quotation_items = quotation.get("items", {"item_code": item_code})
		if not quotation_items:
			quotation.append("items", {
				"doctype": "Quotation Item",
				"item_code": item_code,
				"qty": qty,
				"additional_notes": additional_notes
			})
		else:
# quantity is cumulated
			quotation_items[0].qty = quotation_items[0].qty + qty
			quotation_items[0].additional_notes = additional_notes

	apply_cart_settings(quotation=quotation)

	quotation.flags.ignore_permissions = True
	quotation.payment_schedule = []
	if not empty_card:
		quotation.save()
	else:
		quotation.delete()
		quotation = None

	set_cart_count(quotation)

	context = get_cart_quotation(quotation)

	if cint(with_items):
		return {
			"items": frappe.render_template("templates/includes/cart/cart_items.html",
				context),
			"taxes": frappe.render_template("templates/includes/order/order_taxes.html",
				context),
		}
	else:
		return {
			'name': quotation.name,
			'shopping_cart_menu': get_shopping_cart_menu(context)
		}	

#Helper for finding item qty
def get_qty_in_stock(item_code, item_warehouse_field, warehouse=None):
	from erpnext.utilities.product import get_price, adjust_qty_for_expired_items
	in_stock, stock_qty = 0, ''
	is_stock_item = frappe.db.get_value("Item", item_code,"is_stock_item")
	template_item_code= frappe.db.get_value("Item", item_code,"variant_of")
	if not warehouse:
		warehouse = frappe.db.get_value("Item", item_code, item_warehouse_field)

	if not warehouse and template_item_code and template_item_code != item_code:
		warehouse = frappe.db.get_value("Item", template_item_code, item_warehouse_field)
	if warehouse:
		p_warehouse = frappe.get_doc("Warehouse", warehouse)
		stock_qty = frappe.db.sql("""
			select SUM(GREATEST(S.actual_qty - S.reserved_qty - S.reserved_qty_for_production - S.reserved_qty_for_sub_contract, 0) / IFNULL(C.conversion_factor, 1))
			from tabBin S
			inner join `tabItem` I on S.item_code = I.Item_code
			left join `tabUOM Conversion Detail` C on I.sales_uom = C.uom and C.parent = I.Item_code
			where S.item_code=%s and S.warehouse in ( select name from `tabWarehouse`
			where lft >= %s and rgt <= %s )
			""",(item_code, p_warehouse.lft, p_warehouse.rgt))
		if stock_qty:
			stock_qty = adjust_qty_for_expired_items(item_code, stock_qty, warehouse)
			if stock_qty:
				if stock_qty[0][0]:
					in_stock = stock_qty[0][0] > 0 and 1 or 0
	return frappe._dict({"in_stock": in_stock, "stock_qty": stock_qty, "is_stock_item": is_stock_item})




# @frappe.whitelist()
# def convert_pre_to_normal_item(item_name):
# 	item_doc=frappe.get_doc('Item',item_name)
# 	if item_doc.is_pre_item_art==1:
# 		from art_collections.ean import calc_check_digit,compact
# 		from stdnum import ean
# 		from frappe.model.rename_doc import rename_doc
# 		id = frappe.db.sql("""SELECT (max(t1.item_code) + 1) id FROM `tabItem` t1 WHERE  cast(t1.item_code AS UNSIGNED)!=0 and t1.item_code like '79%'""")[0][0] or 79000
# 		if id:
# 			id=str(int(id))
# 			new=rename_doc('Item',old=item_doc.name,new=id, merge=False)
# 			# new
# 			item_doc=frappe.get_doc('Item',new)
# 			item_doc.is_pre_item_art=0
# 			item_doc.is_stock_item=1
# 			item_doc.is_sales_item=1
# 			domain='3700091'
# 			code_brut=compact(domain+item_doc.item_code)
# 			key=calc_check_digit(code_brut)
# 			barcode=code_brut+key
# 			if (ean.is_valid(str(barcode))==True):
# 				row = item_doc.append('barcodes', {})
# 				row.barcode=barcode
# 				row.barcode_type='EAN'
# 				item_doc.save(ignore_permissions=True)
# 			return new







# def update_flag_table_from_pricing_rule(self,method):
# 	if self.item_flag_icon_art:
# 		flag=self.item_flag_icon_art
# 		valid_from=self.valid_from
# 		valid_to=self.valid_upto
# 		if self.apply_on=='Item Code' and self.items:
# 			for item in self.items:
# 				doc = frappe.get_doc('Item', item.item_code)
# 				found=False
# 				if doc.website_item_flag_icon_art:
# 					for image in doc.website_item_flag_icon_art:
# 						if image.flag==flag and image.reference == self.name:
# 							found=True
# 				if found == False:
# 					row = doc.append('website_item_flag_icon_art', {})
# 					row.flag=flag
# 					row.valid_from=valid_from
# 					row.valid_to=valid_to
# 					row.reference=self.name
# 					doc.save(ignore_permissions=True)		
# 		elif self.apply_on=='Item Group' and self.item_groups:
# 			for item_groups in self.item_groups:
# 				items=frappe.db.get_list('Item', filters={'item_group': ['=', item_groups.item_group]})
# 				for item in items:
# 					print('---',item.name)
# 					doc = frappe.get_doc('Item', item.name)
# 					found=False
# 					for image in doc.website_item_flag_icon_art:
# 						if image.flag==flag and image.reference == self.name:
# 							print('found')
# 							found=True
# 					if found == False:
# 						print('not found')
# 						row = doc.append('website_item_flag_icon_art', {})
# 						row.flag=flag
# 						row.valid_from=valid_from
# 						row.valid_to=valid_to
# 						row.reference=self.name
# 						doc.save(ignore_permissions=True)					
# 		else:
# 			return
# 	else:
# 		return


def autoname_issue_type(self,method):
	if self.category_art:
		existing_issue=frappe.db.get_list('Issue Type',filters={'category_art': self.category_art,'name':self.name})
		if existing_issue:
			frappe.throw(_('Duplicate record'))

						

def sales_order_from_shopping_cart(self,method):
	if self.order_type=='Shopping Cart':
		frappe.db.set_value(self.doctype, self.name, "workflow_state", "To Deliver and Bill")






@frappe.whitelist()
def pos_so_get_series():
	return frappe.get_meta("Sales Order").get_field("naming_series").options or ""

@frappe.whitelist()
def get_color_code_of_item(item_code):
	color="orange"
	disabled=frappe.db.get_value('Item', item_code, 'disabled')
	if disabled==1:
		color="red"
		return color
	else:
		count=frappe.db.count('Purchase Order Item', {'item_code': item_code})
		if count>0:
			color="green"
			return color
		else:
			color="orange"
			return color


@frappe.whitelist()
def get_average_values_for_item(item_code=None):
	result={}
	result.update(get_average_daily_outgoing_art(item_code))
	result.update(get_average_delivery_days_art(item_code))
	return result

def get_average_daily_outgoing_art(item_code=None):
    if item_code:
        average_daily_outgoing_art=frappe.db.sql("""select 
		ROUND(sum(qty) /DATEDIFF(DATE_ADD(CURRENT_DATE,INTERVAL 1 DAY),min(tso.posting_date)),2) as average_daily_outgoing_art
from `tabSales Invoice` tso 
inner join `tabSales Invoice Item` as tsi
on tso.name = tsi.parent
and tso.docstatus = 1
and tsi.item_code =%s""",item_code,as_dict=True)
        return average_daily_outgoing_art[0] if average_daily_outgoing_art else None
    else:
        return None			

def get_average_delivery_days_art(item_code=None):
	# Logic updated as per ID #317
	# get average diff in date betweeen last modified of sales confirmation and posting date of purchase receipt
	if item_code:
		avg_of_last_3_pr = frappe.db.sql("""
			with fn as
			(
				select 
				ROW_NUMBER() OVER (ORDER BY tpr.posting_date desc) rn ,
					tpri.item_code , tpr.posting_date , tpo.transaction_date , tsc.modified ,
					tpr.name , tsc.name sc_name
				from `tabPurchase Receipt Item` tpri 
				inner join `tabPurchase Receipt` tpr on tpr.name = tpri.parent
				inner join `tabPurchase Order` tpo on tpo.name = tpri.purchase_order and tpo.docstatus = 1
				left join `tabSales Confirmation` tsc on tsc.purchase_order = tpo.name 
			    where tpri.item_code = %s
			) 
 			select avg(DATEDIFF(fn.posting_date,fn.modified)) avg_delay from fn where fn.rn < 4
			-- select fn.posting_date , fn.modified , DATEDIFF(fn.posting_date,fn.modified) ,
			-- fn.name , fn.sc_name
			-- from fn where fn.rn < 4 order by fn.modified
""",(item_code,))
		return avg_of_last_3_pr and avg_of_last_3_pr[0][0] or 0
	return 0



@frappe.whitelist()
def get_actual_delivery_delay_days_art(supplier=None):
    if supplier:
        actual_delivery_delay_days_art=frappe.db.sql("""select 
		AVG(delay_days) as actual_delivery_delay_days from  (
select po.name,DATEDIFF(min(pr.posting_date), po.transaction_date)as delay_days from `tabPurchase Order` po  
inner join `tabPurchase Receipt Item` pri on po.name = pri.purchase_order and po.docstatus = 1 and po.supplier = %s
inner join `tabPurchase Receipt`  pr on pr.name = pri.parent and pr.docstatus = 1  
group by po.name ) t""",supplier,as_dict=True)
        return actual_delivery_delay_days_art[0] if actual_delivery_delay_days_art else None
    else:
        return None			


@frappe.whitelist()
@frappe.read_only()
def get_open_count(doctype, name, items=None):
	"""Get open count for given transactions and filters

	:param doctype: Reference DocType
	:param name: Reference Name
	:param transactions: List of transactions (json/dict)
	:param filters: optional filters (json/list)"""

	if frappe.flags.in_migrate or frappe.flags.in_install:
		return {"count": []}

	doc = frappe.get_doc(doctype, name)
	doc.check_permission()
	meta = doc.meta
	links = meta.get_dashboard_data()

	# compile all items in a list
	if items is None:
		items = []
		for group in links.transactions:
			items.extend(group.get("items"))

	if not isinstance(items, list):
		items = json.loads(items)

	out = []
	for d in items:
		if d in links.get("internal_links", {}):
			continue

		filters = get_filters_for(d)
		fieldname = links.get("non_standard_fieldnames", {}).get(d, links.get("fieldname"))
		data = {"name": d}
		if filters:
			# get the fieldname for the current document
			# we only need open documents related to the current document
			filters[fieldname] = name
			total = len(
				frappe.get_all(d, fields="name", filters=filters, distinct=True, ignore_ifnull=True)
			)
			data["open_count"] = total

		total = len(
			frappe.get_all(
				d, fields="name", filters={fieldname: name}, distinct=True, ignore_ifnull=True
			)
		)
		data["count"] = total
		out.append(data)

	out = {
		"count": out,
	}

	if not meta.custom:
		module = frappe.get_meta_module(doctype)
		if hasattr(module, "get_timeline_data"):
			out["timeline_data"] = module.get_timeline_data(doctype, name)

	return out		