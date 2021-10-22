# Copyright (c) 2021, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import flt
import erpnext

class CustomerIncentiveEntryArt(Document):

	def on_cancel(self):
		for row in self.customer_goal_achievement_detail:
			if row.credit_journal_entry:
				credit_journal_entry=row.credit_journal_entry
				frappe.db.set_value('Customer Goal Achievement Detail', row.name, 'credit_journal_entry',None)
				doc = frappe.get_doc("Journal Entry", credit_journal_entry)
				if doc.docstatus == 1:
					doc.cancel()
					frappe.msgprint(_("Journal Entry {0} is deleted.").format(credit_journal_entry), alert=True,indicator="red")



	def on_submit(self):
		for row in self.customer_goal_achievement_detail:
			user_remark=_('Customer: {0}, Fiscal Year: {1}, Total Achieved Amount: {3}, Discount %: {2}, Discount Amount: {5}, From Amount:{6}, To Amount:{7}, Incentive Entry Reference:{4}').format(row.customer_name,self.fiscal_year,row.discount_percent,row.achieved_amount,self.name, row.discount_amount,row.from_amount,row.to_amount)
			jv_name=create_journal_entry(amount=row.discount_amount,company=self.company,customer=row.customer,posting_date=self.posting_date,user_remark=user_remark)
			frappe.db.set_value('Customer Goal Achievement Detail', row.name, 'credit_journal_entry', jv_name)
			# for UI
			row.credit_journal_entry=jv_name

	@frappe.whitelist()
	def fetch_customer_incentive(self):
		self.calculate_customer_incentive_for_a_fiscal_year()
		if len(self.customer_goal_achievement_detail)==0:
			frappe.msgprint(_("No matching invoice found for above crieteria"), alert=True,indicator="orange")


	def calculate_customer_incentive_for_a_fiscal_year(self):
			self.customer_goal_achievement_detail=[]
			customers=frappe.db.get_list('Customer Target Art', filters={'fiscal_year': ['=', self.fiscal_year]},fields=['parent','from_value','to_value','discount_percent'],as_list=False)
			start_date, end_date = frappe.db.get_value('Fiscal Year', self.fiscal_year,['year_start_date', 'year_end_date'])
			for customer in customers:
				customer_name=customer.parent
				sales_invoices=frappe.db.get_list('Sales Invoice', 
				filters={
				'customer': ['=', customer_name],
				'docstatus': ['=', 1],
				'company':['=', self.company],
				'posting_date':['between', [start_date,end_date]]
				},fields=['name','base_net_total'],as_list=False)
				total_achieved_amount=0
				achieved_discount_amount=0
				for sales_invoice in sales_invoices:
					total_achieved_amount+=sales_invoice.base_net_total
					

				if total_achieved_amount>=customer.from_value and (total_achieved_amount<=customer.to_value or customer.to_value==0):
					achieved_discount_amount=(total_achieved_amount*customer.discount_percent)/100
					self.append('customer_goal_achievement_detail',{
					'customer':customer_name,
					'customer_name':frappe.db.get_value('Customer', customer_name, 'customer_name'),
					'achieved_amount':total_achieved_amount,
					'discount_amount':achieved_discount_amount,
					'from_amount':customer.from_value,
					'to_amount':customer.to_value,					
					'discount_percent':customer.discount_percent
					})							

def create_journal_entry(amount,company,customer,posting_date,user_remark):
	default_target_incentive_expense_account_art = frappe.db.get_value('Company', company, 'default_target_incentive_expense_account_art')
	default_party_account=None
	default_receivable_account= frappe.db.get_value('Company', company, 'default_receivable_account')
	party_account=frappe.db.get_list('Party Account', filters={'parent': ['=', customer],'company': ['=', company]},fields=['account'],as_list=True)
	if party_account and party_account[0][0]:
		default_party_account=party_account[0][0]
	precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")

	accounts = []

	# credit entry
	accounts.append({
		"account": default_party_account or default_receivable_account,
		"credit_in_account_currency": flt(amount, precision),
		"is_advance":'Yes',
		'party_type':'Customer',
		'party':customer
	})

	# debit entry
	accounts.append({
		"account": default_target_incentive_expense_account_art,
		"debit_in_account_currency": flt(amount, precision),
	})

	journal_entry = frappe.new_doc('Journal Entry')
	journal_entry.voucher_type = 'Credit Note'
	journal_entry.user_remark =user_remark
	journal_entry.company = company
	journal_entry.posting_date = posting_date
	journal_entry.set("accounts", accounts)
	journal_entry.save(ignore_permissions = True)				
	journal_entry.submit()	
	return journal_entry.name		
