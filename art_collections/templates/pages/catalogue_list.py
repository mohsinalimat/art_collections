from __future__ import unicode_literals
import frappe
import frappe.website.render
from art_collections.api import get_value
from frappe.utils import cstr

page_title = "Catalogue"

def get_context(context):
	#  get_all_nodes("Catalogue","Summer 2019","frappe.desk.treeview.get_children")
	# get_children("Catalogue",parent="Summer 2019")
	parent = cstr(frappe.form_dict.parent or "All Catalogue")
	print(get_value())
	context.universe=get_value(parent)
	return context


# def get_value():
# 	catalogue =get_children("Catalogue",parent="Summer 2019")
# 	universe=[]
# 	for x in catalogue:
# 		print('xx',x.get('title'))
# 		title=x.get('title')
# 		universe.append(title)
# 	return universe	