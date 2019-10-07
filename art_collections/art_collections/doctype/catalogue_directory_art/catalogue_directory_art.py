# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils.nestedset import NestedSet
from frappe.model.naming import set_name_by_naming_series

class CatalogueDirectoryArt(NestedSet):
	nsm_parent_field ='parent_catalogue_directory_art'

	def on_update(self):
		super(CatalogueDirectoryArt, self).on_update()
		self.validate_one_root()

def on_doctype_update():
	frappe.db.add_index("Catalogue Directory Art", ["lft", "rgt"])
