from __future__ import unicode_literals
import frappe
from frappe import _
import functools

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
		print(item_code, p_warehouse.lft, p_warehouse.rgt)
		stock_qty = frappe.db.sql("""
			select GREATEST(S.actual_qty - S.reserved_qty - S.reserved_qty_for_production - S.reserved_qty_for_sub_contract, 0) / IFNULL(C.conversion_factor, 1)
			from tabBin S
			inner join `tabItem` I on S.item_code = I.Item_code
			left join `tabUOM Conversion Detail` C on I.sales_uom = C.uom and C.parent = I.Item_code
			where S.item_code=%s and S.warehouse in ( select name from `tabWarehouse`
			where lft >= %s and rgt <= %s )
			""",(item_code, p_warehouse.lft, p_warehouse.rgt))
		if stock_qty:
			stock_qty = adjust_qty_for_expired_items(item_code, stock_qty, warehouse)
			in_stock = stock_qty[0][0] > 0 and 1 or 0

	return frappe._dict({"in_stock": in_stock, "stock_qty": stock_qty, "is_stock_item": is_stock_item})
		