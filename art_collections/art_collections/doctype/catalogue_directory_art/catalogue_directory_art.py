# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils.nestedset import NestedSet
from frappe.utils import nowdate, cint, cstr
from frappe.model.naming import set_name_by_naming_series
from frappe import _
from frappe.utils.nestedset import NestedSet
from frappe.website.website_generator import WebsiteGenerator
from frappe.website.render import clear_cache
from frappe.website.doctype.website_slideshow.website_slideshow import get_slideshow
from frappe.utils import get_link_to_form
# from erpnext.shopping_cart.product_info import set_product_info_for_website
from erpnext.e_commerce.shopping_cart.product_info import set_product_info_for_website
# from erpnext.utilities.product import get_qty_in_stock
# mostly get_qty_in_stock and get_web_item_qty_in_stock same
from erpnext.utilities.product import get_web_item_qty_in_stock
from six.moves.urllib.parse import quote

class CatalogueDirectoryArt(NestedSet,WebsiteGenerator):
	nsm_parent_field ='parent_catalogue_directory_art'
	website = frappe._dict(
		condition_field = "show_in_website",
		template = "templates/generators/catalogue.html",
		no_cache = 1
	)

	def autoname(self):
		self.name=self.catalogue_directory_art_name

	def validate(self):
		super(CatalogueDirectoryArt, self).validate()
		if not self.parent_catalogue_directory_art and not frappe.flags.in_test:
			if frappe.db.exists("Catalogue Directory Art", _('Catalogues')):
				self.parent_catalogue_directory_art = _('Catalogues')
		self.make_route()
		self.set_title()
		# self.set_universe_catalogue_in_item_description()

	def set_universe_catalogue_in_item_description(self):
		if self.items_in_universe and self.node_type=='Universe':
			# from frappe.utils.nestedset import get_ancestors_of
			result=get_ancestors_of(self.doctype,self.name)
			result.append(self.title or self.name)
			result=cstr(result)
			for item in self.items_in_universe:
				print(item.item,cstr(result))
				description = frappe.db.get_value('Item', item.item, 'description')
				if not(result in description):
					description +=result
					frappe.db.set_value('Item', item.item, 'description',description)




	def set_title(self):
		if not self.title:
			self.title=self.catalogue_directory_art_name

	def on_update(self):
		NestedSet.on_update(self)
		invalidate_cache_for(self)
		self.validate_name_with_item()
		self.validate_one_root()

	def make_route(self):
		'''Make website route'''
		if not self.route:
			self.route = ''
			if self.parent_catalogue_directory_art:
				parent_catalogue_directory_art = frappe.get_doc('Catalogue Directory Art', self.parent_catalogue_directory_art)

				# make parent route only if not root
				if parent_catalogue_directory_art.parent_catalogue_directory_art and parent_catalogue_directory_art.route:
					self.route = parent_catalogue_directory_art.route + '/'

			self.route += self.scrub(self.catalogue_directory_art_name)
			return self.route

	def on_trash(self):
		NestedSet.on_trash(self)
		WebsiteGenerator.on_trash(self)

	def validate_name_with_item(self):
		if frappe.db.exists("Item", self.name):
			frappe.throw(frappe._("An item exists with same name ({0}), please change the node name or rename the item").format(self.name), frappe.NameError)		

	def get_context(self, context):
		context.show_search=True
		context.page_length = cint(frappe.db.get_single_value('Products Settings', 'products_per_page')) or 6
		context.search_link = '/product_search'

		start = int(frappe.form_dict.start or 0)
		if start < 0:
			start = 0
		context.update({
			"items": get_product_list_for_group(product_group = self.name, start=start,
				limit=context.page_length + 1, search=frappe.form_dict.get("search"),parent=self.name,node_type=self.node_type,universe_items=self.items_in_universe),
			"parents": get_parent_item_groups(self.parent_catalogue_directory_art),
			"title": self.title ,
			"name":self.name,
			"type":self.node_type
		})

		if self.slideshow:
			context.update(get_slideshow(self))

		return context


