from __future__ import unicode_literals
import frappe
from frappe import throw, _
import unidecode



def make_route_ascents_free(self,method):
	if self.route:
		self.route=unidecode.unidecode(self.route)