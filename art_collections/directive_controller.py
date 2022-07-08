from __future__ import unicode_literals
from ast import If
from distutils.log import debug
from re import I
import frappe
from frappe import _
import operator
import itertools

def get_directive(self,method):
    directive_list=[]
    if self.doctype=='Quotation':
        if self.quotation_to=='Customer' and self.party_name:
            customer_group=frappe.db.get_value('Customer', self.party_name, 'customer_group')
            customer_only_directive=get_only_entity_directive(self.doctype,self.quotation_to,self.party_name)
            customer_group_only_directive=get_only_entity_group_directive(self.doctype,'Customer Group',customer_group)
            if customer_only_directive:
                directive_list.append(customer_only_directive)
            if customer_group_only_directive:
                directive_list.append(customer_group_only_directive)
            for item in self.items:
                combined_entity_item_directive=get_combined_entity_item_directive(doctype=self.doctype,entity_type='Customer',entity_name=self.party_name,
                entity_group_type='Customer Group',entity_group_type_name=customer_group,item_name=item.item_code,item_group_name=item.item_group)
                directive_list.append(combined_entity_item_directive)

    elif self.doctype=='Sales Order' or self.doctype=='Delivery Note' or self.doctype=='Sales Invoice' or self.doctype=='Pick List':
        if self.doctype =='Pick List':
            items=self.locations
        else:
            items=self.items
        customer_group=frappe.db.get_value('Customer', self.customer, 'customer_group')
        customer_only_directive=get_only_entity_directive(self.doctype,'Customer',self.customer)
        customer_group_only_directive=get_only_entity_group_directive(self.doctype,'Customer Group',customer_group)
        if customer_only_directive:
            directive_list.append(customer_only_directive)
        if customer_group_only_directive:
            directive_list.append(customer_group_only_directive)
        for item in items:
            combined_entity_item_directive=get_combined_entity_item_directive(doctype=self.doctype,entity_type='Customer',entity_name=self.customer,
            entity_group_type='Customer Group',entity_group_type_name=customer_group,item_name=item.item_code,item_group_name=item.item_group)
            directive_list.append(combined_entity_item_directive)            
     
    elif self.doctype=='Purchase Receipt' or self.doctype=='Purchase Invoice' or self.doctype=='Purchase Order' or self.doctype=='Supplier Quotation':
        supplier_group=frappe.db.get_value('Supplier', self.supplier, 'supplier_group')
        supplier_only_directive=get_only_entity_directive(self.doctype,'Supplier',self.supplier)
        supplier_group_only_directive=get_only_entity_group_directive(self.doctype,'Supplier Group',supplier_group)
        if supplier_only_directive:
            directive_list.append(supplier_only_directive)
        if supplier_group_only_directive:
            directive_list.append(supplier_group_only_directive)
        for item in self.items:
            combined_entity_item_directive=get_combined_entity_item_directive(doctype=self.doctype,entity_type='Supplier',entity_name=self.supplier,
            entity_group_type='Supplier Group',entity_group_type_name=supplier_group,item_name=item.item_code,item_group_name=item.item_group)
            directive_list.append(combined_entity_item_directive)            

    elif self.doctype=='Request for Quotation':
        for supplier in self.suppliers:
            supplier_group=frappe.db.get_value('Supplier', supplier.supplier, 'supplier_group')
            supplier_only_directive=get_only_entity_directive(self.doctype,'Supplier',supplier.supplier)
            supplier_group_only_directive=get_only_entity_group_directive(self.doctype,'Supplier Group',supplier_group)
            if supplier_only_directive:
                directive_list.append(supplier_only_directive)
            if supplier_group_only_directive:
                directive_list.append(supplier_group_only_directive)            
            for item in self.items:
                combined_entity_item_directive=get_combined_entity_item_directive(doctype=self.doctype,entity_type='Supplier',entity_name=supplier.supplier,
                entity_group_type='Supplier Group',entity_group_type_name=supplier_group,item_name=item.item_code,item_group_name=item.item_group)
                directive_list.append(combined_entity_item_directive)                

    unique_directive_list = []
    unique_directive_name=[]
    for x in directive_list:
        for d in x:
            if d.directive_name not in unique_directive_name:
                unique_directive_list.append(d)  
                unique_directive_name.append(d.directive_name)  
    unique_directive_list= sorted(unique_directive_list, key=operator.itemgetter("directive_type"))           
    directive_content=''
    print_directive_content=''
    alert_content=''
    last_directive_type=''
    last_print_directive_type=''
    last_alert_directive_type=''
    for directive in unique_directive_list:
        if directive.show_on_print==0 :
            if last_directive_type!=directive.directive_type:
                directive_content+=directive.directive_type
                directive_content+='\n'
                directive_content+=directive.directive
            else:
                directive_content+=directive.directive  
            if unique_directive_list.index(directive) != len(unique_directive_list)-1:
                directive_content+='\n\n'
            last_directive_type=directive.directive_type     
        elif directive.show_on_print==1:
            if last_print_directive_type!=directive.directive_type:
                print_directive_content+=directive.directive_type
                print_directive_content+='\n'
                print_directive_content+=directive.directive
            else:
                print_directive_content+=directive.directive  
            if unique_directive_list.index(directive) != len(unique_directive_list)-1:
                print_directive_content+='\n\n'
            last_print_directive_type=directive.directive_type
        if directive.show_as_alert==1:

            if last_alert_directive_type!=directive.directive_type:
                alert_content+= '<b>'+directive.directive_type+'</b>'
                alert_content+='<br>'
                alert_content+="<br />".join(directive.directive.split("\n"))  
            else:
                alert_content+="<br />".join(directive.directive.split("\n"))  
            if unique_directive_list.index(directive) != len(unique_directive_list)-1:
                alert_content+='<br><br>'     
        last_alert_directive_type=directive.directive_type             
    
    if len(directive_content)>0:
        self.directive_art=directive_content
    else:
        self.directive_art=None
 
    if len(print_directive_content)>0:
        self.directive_print_art=print_directive_content
    else:
        self.directive_print_art=None        
 
    if len(alert_content)>0:
        frappe.msgprint(msg= _(alert_content),title= _('Directive Alert'),indicator= 'orange')     

