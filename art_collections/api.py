from __future__ import unicode_literals
import frappe
from frappe import _
import functools
from frappe.utils import nowdate,add_days

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
	from erpnext.shopping_cart.cart import get_party
	party = get_party()
	return frappe.db.get_all('Wish List Name',filters={'customer':party.name},fields='wish_list_name', order_by='wish_list_name asc',as_list=True)

@frappe.whitelist()
def update_cart(item_code, qty, additional_notes=None, with_items=False):
	from erpnext.shopping_cart.cart import apply_cart_settings,set_cart_count,get_cart_quotation,_get_cart_quotation,get_shopping_cart_menu
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
	template_item_code, is_stock_item = frappe.db.get_value("Item", item_code, ["variant_of", "is_stock_item"])

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
		

def update_flag_table(self,method):
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

def update_flag_table_from_pricing_rule(self,method):
	if self.item_flag_icon_art:
		flag=self.item_flag_icon_art
		valid_from=self.valid_from
		valid_to=self.valid_upto
		if self.apply_on=='Item Code' and self.items:
			for item in self.items:
				doc = frappe.get_doc('Item', item.item_code)
				found=False
				if doc.website_item_flag_icon_art:
					for image in doc.website_item_flag_icon_art:
						if image.flag==flag and image.reference == self.name:
							found=True
				if found == False:
					row = doc.append('website_item_flag_icon_art', {})
					row.flag=flag
					row.valid_from=valid_from
					row.valid_to=valid_to
					row.reference=self.name
					doc.save(ignore_permissions=True)		
		elif self.apply_on=='Item Group' and self.item_groups:
			for item_groups in self.item_groups:
				items=frappe.db.get_list('Item', filters={'item_group': ['=', item_groups.item_group]})
				for item in items:
					print('---',item.name)
					doc = frappe.get_doc('Item', item.name)
					found=False
					for image in doc.website_item_flag_icon_art:
						if image.flag==flag and image.reference == self.name:
							print('found')
							found=True
					if found == False:
						print('not found')
						row = doc.append('website_item_flag_icon_art', {})
						row.flag=flag
						row.valid_from=valid_from
						row.valid_to=valid_to
						row.reference=self.name
						doc.save(ignore_permissions=True)					
		else:
			return
	else:
		return


def autoname_issue_type(self,method):
	if self.category_art:
		existing_issue=frappe.db.get_list('Issue Type',filters={'category_art': self.category_art,'name':self.name})
		if existing_issue:
			frappe.throw(_('Duplicate record'))

def stock_availability_notification(self,method):
	from frappe.utils.background_jobs import enqueue
	from frappe.contacts.doctype.contact.contact import get_default_contact

	if self.items:
		for item in self.items:
			wishlists= frappe.db.get_list('Quotation', filters={'order_type': ['=', 'Shopping Cart Wish List'],
			'status': ['=', 'Draft']})
			for wishlist in wishlists:
				doc = frappe.get_doc('Quotation', wishlist.name)
				for  quot_item in doc.items:
					if quot_item.item_code == item.item_code and quot_item.is_stock_available_art == 0:
						url=frappe.utils.get_url() + '/art_cart?wish_list=' +doc.wish_list_name
						item_name=quot_item.item_name
						customer=doc.party_name
						template='Stock Availability Notification'
						email_template = frappe.get_doc("Email Template", template)
						args={
							"url":url,
							"item_name":item_name,
							"customer":doc.customer_name
						}
						message = frappe.render_template(email_template.response, args)
						email_to = frappe.db.get_value('Contact', get_default_contact('customer', customer), 'email_id')
						email_args = {
							"recipients": email_to,
							"sender": None,
							"subject": email_template.subject,
							"message": message,
							"now": True,
							}
						enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)						

def sales_order_from_shopping_cart(self,method):
	if self.order_type=='Shopping Cart':
		frappe.db.set_value(self.doctype, self.name, "workflow_state", "To Deliver and Bill")

def purchase_order_update_delivery_date_of_item(self,method):
	from frappe.utils import add_days
	for item in self.get("items"):
		if item.expected_delivery_date:
			lag_days=45
			availability_date=add_days(item.expected_delivery_date, lag_days)
			frappe.db.set_value('Item', item.item_code, 'availability_date_art', availability_date)