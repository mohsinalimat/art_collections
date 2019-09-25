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
			"width": 150
		},
		{
			"fieldname": "slideshow",
			"fieldtype": "Link",
			"options": "Website Slideshow",
			"label": "Slideshow",
			"width": 100
		},
		{
			"fieldname": "item_name",
			"fieldtype": "Data",
			"label": _("Item Name"),
			"width": 150
		},
		{
			"fieldname": "check_allow_insuf",
			"fieldtype": "Data",
			"label": _("Allow Less"),
			"width": 90
		},		
		{
			"fieldname": "main",
			"fieldtype": "Int",
			"label": _("Main"),
			"width": 50
		},
		{
			"fieldname": "back",
			"fieldtype": "Int",
			"label": _("Back"),
			"width": 50
		},
		{
			"fieldname": "front",
			"fieldtype": "Int",
			"label": _("Front"),
			"width": 60
		},
		{
			"fieldname": "detail",
			"fieldtype": "Int",
			"label": _("Detail"),
			"width": 60
		},
		{
			"fieldname": "situation",
			"fieldtype": "Int",
			"label": _("Situation"),
			"width": 80
		},
		{
			"fieldname": "total_photo",
			"fieldtype": "Int",
			"label": _("Total Photo"),
			"width": 90
		}
	]

	return columns

def get_data(filters):
	condition =''
	if filters["based_on"] == "All Items":
		condition = """1=1 """
	elif filters["based_on"] == "All < 5 Photo":
		condition="""( 
					(file.item_count =0 or file.item_count is NULL )or 
					(file.ba_count =0 or file.ba_count is NULL) or
					(file.fr_count =0 or file.fr_count is NULL )or
					(file.sit_count =0 or file.sit_count is NULL) or
					(file.det_count =0 or file.det_count is NULL )
					)"""
	elif filters["based_on"] == "< 5 Photo & not resolved":		
		condition="""( 
					(file.item_count =0 or file.item_count is NULL )or 
					(file.ba_count =0 or file.ba_count is NULL) or
					(file.fr_count =0 or file.fr_count is NULL )or
					(file.sit_count =0 or file.sit_count is NULL) or
					(file.det_count =0 or file.det_count is NULL ))
					and i.allow_insufficient_images_for_web_art=0"""

	data = []
	print(condition)
	query="""
SELECT 
    COALESCE(file.item, i.name) item,
    i.item_name item_name,
    i.allow_insufficient_images_for_web_art as allow_insuff,
	IF(i.allow_insufficient_images_for_web_art=1,
	 concat("<input type='checkbox' id=",i.name," onclick='toggle_allow_insufficient_images(&quot;",i.name,"&quot;);' class='buzz' checked/>") , 
	 concat("<input type='checkbox' id=",i.name," onclick='toggle_allow_insufficient_images(&quot;",i.name,"&quot;);' class='buzz' />")) check_allow_insuf,	
    COALESCE(file.total_count, 0) total_photo,
    COALESCE(file.item_count, 0) main,
    COALESCE(file.ba_count, 0) back,
    COALESCE(file.fr_count, 0) front,
    COALESCE(file.sit_count, 0) situation,
    COALESCE(file.det_count, 0) detail,
	i.slideshow slideshow
FROM
    tabItem i
        LEFT OUTER JOIN
    (SELECT 
        t.item,
            COUNT(*) total_count,
            SUM(t.suff REGEXP 'item') item_count,
            SUM(t.suff REGEXP '^ba') ba_count,
            SUM(t.suff REGEXP '^fr') fr_count,
            SUM(t.suff REGEXP '^sit') sit_count,
            SUM(t.suff REGEXP '^det') det_count
    FROM
        (SELECT 
        attached_to_name item,
        	substring_index(REPLACE(LOWER(file_name), CONCAT(LOWER(attached_to_name), '_'), ''), '.', 1) suff
    FROM
        tabFile
    WHERE
        docstatus = 0 AND is_folder = 0
            AND attached_to_doctype = 'Website Slideshow' 
  UNION ALL SELECT 
        substring_index(file_name, '.', 1) item,  
        'item' suff
    FROM
        tabFile
    WHERE
        docstatus = 0 AND is_folder = 0
            AND attached_to_doctype = 'Item') t
    GROUP BY t.item) file ON LOWER(i.name) = LOWER(file.item)
	WHERE """+condition+""" ORDER BY allow_insuff , total_count"""
	data = frappe.db.sql(query, as_dict=1)
	return data