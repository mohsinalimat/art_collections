# Copyright (c) 2013, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
# from frappe.utils import getdate, add_days, today, cint
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	columns = []
	columns = [
		{
			"fieldname": "item",
			"fieldtype": "Link",
			"options": "Item",
			"label": "Item",
			"width": 100
		},
		{
			"fieldname": "item_name",
			"fieldtype": "Data",
			"label": _("Item Name"),
			"width": 240
		},	
		{
			"fieldname": "website_item",
			"fieldtype": "Link",
			"options": "Website Item",
			"label": _("Website Item"),
			"width": 120
		},			
		{
			"fieldname": "published",
			"fieldtype": "Check",
			"label": _("Published"),
			"width": 100
		},		
		{
			"fieldname": "slideshow",
			"fieldtype": "Link",
			"options": "Website Slideshow",
			"label": "Slideshow",
			"width": 120
		},
		{
			"fieldname": "website_slideshow_link",
			"fieldtype": "Data",
			"label": _("Website Slide"),
			"width": 120
		},
		{
			"fieldname": "check_allow_insuf",
			"fieldtype": "Data",
			"label": _("Allow Less"),
			"width": 110
		},		
		{
			"fieldname": "detoure",
			"fieldtype": "Int",
			"label": _("Détouré"),
			"width": 90
		},
		{
			"fieldname": "ambiance",
			"fieldtype": "Int",
			"label": _("Ambiance"),
			"width": 90
		},		
		{
			"fieldname": "front",
			"fieldtype": "Int",
			"label": _("Front Packaged"),
			"width": 90
		},		
		{
			"fieldname": "back",
			"fieldtype": "Int",
			"label": _("Back Packaged"),
			"width": 90
		},
		{
			"fieldname": "total_photo",
			"fieldtype": "Int",
			"label": _("Total Photo"),
			"width": 110
		}
	]

	return columns

def get_data(filters):
	condition = """1=1 """


	data = []
	print(condition)
	query="""select
	item.name as item,
	item.item_name as item_name,
	website_item.name as website_item,
	website_item.published as published,
	slideshow.name as slideshow,
	website_item.slideshow as website_slideshow_link, 
	website_item.allow_insufficient_images_for_web_art,
	IF(website_item.allow_insufficient_images_for_web_art = 1,
	 concat("<input type='checkbox' id=", website_item.name, " onclick='toggle_allow_insufficient_images(&quot;", website_item.name, "&quot;);' class='buzz' checked/>") , 
	 concat("<input type='checkbox' id=", website_item.name, " onclick='toggle_allow_insufficient_images(&quot;", website_item.name, "&quot;);' class='buzz' />")) check_allow_insuf,
	COALESCE(slideshow_items.detoure_count, 0) detoure,
	COALESCE(slideshow_items.ambiance_count, 0) ambiance,
	COALESCE(slideshow_items.fr_count, 0) front,
	COALESCE(slideshow_items.ba_count, 0) back,
	COALESCE(slideshow_items.total_count, 0) total_photo
from
	`tabItem` item
left outer join `tabWebsite Item` website_item on
	website_item.item_code = item.name
left outer join `tabWebsite Slideshow` as slideshow on
	item.name = slideshow.name
left outer join 
 (
	SELECT
		COUNT(*) total_count,
		slideshow_item.parent,
		SUM(slideshow_item.heading REGEXP '^Détouré') detoure_count,
		SUM(slideshow_item.heading REGEXP '^Ambiance') ambiance_count,
		SUM(slideshow_item.heading REGEXP '^Packaged Front') fr_count,
		SUM(slideshow_item.heading REGEXP '^Packaged back') ba_count
	FROM
		`tabWebsite Slideshow Item` as slideshow_item
	group by
		parent
	ORDER by
		heading DESC ) as slideshow_items
 on
	slideshow_items.parent = slideshow.name
where
	item.disabled = 0
order by
	item.name DESC
"""
	data = frappe.db.sql(query, as_dict=1)
	return data