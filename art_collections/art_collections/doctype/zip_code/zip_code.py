# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ZipCode(Document):
	def autoname(self):
		self.name = " - ".join([self.zip_code, self.city])
