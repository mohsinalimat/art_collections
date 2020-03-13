# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals

import frappe, os
from frappe import _
import tarfile
from frappe import scrub

no_cache = 1

@frappe.whitelist()
def get_zip(name):
    zip_file_with_path,zip_file=get_image_list_for_sales_invoice(name)
    with open(zip_file_with_path, 'rb') as fileobj:
        filedata = fileobj.read()
        frappe.local.response.filename = zip_file
        frappe.local.response.filecontent = filedata
        frappe.local.response.type = "download"

def get_image_list_for_sales_invoice(sales_invoice_name):
        file_list=[]
        file_list_with_path=[]
        doc = frappe.get_doc('Sales Invoice', sales_invoice_name)
        for si_item in doc.get("items") or []:
                main_image=si_item.image
                if main_image!=None:
                        file_list.append(main_image)
                item_code=si_item.item_code
                item_slideshow=frappe.get_value('Item', item_code, 'slideshow')
                if item_slideshow!=None:
                        slideshow=frappe.get_doc('Website Slideshow', item_slideshow)
                        for slideshow_item in slideshow.get('slideshow_items') or []:
                                slideshow_image=slideshow_item.image
                                if slideshow_image!=main_image:
                                        file_list.append(slideshow_image)

        public_files_path = frappe.get_site_path('public', 'files')
        public_folder_path=frappe.get_site_path('public')
        si_zip_folder = os.path.join(public_files_path, "si_zip_folder")
        frappe.create_folder(si_zip_folder, with_init=False)
        #del old failed tar files other than last 2
        cmd_string = """find %s -type f -name "acc*.tar" | sort -nr | tail -n +3 | xargs rm """ % (si_zip_folder)
        err, out = frappe.utils.execute_in_shell(cmd_string)

        zip_file_name=scrub(sales_invoice_name+'.tar')

        zip_file_with_path=os.path.join(si_zip_folder,zip_file_name)
        with tarfile.open(zip_file_with_path, "w:gz") as tar_handle:
                print(file_list,'file_list')
                for file_name in file_list or []:
                        try:
                                is_file_in_file_doctype=len(frappe.db.exists({'doctype': 'File',"file_url": file_name}))
                                if is_file_in_file_doctype==1 :
                                        file_doc = frappe.get_doc('File', {"file_url": file_name})
                                        file_path = file_doc.get_full_path()
                                        file_list_with_path.append(file_path)
                                else:   
                                        print('else',file_name)
                                        remove_slash=file_name.startswith("/")
                                        if remove_slash:
                                                file_name = file_name.replace("/", "", 1)
                                        file_path=os.path.join(public_folder_path, file_name)
                                        print('file_path',file_path)
                                        file_list_with_path.append(file_path)
                                tar_handle.add(file_path,arcname=file_doc.file_name or file_name)
                        except frappe.DoesNotExistError:
                                continue
        tar_handle.close()
        #print(os.stat(zip_file_with_path).st_size)
        #for empty it is 69 
        print(zip_file_with_path,zip_file_name)
        return zip_file_with_path,zip_file_name




# def get_context(context):
#     """Build context for print"""
#     if not ((frappe.form_dict.doctype and frappe.form_dict.name) or frappe.form_dict.doc):
#         return {
#             "body": """<h1>Error</h1>
#                 <p>Parameters doctype and name required</p>
#                 <pre>%s</pre>""" % repr(frappe.form_dict)
#         }
    
#     if frappe.form_dict.name:
        # from art_collections.api import get_image_list_for_sales_invoice
        # zip_file=get_image_list_for_sales_invoice(frappe.form_dict.name)
        # zip_file_with_path,zip_file=get_image_list_for_sales_invoice(frappe.form_dict.name)

        # option 3

        # from frappe.utils import get_url
        # site_url = get_url()+'/files/si_zip_folder/{0}'.format(zip_file)
        # print(site_url)
        
        # return {
        #     "body": '<a href="'+site_url+'">Download!</a>'
        # }

        # option 4 via py
        # return webbrowser.open(site_url,new=0)
        
        # option 1 via py
        # frappe.respond_as_web_page

        # option 2 via py
        # with open(zip_file_with_path, 'rb') as fileobj:
        # 		filedata = fileobj.read()

        # frappe.local.response.filename = zip_file
        # frappe.local.response.filecontent = filedata
        # frappe.local.response.type = "download"
        # print(frappe.local.response.filename )
        # print(frappe.local.response.filecontent)

        # option 5 via JS
        # 		html += trigger_print_script

        # 	return html		
