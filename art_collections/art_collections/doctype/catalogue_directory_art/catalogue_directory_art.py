# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils.nestedset import NestedSet
from frappe.utils import cstr
from frappe.model.naming import set_name_by_naming_series

class CatalogueDirectoryArt(NestedSet):
	nsm_parent_field ='parent_catalogue_directory_art'

	def autoname(self):
		print(self.node_type,'self.node_type')
		if self.node_type == 'Catalogue Year' :
			self.catalogue_directory_art_name = self.year
		elif self.node_type == 'Universe' :
			self.catalogue_directory_art_name = cstr(self.universe_page_range_start)+'_'+frappe.scrub(self.website_title)
			print(self.catalogue_directory_art_name,'self.catalogue_directory_art_name')
		elif self.node_type == 'Catalogue' :
			self.catalogue_directory_art_name =frappe.scrub(self.website_title)
	def on_update(self):
		# super(CatalogueDirectoryArt, self).on_update()
		self.validate_one_root()

def on_doctype_update():
	frappe.db.add_index("Catalogue Directory Art", ["lft", "rgt"])
