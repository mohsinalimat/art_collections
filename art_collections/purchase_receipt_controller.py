import frappe
from frappe import _
from frappe.utils import get_link_to_form

def purchase_receipt_custom_submit_logic(self,method):
	enable_allow_order_still_stock_last_logic(self)
	stock_availability_notification(self)

def enable_allow_order_still_stock_last_logic(self):
	if self.items:
		for item in self.items:
			eligible_item=frappe.get_doc('Item',item.item_code)
			if eligible_item.is_sales_item==0:
				eligible_item.is_sales_item=1
				eligible_item.save(ignore_permissions=True)				
				frappe.msgprint(_("Item {0} is updated with is_sales_item to 1.").format(get_link_to_form('Item',eligible_item.name)), alert=True,indicator="green")

def stock_availability_notification(self):
	from frappe.utils.background_jobs import enqueue
	from frappe.contacts.doctype.contact.contact import get_default_contact

	if self.items:
		for item in self.items:
			wishlists= frappe.db.get_list('Quotation', filters={'order_type': ['=', 'Shopping Cart Wish List'],
			'status': ['=', 'Draft']})
			for wishlist in wishlists:
				doc = frappe.get_doc('Quotation', wishlist.name)
				for  quot_item in doc.items:
					if quot_item.item_code == item.item_code and quot_item.is_stock_available_art == 0:
						url=frappe.utils.get_url() + '/art_cart?wish_list=' +doc.wish_list_name
						item_name=quot_item.item_name
						customer=doc.party_name
						template='Stock Availability Notification'
						email_template = frappe.get_doc("Email Template", template)
						args={
							"url":url,
							"item_name":item_name,
							"customer":doc.customer_name
						}
						message = frappe.render_template(email_template.response, args)
						email_to = frappe.db.get_value('Contact', get_default_contact('customer', customer), 'email_id')
						email_args = {
							"recipients": email_to,
							"sender": None,
							"subject": email_template.subject,
							"message": message,
							"now": True,
							}
						enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)

def unlink_supplier_packing_list_from_purchase_receipt(self,method):
	for item in self.items:
		item.ref_supplier_packing_list_art=None			


def copy_set_apart_from_PO(self,method):
	self.set_apart_po_item_for_customer_cf=[]
	for pr_item in self.items:
		if pr_item.purchase_order and pr_item.purchase_order_item:
			set_apart_po_items=frappe.db.get_list('Set Apart PO Item for Customer', \
			filters={'parent': ['=', pr_item.purchase_order],'item_code': ['=', pr_item.item_code]}, \
			fields=['item_code', 'qty','customer'])
			if len(set_apart_po_items)>0:
					for set_apart_item in set_apart_po_items:
						self.append('set_apart_po_item_for_customer_cf',set_apart_item)							


def get_pr_dashboard_links(data):
    data["internal_links"].update({"Supplier Packing List Art": ["items", "ref_supplier_packing_list_art"]})

    for d in data.get("transactions",[]):
        if d.get("label") == _("Reference"):
            d.update({"items":d.get("items")+["Supplier Packing List Art"]})

    return data						