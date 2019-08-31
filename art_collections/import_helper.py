from __future__ import unicode_literals
import frappe
from frappe import _
import os
import shutil
from frappe.website.render import clear_cache
from frappe.core.doctype.file.file import create_new_folder
from frappe.utils.file_manager import upload
from frappe.utils import encode
from datetime import datetime
from frappe.utils import cstr, get_url, now_datetime


@frappe.whitelist()
def upload_files():

    public_files = frappe.get_site_path('public', 'files')
    temp_public_folder=os.path.join(public_files, "temp")
    failed_public_folder=os.path.join(public_files, "failed")

    frappe.create_folder(failed_public_folder, with_init=False)

    list_of_item_code=frappe.get_list('Item', filters={'docstatus': 0}, fields=['name'], order_by='name')
    list_of_item_code= [x['name'].lower() for x in list_of_item_code]

    if not frappe.db.exists("File", {"file_name": 'item_pics'}):
        create_new_folder('item_pics','Home')
        folder_name='Home/item_pics'

    for root, dirs, files in os.walk(temp_public_folder):
        for fname in files:
            fname=fname.lower()
            extn = fname.rsplit(".", 1)[1]
            delimit_filename = fname.split("_")
            suffix_in_fname=None
            item_code_in_fname=None
            reason=None
            for index,value in enumerate(delimit_filename):
                if index==0:
                    item_code_in_fname=value.rsplit(".", 1)[0]
                elif index==1:
                    suffix_in_fname=value.rsplit(".", 1)[0]

            path = os.path.join(root, fname)
            file_size = os.stat(path).st_size # in bytes

            if extn not in ['gif','jpg','jpeg','tiff','png','svg']:
                reason='not_a_image'
            elif frappe.db.exists("File", {"file_name": fname}):
                reason='duplicate_entry'
            elif item_code_in_fname not in list_of_item_code:
                reason='item_code_doesnot_exist'
            elif suffix_in_fname:
                count='01'
                if (suffix_in_fname in ['fr','ba']):
                    reason=None
                    suffix_heading=heading(suffix_in_fname,count)
                elif (suffix_in_fname[0:3] in ['sit','det'] and (len(suffix_in_fname)==5)):
                    if suffix_in_fname[-2].isdigit(): 
                        count=suffix_in_fname[-2:]
                        suffix_heading=heading(suffix_in_fname[0:3],count)
                        reason=None
                else:
                    reason='incorrect_suffix'
            if reason:
                move_file_with_reason(temp_public_folder,failed_public_folder,fname,reason)
            else:
                # move_file_to_public_folder(temp_public_folder,fname,public_files)

                if not frappe.db.exists("File", {"file_name": item_code_in_fname}):
                    create_new_folder(item_code_in_fname,'Home/item_pics')

                if not suffix_in_fname:
                    attached_to_doctype='Item'
                    attached_to_name=item_code_in_fname
                else:
                    if not frappe.db.exists("Website Slideshow", item_code_in_fname):
                        slideshow_doc = frappe.get_doc({
                            "doctype": "Website Slideshow",
                            "slideshow_name": item_code_in_fname,
                        })
                        slideshow_doc.insert()
                    else:
                        slideshow_doc =frappe.get_doc('Website Slideshow', item_code_in_fname)
                    attached_to_doctype='Website Slideshow'
                    attached_to_name=slideshow_doc.name
                    folder_name='Home/item_pics/'+item_code_in_fname

                output_path=os.path.join(temp_public_folder, fname)
                print(output_path,'output_path')
                fileobj=open(output_path, 'rb')
                content=fileobj.read()

                file_name = frappe.db.get_value('File', fname)
                if file_name:
                    file_doc = frappe.get_doc('File', file_name)
                else:
                    file_doc = frappe.new_doc("File")

                file_doc.file_name = fname
                file_doc.file_size = file_size
                file_doc.folder = folder_name
                file_doc.is_private = 0
                file_doc.file_url = '/files/{0}'.format(fname)
                file_doc.content=content
                file_doc.attached_to_doctype = attached_to_doctype
                file_doc.attached_to_name = attached_to_name
                file_doc.save()
                add_comment('File',file_doc.name)


            
                item_doc = frappe.get_doc('Item', item_code_in_fname)
                if not suffix_in_fname:
                    item_doc.image=file_doc.file_url
                    item_doc.save()
                    # item_doc.run_method('validate')
                    item_doc.run_method('validate_website_image')
                    item_doc.run_method('make_thumbnail')
                else:
                    row=slideshow_doc.append("slideshow_items",{})
                    row.image=file_doc.file_url 
                    row.heading=suffix_heading
                    slideshow_doc.save()
                    item_doc.slideshow=slideshow_doc.name
                    item_doc.save()
                    # add_comment('Website Slideshow',slideshow_doc.name)
                    clear_cache()
                path = encode(output_path)
                if os.path.exists(path):
                    os.remove(path)
            
# get_site_path()
def move_file_with_reason(from_path,to_path,file_name,reason):
    print(reason)
    shutil.move(os.path.join(from_path, file_name),os.path.join(to_path, file_name))
    os.rename(os.path.join(to_path, file_name), os.path.join(to_path, (file_name+'_'+reason)))

def move_file_to_public_folder(from_path,file_name,to_path=None):
    if not to_path:
        to_path=frappe.get_site_path('public', 'files')
    print('os.path')
    print(os.path.join(from_path, file_name))
    shutil.move(os.path.join(from_path, file_name),os.path.join(to_path, file_name))

def add_comment(dt,dn):
    comment = {}
    file_doc = frappe.get_doc(dt, dn)
    if dt and dn:
        comment = frappe.get_doc(dt, dn).add_comment("Attachment",
            ("added {0}").format("<a href='{file_url}' target='_blank'>{file_name}</a>{icon}".format(**{
                "icon": ' <i class="fa fa-lock text-warning"></i>' \
                    if file_doc.is_private else "",
                "file_url": file_doc.file_url.replace("#", "%23") \
                    if file_doc.file_name else file_doc.file_url,
                "file_name": file_doc.file_name or file_doc.file_url
            })))

def heading(i,count):
        switcher={
                'fr':'Front',
                'ba':'Back',
                'sit':'Situation_'+count,
                'det':'Detail_'+count
        }
        return switcher.get(i,"Incorrect header")



def zip_failed_files():
    todays_date = now_datetime().strftime('%Y%m%d_%H%M%S')
    failed_folder_path=frappe.get_site_path("public", "files")
    zip_file_name="failed"+"_"+todays_date+".tar"
    
    zip_file_with_path=os.path.join(frappe.get_site_path("public", "files"),zip_file_name)
    print(zip_file_with_path)
    cmd_string = """tar -czf %s %s""" % (zip_file_with_path, "--directory="+failed_folder_path+" failed")
    print(cmd_string)
    err, out = frappe.utils.execute_in_shell(cmd_string)
    print(err,out)