# def get_entity_directive(doctype,entity_type,entity_name):
#     directive = frappe.db.sql("""
# SELECT  directive.directive_name,directive.show_as_alert,directive.directive_type,directive.directive
# FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
# where doctypes.directive_doctype = %s
# and directive.disabled =0
# and directive.apply_on = %s
# and directive.apply_for_value = %s""", (doctype,entity_type,entity_name),as_dict=True)
#     return directive if len(directive)>0 else None

# def get_entity_group_directive(doctype,group_type,group_name):
#     result_directive=[]
#     directives = frappe.db.sql("""
# SELECT  directive.directive_name,directive.show_as_alert,directive.directive_type,directive.directive,directive.apply_for_value
# FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
# where doctypes.directive_doctype ='%s'
# and directive.disabled =0
# and directive.apply_on = '%s'
# """ %(doctype,group_type),as_dict=True)
#     if len(directives)>0:
#         for directive in directives:
#             child_groups_list=get_child_groups(group_type,directive.apply_for_value)
#             if group_name in child_groups_list:
#                 result_directive.append(directive)
#     return result_directive if len(result_directive)>0 else None 


# def get_item_directive(doctype,entity_type,entity_name):
#     directive = frappe.db.sql("""
# SELECT  directive.directive_name,directive.show_as_alert,directive.directive_type,directive.directive
# FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
# where doctypes.directive_doctype = %s
# and directive.disabled =0
# and directive.apply_for_items = %s
# and directive.apply_for_item_value = %s""", (doctype,entity_type,entity_name),as_dict=True)
#     import json
#     return directive if len(directive)>0 else None

# def get_item_group_directive(doctype,group_type,group_name):
#     result_directive=[]
#     directives = frappe.db.sql("""
# SELECT  directive.directive_name,directive.show_as_alert,directive.directive_type,directive.directive,directive.apply_for_item_value
# FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
# where doctypes.directive_doctype ='%s'
# and directive.disabled =0
# and directive.apply_for_items = '%s'
# """ %(doctype,group_type),as_dict=True)
#     if len(directives)>0:
#         for directive in directives:
#             child_groups_list=get_child_groups(group_type,directive.apply_for_item_value)
#             if group_name in child_groups_list:
#                 result_directive.append(directive)
#     return result_directive if len(result_directive)>0 else None 

def get_child_groups(group_type, group_name):
	group_details = frappe.get_cached_value(group_type,
		group_name, ["lft", "rgt"], as_dict=1)
	child_groups = [d.name for d in frappe.get_all(group_type,
		filters= {'lft': ('>=', group_details.lft),'rgt': ('<=', group_details.rgt)})]
	return child_groups or {}    

def get_only_entity_directive(doctype,entity_type,entity_name):
    directive = frappe.db.sql("""
SELECT  directive.directive_name,directive.show_as_alert,directive.show_on_print,directive.directive_type,directive.directive
FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
where doctypes.directive_doctype = %s
and directive.disabled =0
and directive.apply_on = %s
and directive.apply_for_value = %s
and (directive.apply_for_items is NULL  or directive.apply_for_items ='')""", (doctype,entity_type,entity_name),as_dict=True)
    return directive if len(directive)>0 else None

