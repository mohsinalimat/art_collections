from __future__ import unicode_literals
from re import I
import frappe
from frappe import _


def get_directive(self,method):
    directive_list=[]
    if self.doctype=='Quotation':
        if self.quotation_to=='Customer' and self.party_name:
            directive=get_entity_directive(self.doctype,self.quotation_to,self.party_name)
            if directive:
                directive_list.append(directive)
            customer_group=frappe.db.get_value('Customer', self.party_name, 'customer_group')
            directive=get_entity_group_directive(self.doctype,'Customer Group',customer_group)
            if directive:
                directive_list.append(directive)            
            for item in self.items:
                directive=get_item_directive(self.doctype,'Item',item.item_code)
                if directive:
                    directive_list.append(directive)                 
                directive=get_item_group_directive(self.doctype,'Item Group',item.item_group)  
                if directive:
                    directive_list.append(directive)                              
    elif self.doctype=='Sales Order' or self.doctype=='Delivery Note' or self.doctype=='Sales Invoice':
        directive=get_entity_directive(self.doctype,'Customer',self.customer)
        if directive:
            directive_list.append(directive)
        customer_group=frappe.db.get_value('Customer', self.customer, 'customer_group')
        directive=get_entity_group_directive(self.doctype,'Customer Group',customer_group)
        if directive:
            directive_list.append(directive)            
        for item in self.items:
            directive=get_item_directive(self.doctype,'Item',item.item_code)
            if directive:
                directive_list.append(directive)                 
            directive=get_item_group_directive(self.doctype,'Item Group',item.item_group)  
            if directive:
                directive_list.append(directive) 
    elif self.doctype=='Purchase Receipt' or self.doctype=='Purchase Invoice' or self.doctype=='Supplier Quotation':
        directive=get_entity_directive(self.doctype,'Supplier',self.supplier)
        if directive:
            directive_list.append(directive)
        supplier_group=frappe.db.get_value('Supplier', self.supplier, 'supplier_group')
        directive=get_entity_group_directive(self.doctype,'Supplier Group',supplier_group)
        if directive:
            directive_list.append(directive)            
        for item in self.items:
            directive=get_item_directive(self.doctype,'Item',item.item_code)
            if directive:
                directive_list.append(directive)                 
            directive=get_item_group_directive(self.doctype,'Item Group',item.item_group)  
            if directive:
                directive_list.append(directive) 
    elif self.doctype=='Request for Quotation':
        for supplier in self.suppliers:
            directive=get_entity_directive(self.doctype,'Supplier',supplier.supplier)
            if directive:
                directive_list.append(directive)
            supplier_group=frappe.db.get_value('Supplier', supplier.supplier, 'supplier_group')
            directive=get_entity_group_directive(self.doctype,'Supplier Group',supplier_group)
            if directive:
                directive_list.append(directive)            
        for item in self.items:
            directive=get_item_directive(self.doctype,'Item',item.item_code)
            if directive:
                directive_list.append(directive)                 
            directive=get_item_group_directive(self.doctype,'Item Group',item.item_group)  
            if directive:
                directive_list.append(directive) 

    unique_directive_list = []
    unique_directive_name=[]
    for x in directive_list:
        for d in x:
            if d.directive_name not in unique_directive_name:
                unique_directive_list.append(d)  
                unique_directive_name.append(d.directive_name)  
    directive_content=''
    alert_content=''
    for directive in unique_directive_list:
        directive_content+=directive.directive_type
        directive_content+='\n'
        directive_content+=directive.directive
        if unique_directive_list.index(directive) != len(unique_directive_list)-1:
            directive_content+='\n\n'
        if directive.show_as_alert==1:
            alert_content+= '<b>'+directive.directive_type+'</b>'
            alert_content+='<br>'
            alert_content+="<br />".join(directive.directive.split("\n"))  
            if unique_directive_list.index(directive) != len(unique_directive_list)-1:
                alert_content+='<br><br>'                       
    if len(directive_content)>0:
        self.directive_art=directive_content
    if len(alert_content)>0:
        frappe.msgprint(msg= _(alert_content),title= _('Directive Alert'),indicator= 'orange')     


def get_entity_directive(doctype,entity_type,entity_name):
    directive = frappe.db.sql("""
SELECT  directive.directive_name,directive.show_as_alert,directive.directive_type,directive.directive
FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
where doctypes.directive_doctype = %s
and directive.disabled =0
and directive.apply_on = %s
and directive.apply_for_value = %s""", (doctype,entity_type,entity_name),as_dict=True)
    return directive if len(directive)>0 else None

def get_entity_group_directive(doctype,group_type,group_name):
    result_directive=[]
    directives = frappe.db.sql("""
SELECT  directive.directive_name,directive.show_as_alert,directive.directive_type,directive.directive,directive.apply_for_value
FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
where doctypes.directive_doctype ='%s'
and directive.disabled =0
and directive.apply_on = '%s'
""" %(doctype,group_type),as_dict=True)
    if len(directives)>0:
        for directive in directives:
            child_groups_list=get_child_groups(group_type,directive.apply_for_value)
            if group_name in child_groups_list:
                result_directive.append(directive)
    return result_directive if len(result_directive)>0 else None 


def get_item_directive(doctype,entity_type,entity_name):
    directive = frappe.db.sql("""
SELECT  directive.directive_name,directive.show_as_alert,directive.directive_type,directive.directive
FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
where doctypes.directive_doctype = %s
and directive.disabled =0
and directive.apply_for_items = %s
and directive.apply_for_item_value = %s""", (doctype,entity_type,entity_name),as_dict=True)
    return directive if len(directive)>0 else None

def get_item_group_directive(doctype,group_type,group_name):
    result_directive=[]
    directives = frappe.db.sql("""
SELECT  directive.directive_name,directive.show_as_alert,directive.directive_type,directive.directive,directive.apply_for_item_value
FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
where doctypes.directive_doctype ='%s'
and directive.disabled =0
and directive.apply_for_items = '%s'
""" %(doctype,group_type),as_dict=True)
    if len(directives)>0:
        for directive in directives:
            child_groups_list=get_child_groups(group_type,directive.apply_for_item_value)
            if group_name in child_groups_list:
                result_directive.append(directive)
    return result_directive if len(result_directive)>0 else None 

def get_child_groups(group_type, group_name):
	group_details = frappe.get_cached_value(group_type,
		group_name, ["lft", "rgt"], as_dict=1)
	child_groups = [d.name for d in frappe.get_all(group_type,
		filters= {'lft': ('>=', group_details.lft),'rgt': ('<=', group_details.rgt)})]
	return child_groups or {}    