def get_ancestors_of(doctype, name, order_by="lft desc", limit=None):
	"""Get ancestor elements of a DocType with a tree structure"""
	lft, rgt = frappe.db.get_value(doctype, name, ["lft", "rgt"])

	result = [d["title"] or d["name"] for d in frappe.db.get_all(doctype, {"lft": ["<", lft], "rgt": [">", rgt]},
		["name","title"], order_by=order_by, limit_page_length=limit)]

	return result or []

@frappe.whitelist(allow_guest=True)
def get_product_list_for_group(product_group=None, start=0, limit=10, search=None,parent=None,node_type=None,universe_items=None):
	if product_group:
		item_group = frappe.get_cached_doc('Catalogue Directory Art', product_group)
		if item_group.is_group:
			# return child item groups if the type is of "Is Group"
			return get_child_groups_for_list_in_html(item_group, start, limit, search,parent,node_type,universe_items)

	child_groups = ", ".join([frappe.db.escape(i[0]) for i in get_child_groups(product_group)])

	# base query
	query = """select I.name, I.item_name, I.item_code, I.route, I.image, I.website_image, I.thumbnail, I.item_group,
			I.description, I.web_long_description as website_description, I.is_stock_item,
			case when (S.actual_qty - S.reserved_qty) > 0 then 1 else 0 end as in_stock, I.website_warehouse,
			I.has_batch_no
		from `tabItem` I
		left join tabBin S on I.item_code = S.item_code and I.website_warehouse = S.warehouse
		where I.published_in_website = 1
			and I.disabled = 0
			and (I.end_of_life is null or I.end_of_life='0000-00-00' or I.end_of_life > %(today)s)
			and (I.variant_of = '' or I.variant_of is null)
			and (I.item_group in ({child_groups})
			or I.name in (select parent from `tabWebsite Item Group` where item_group in ({child_groups})))
			""".format(child_groups=child_groups)
	# search term condition
	if search:
		query += """ and (I.web_long_description like %(search)s
				or I.item_name like %(search)s
				or I.name like %(search)s)"""
		search = "%" + cstr(search) + "%"

	query += """order by I.weightage desc, in_stock desc, I.modified desc limit %s, %s""" % (start, limit)

	data = frappe.db.sql(query, {"product_group": product_group,"search": search, "today": nowdate()}, as_dict=1)
	data = adjust_qty_for_expired_items(data)

	if cint(frappe.db.get_single_value("Shopping Cart Settings", "enabled")):
		for item in data:
			set_product_info_for_website(item)
	return data

def get_child_groups_for_list_in_html(item_group, start, limit, search,parent,node_type,universe_items):
	search_filters = None
	if search_filters:
		search_filters = [
			dict(name = ('like', '%{}%'.format(search))),
			dict(description = ('like', '%{}%'.format(search)))
		]
	
	data=None
	if node_type =='Catalogue' or node_type =='Root':
		data = frappe.db.get_all('Catalogue Directory Art',
			fields = ['name','title' ,'route', 'description', 'image','is_group','alt_image'],
			filters = dict(
				show_in_website = 1,
				lft = ('>', item_group.lft),
				rgt = ('<', item_group.rgt),
				parent = parent
			),
			or_filters = search_filters,
			order_by = 'weightage desc, name asc',
			start = start,
			limit = limit
		)
	elif node_type=='Universe':
		data=frappe.db.sql("""select 
Item.name,Item.item_name,Item.route,Item.description,Item.image 
from `tabItem Universe Page Art` Univ
inner join `tabItem` Item
on Univ.item=Item.name
where Univ.parent=%s
and Univ.parentfield='items_in_universe'
and Univ.parenttype='Catalogue Directory Art'
and Item.published_in_website=1
order by Univ.idx
limit %s
offset %s""",(parent,limit,start),as_dict=1)
	return data