def get_only_entity_group_directive(doctype,group_type,group_name):
    result_directive=[]
    directives = frappe.db.sql("""
SELECT  directive.directive_name,directive.show_as_alert,directive.show_on_print,directive.directive_type,directive.directive,directive.apply_for_value
FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
where doctypes.directive_doctype ='%s'
and directive.disabled =0
and directive.apply_on = '%s'
and (directive.apply_for_items is NULL  or directive.apply_for_items ='')
""" %(doctype,group_type),as_dict=True)
    if len(directives)>0:
        for directive in directives:
            child_groups_list=get_child_groups(group_type,directive.apply_for_value)
            if group_name in child_groups_list:
                result_directive.append(directive)
    return result_directive if len(result_directive)>0 else None     


def get_combined_entity_item_directive(doctype,entity_type,entity_name,entity_group_type,entity_group_type_name,item_name,item_group_name):
    result_directive=[]
    item_entity_directives=frappe.db.sql("""
            SELECT  directive.directive_name,directive.show_as_alert,directive.show_on_print,directive.directive_type,directive.directive
            FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
            where doctypes.directive_doctype = '%s'
            and directive.disabled =0
            and directive.apply_on = '%s'
            and directive.apply_for_value = '%s'
            and directive.apply_for_items = 'Item'
            and directive.apply_for_item_value = '%s'
""" %(doctype,entity_type,entity_name,item_name),as_dict=True)

    item_entity_group_directives=frappe.db.sql("""
            SELECT  directive.directive_name,directive.show_as_alert,directive.show_on_print,directive.directive_type,directive.directive
            FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
            where doctypes.directive_doctype = '%s'
            and directive.disabled =0
            and directive.apply_on = '%s'
            and directive.apply_for_value in (select name from `tab%s` cg 
            where cg.lft <=(select lft from `tab%s` where name='%s')
            and cg.rgt >=(select rgt from `tab%s` where name='%s')
            ) 
            and directive.apply_for_items = 'Item'
            and directive.apply_for_item_value = '%s'
""" %(doctype,entity_group_type,entity_group_type,entity_group_type,entity_group_type_name,entity_group_type,entity_group_type_name,item_name),as_dict=True)

    item_group_entity_directive=frappe.db.sql("""
            SELECT  directive.directive_name,directive.show_as_alert,directive.show_on_print,directive.directive_type,directive.directive
            FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
            where doctypes.directive_doctype = '%s'
            and directive.disabled =0
            and directive.apply_on = '%s'
            and directive.apply_for_value = '%s'
            and directive.apply_for_items = 'Item Group'
            and directive.apply_for_item_value in 
            (
            select name from `tabItem Group` ig 
            where ig.lft <=(select lft from `tabItem Group` where name='%s')
            and ig.rgt >=(select rgt from `tabItem Group` where name='%s')
            ) 
""" %(doctype,entity_type,entity_name,item_group_name,item_group_name),as_dict=True)

    item_group_entity_group_directive=frappe.db.sql("""
            SELECT  directive.directive_name,directive.show_as_alert,directive.show_on_print,directive.directive_type,directive.directive
            FROM `tabDirective` directive inner join `tabShow Directive on Doctypes Art` doctypes on directive.name = doctypes.parent 
            where doctypes.directive_doctype = '%s'
            and directive.disabled =0
            and directive.apply_on = '%s'
            and directive.apply_for_items = 'Item Group'
            and directive.apply_for_value in 
            (select name from `tab%s` cg 
            where cg.lft <=(select lft from `tab%s` where name='%s')
            and cg.rgt >=(select rgt from `tab%s` where name='%s')
            )
            and directive.apply_for_item_value in 
            (select name from `tabItem Group` ig 
            where ig.lft <=(select lft from `tabItem Group` where name='%s')
            and ig.rgt >=(select rgt from `tabItem Group` where name='%s')
            ) 
""" %(doctype,entity_group_type,entity_group_type,entity_group_type,entity_group_type_name,entity_group_type,entity_group_type_name,item_group_name,item_group_name),as_dict=True)

    for entity in item_entity_directives:
        if entity not in result_directive:
            result_directive.append(entity)

    for entity in item_entity_group_directives:
        if entity not in result_directive:
            result_directive.append(entity)

    for entity in item_group_entity_directive:
        if entity not in result_directive:
            result_directive.append(entity)

    for entity in item_group_entity_group_directive:
        if entity not in result_directive:
            result_directive.append(entity)   

    return result_directive