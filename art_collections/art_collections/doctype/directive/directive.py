# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document

class Directive(Document):
	def validate(self):
		self.validate_for_duplicate_doctype()	

	def validate_for_duplicate_doctype(self):
		chk_dupl_itm = []
		for d in self.get('show_directive_on_doctypes_art'):
			if d.directive_doctype in chk_dupl_itm:
				frappe.throw(_("Note: Doctype <b>{0}</b> is entered multiple times").format(d.directive_doctype))
			else:
				chk_dupl_itm.append(d.directive_doctype)			