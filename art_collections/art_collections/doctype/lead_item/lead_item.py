# Copyright (c) 2022, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import cint
from frappe.model.document import Document


class LeadItem(Document):
    def validate(self):
        if cint(self.is_disabled):
            self.status = "Disabled"
        self.is_quoted = cint(self.unit_price)