def adjust_qty_for_expired_items(data):
	adjusted_data = []

	for item in data:
		if item.get('has_batch_no') and item.get('website_warehouse'):
			stock_qty_dict = get_qty_in_stock(
				item.get('name'), 'website_warehouse', item.get('website_warehouse'))
			qty = stock_qty_dict.stock_qty[0][0] if stock_qty_dict.stock_qty else 0
			item['in_stock'] = 1 if qty else 0
		adjusted_data.append(item)

	return adjusted_data


def get_child_groups(item_group_name):
	item_group = frappe.get_doc("'Catalogue Directory Art", item_group_name)
	return frappe.db.sql("""select name
		from `tabCatalogue Directory Art` where lft>=%(lft)s and rgt<=%(rgt)s
			and show_in_website = 1""", {"lft": item_group.lft, "rgt": item_group.rgt})

def get_item_for_list_in_html(context):
	# add missing absolute link in files
	# user may forget it during upload
	if (context.get("website_image") or "").startswith("files/"):
		context["website_image"] = "/" + quote(context["website_image"])

	context["show_availability_status"] = cint(frappe.db.get_single_value('Products Settings',
		'show_availability_status'))

	products_template = 'templates/includes/products_as_list.html'

	return frappe.get_template(products_template).render(context)

def get_group_item_count(item_group):
	child_groups = ", ".join(['"' + i[0] + '"' for i in get_child_groups(item_group)])
	return frappe.db.sql("""select count(*) from `tabItem`
		where docstatus = 0 and published_in_website = 1
		and (item_group in (%s)
			or name in (select parent from `tabWebsite Item Group`
				where item_group in (%s))) """ % (child_groups, child_groups))[0][0]


def get_parent_item_groups(item_group_name):
	base_parents = [
		{"name": frappe._("Home"), "route":"/"},
		{"name": frappe._("All Products"), "route":"/all-products"},
	]
	if not item_group_name:
		return base_parents

	item_group = frappe.get_doc("Catalogue Directory Art", item_group_name)
	parent_groups = frappe.db.sql("""select ifnull(title,name) as name, route from `tabCatalogue Directory Art`
		where lft <= %s and rgt >= %s
		and show_in_website=1
		order by lft asc""", (item_group.lft, item_group.rgt), as_dict=True)

	return base_parents + parent_groups

def invalidate_cache_for(doc, item_group=None):
	if not item_group:
		item_group = doc.name

	for d in get_parent_item_groups(item_group):
		item_group_name = frappe.db.get_value("'Catalogue Directory Art", d.get('name'))
		if item_group_name:
			clear_cache(frappe.db.get_value('Catalogue Directory Art', item_group_name, 'route'))

def get_item_group_defaults(item, company):
	item = frappe.get_cached_doc("Item", item)
	item_group = frappe.get_cached_doc("'Catalogue Directory Art", item.item_group)

	for d in item_group.item_group_defaults or []:
		if d.company == company:
			row = copy.deepcopy(d.as_dict())
			row.pop("name")
			return row

	return frappe._dict()

