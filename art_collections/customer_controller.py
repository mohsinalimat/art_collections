from __future__ import unicode_literals
from distutils.log import debug
import frappe
from frappe import _


@frappe.whitelist()
def get_payment_terms_based_on_territory(territory):
	territory=frappe.db.sql("""SELECT territory.name,territory.lft,territory.rgt, territory.is_group ,territory.default_price_list_cf,
territory.default_payment_terms_template_cf,territory.minimum_order_amount_cf,customer_credit_limit.credit_limit,customer_credit_limit.company, customer_credit_limit.bypass_credit_limit_check 
from `tabTerritory` territory left outer join `tabCustomer Credit Limit` customer_credit_limit on customer_credit_limit.parent = territory.credit_limit_cf 
and customer_credit_limit.parenttype='Territory' and customer_credit_limit.idx=1 
where territory.name=%s""",(territory), as_dict=1)
	if len(territory) >0:
		if territory[0].is_group==0:
			territory=frappe.db.sql("""SELECT territory.name,territory.lft,territory.rgt, territory.is_group ,territory.default_price_list_cf,
territory.default_payment_terms_template_cf,territory.minimum_order_amount_cf,customer_credit_limit.credit_limit,customer_credit_limit.company, customer_credit_limit.bypass_credit_limit_check  
from `tabTerritory` territory left outer join `tabCustomer Credit Limit` customer_credit_limit on customer_credit_limit.parent = territory.credit_limit_cf 
and customer_credit_limit.parenttype='Territory' and customer_credit_limit.idx=1
where territory.lft <= %s and territory.rgt >= %s and territory.is_group=1 order by territory.lft desc limit 1""",(territory[0].lft,territory[0].rgt), as_dict=1)	
			if len(territory) >0:
				return territory[0]
			else:
				None		
		else:
			return territory[0]
	else:
		return None
