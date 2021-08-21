from __future__ import unicode_literals
import frappe
from frappe import throw, _

# @frappe.whitelist()
# def get_user_with_picker_role(doctype, txt, searchfield, start, page_length, filters, as_dict):
# 	valid_user_list=[]
# 	picker_role=frappe.db.get_value('Art Collections Settings', 'Art Collections Settings', 'picker_role')
# 	user_lists = frappe.db.get_list('User')
# 	for user in user_lists:
# 		user = frappe.get_doc('User', user.name)
# 		if picker_role:
# 			user_roles=user.get("roles")
# 			for user_role in user_roles:
# 				if user_role.role==picker_role:
# 					valid_user_list.append( (user.name,))
# 		else:
# 			valid_user_list.append( (user.name,))
# 	return valid_user_list


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_user_with_picker_role(doctype, txt, searchfield, start, page_len, filters, as_dict):
	picker_role=frappe.db.get_value('Art Collections Settings', 'Art Collections Settings', 'picker_role')
	valid_user_list= frappe.db.sql("""
	select user.name,user.full_name from  `tabUser` user
inner join `tabHas Role` role
on user.name=role.parent
where role.role = %(picker_role)s
			AND user.`name` like %(txt)s
		ORDER BY
			if(locate(%(_txt)s, user.name), locate(%(_txt)s, user.name), 99999), user.name
		LIMIT
			%(start)s, %(page_len)s""",
		{
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace('%', ''),
			'start': start,
			'page_len': frappe.utils.cint(page_len),
			'picker_role': picker_role
		}, as_dict=as_dict)
	return valid_user_list	