@frappe.whitelist()
def impact_on_website_item_due_to_catalogue_directory_art(show_in_website,catalogue_name):
	catalogue=frappe.get_doc('Catalogue Directory Art',catalogue_name)
	if int(show_in_website)==1:
		for item in catalogue.get('items_in_universe'):
			website_item_list=frappe.db.get_list('Website Item', filters={'item_code':item.item},fields=['name'])
			if len(website_item_list)>0:
				for website_item in website_item_list:
					frappe.db.set_value('Website Item', website_item.name, 'published', 1)
					frappe.msgprint(_("Website item {0} is set to <b>published</b> for item {0} of universe.")
					.format(get_link_to_form("Website Item",website_item.name),item.item), alert=True)
			else:
				frappe.msgprint(_("There is no website item for item {0} of universe.").format(item.item), alert=True)

	elif int(show_in_website)==0:
		parent_catalogue_directory_art=catalogue.parent_catalogue_directory_art
		for item in catalogue.get('items_in_universe'):
			website_item_list=frappe.db.get_list('Website Item', filters={'item_code':item.item},fields=['name'])
			if len(website_item_list)>0:
				for website_item in website_item_list:
					website_item_doc=frappe.get_doc('Website Item',website_item.name)
					found_catalogue_item=False
					for catalogue_directory_art_website in website_item_doc.get("catalogue_directory_art_website_cf"):
						print('catalogue_directory_art_website',catalogue_directory_art_website)
						print(catalogue_directory_art_website.catalogue,parent_catalogue_directory_art, catalogue_directory_art_website.universe,catalogue_name)
						if catalogue_directory_art_website.catalogue==parent_catalogue_directory_art and catalogue_directory_art_website.universe==catalogue_name:
							found_catalogue_item=True
							[website_item_doc.catalogue_directory_art_website_cf.remove(d) for d in website_item_doc.get('catalogue_directory_art_website_cf') if d.name == catalogue_directory_art_website.name]	
							website_item_doc.save(ignore_permissions=True)							
							frappe.msgprint(_("Website item {0} : from 'Catalogue Directory Art Website' : row {1} with catalogue {2} and universe {3} is removed")
			.format(get_link_to_form("Website Item",website_item.name),catalogue_directory_art_website.idx,catalogue_directory_art_website.catalogue,catalogue_directory_art_website.universe), alert=True)
				if found_catalogue_item==False:
					frappe.msgprint(_("There is no corresponding entry in 'Catalogue Directory Art' website item {0} of universe.").format(item.item), alert=True)

			else:
				frappe.msgprint(_("There is no website item for item {0} of universe.").format(item.item), alert=True)		

@frappe.whitelist()
def get_universe_items_from_catalogue_directory_art(item_name):
	catalogue_directory_art_website_cf=[]
	item_universe_list=frappe.db.get_list('Item Universe Page Art', filters={'item':item_name},fields=['parent'])
	for universe in item_universe_list:
		catalogue_dict = frappe.db.get_value('Catalogue Directory Art', universe.parent, ['show_in_website', 'parent_catalogue_directory_art'], as_dict=1)
		if catalogue_dict.show_in_website==1:
			catalogue_directory_art_website_cf.append({'catalogue':catalogue_dict.parent_catalogue_directory_art,'universe':universe.parent})
	return catalogue_directory_art_website_cf

#  from item --> cat
@frappe.whitelist()
def del_catalogue_item_universe_based_on_item_doc(catalogue,universe,item):
	item_universe_list=frappe.db.get_list('Item Universe Page Art', filters={'item':item},fields=['parent','name'])
	for universe_row in item_universe_list:
		if universe_row.parent==universe:
			parent_catalogue_directory_art = frappe.db.get_value('Catalogue Directory Art', universe_row.parent, 'parent_catalogue_directory_art')	
			if parent_catalogue_directory_art==catalogue:
				catalogue_doc=frappe.get_doc("Catalogue Directory Art",universe_row.parent)
				[catalogue_doc.items_in_universe.remove(d) for d in catalogue_doc.get('items_in_universe') if d.name == universe_row.name]	
				catalogue_doc.save(ignore_permissions=True)
				frappe.msgprint(_("{0} is removed from Catalogue Directory {1} universe.").format(item,universe), alert=True)

#  from cat --> item
@frappe.whitelist()
def del_catalogue_directory_art_item_based_on_catalogue(catalogue,universe,item):
	catalogue_directory_art_item_list=frappe.db.get_list('Catalogue Directory Art Item Detail', filters={'catalogue':catalogue,'universe':universe,'parent':item},fields=['name'])
	for catalogue_directory_art_item in catalogue_directory_art_item_list:
		item_doc=frappe.get_doc("Item",item)
		[item_doc.catalogue_directory_art_item_detail_cf.remove(d) for d in item_doc.get('catalogue_directory_art_item_detail_cf') if d.name == catalogue_directory_art_item.name]	
		item_doc.save(ignore_permissions=True)	
		frappe.msgprint(_("{0} is removed from Item's universe {1} under catalogue {2}.").format(item,universe,catalogue), alert=True)