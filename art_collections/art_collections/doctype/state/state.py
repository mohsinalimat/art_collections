# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class State(Document):
	def autoname(self):
		if self.state and self.country:
			self.name=" - ".join([self.state, self.country])
			self.title = " - ".join([self.state, self.country])

	def validate(self):
		if self.title:
			new_name = " - ".join([self.state, self.country])
			if new_name!=self.title:
				self.title=new_name