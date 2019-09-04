# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe import _
import os
import shutil
from frappe.website.render import clear_cache
from frappe.core.doctype.file.file import create_new_folder,get_files_path
from frappe.utils.file_manager import upload
from frappe.utils import encode
from datetime import datetime
from frappe.utils import cstr, get_url, now_datetime,get_bench_path
from frappe.utils import update_progress_bar
from frappe.utils.background_jobs import enqueue



class PhotoUploadUtility(Document):
    def start_file_upload(self):
        frappe.publish_realtime("file_upload_progress",{"progress": "0", "reload": 1}, user=frappe.session.user)

        public_files_path = frappe.get_site_path('public', 'files')
        temp_public_folder = os.path.join(public_files_path, "temp")
        total_files_count=sum([len(filenames) for dirpath, dirnames, filenames in os.walk(temp_public_folder) ])
        if total_files_count==0:
            frappe.publish_realtime("file_upload_progress",{"progress": "100", "reload": 1}, user=frappe.session.user)
            temp_folder_absolute_path=get_bench_path()+temp_public_folder
            temp_folder_absolute_path=temp_folder_absolute_path.replace('.','/sites')
            return 'empty_folder',temp_folder_absolute_path
        else:
        # self.queue_action('upload_action')
            enqueue(upload_files, queue='default', timeout=6000, event='upload_files',photo_upload_utility=self.name)
            return 'queued'


@frappe.whitelist()
def upload_files(photo_upload_utility):
    error_log=[]
    total_files_count=0
    processed_files_count=0
    failed_files_count=0
    system_error=False
    successful_files_count=0
    pending_files_count=0

    #folder paths
    public_files_path = frappe.get_site_path('public', 'files')
    temp_public_folder = os.path.join(public_files_path, "temp")
    failed_public_folder = os.path.join(public_files_path, "failed")

    #create folder if it doesn't exist
    frappe.create_folder(failed_public_folder, with_init=False)
    frappe.create_folder(temp_public_folder, with_init=False)

    # take  backup of last state of failed folder
    zip_failed_files()
    #del all files from failed folder
    failed_files_path = os.path.join(public_files_path, "failed/*")
    cmd_string = """rm -r %s""" % (failed_files_path)
    err, out = frappe.utils.execute_in_shell(cmd_string)

    #del old failed tar files other than last 2
    cmd_string = """find %s -type f -name "failed_*.tar" | sort -nr | tail -n +3 | xargs rm -v""" % (public_files_path)
    err, out = frappe.utils.execute_in_shell(cmd_string)    

    total_files_count=sum([len(filenames) for dirpath, dirnames, filenames in os.walk(temp_public_folder) ])
    pending_files_count=total_files_count
    # if total_files_count==0:
    #     frappe.throw("Temp Folder is empty")
    # get list of item codes
    list_of_item_code = frappe.get_list('Item', filters={'docstatus': 0}, fields=['name'], order_by='name')
    list_of_item_code = [x['name'].lower() for x in list_of_item_code] # convert item_codes in lower case

    # create virtual folder item_pics in file list if not exist
    if not frappe.db.exists("File", {"file_name": 'item_pics'}):
        create_new_folder('item_pics','Home')
    try:
        walk_folder=os.walk(temp_public_folder)
        for dirpath, dirnames, filenames in walk_folder:
            for filename in filenames:
                item_code_in_fname=None
                suffix_in_fname=None
                reason=None

                fname=filename.lower()
                extn = fname.rsplit(".", 1)[1]
                
                # Extract suffix and item_code from file name
                delimit_filename = fname.split("_")
                for index,value in enumerate(delimit_filename):
                    if index==0:
                        item_code_in_fname=value.rsplit(".", 1)[0]
                    elif index==1:
                        suffix_in_fname=value.rsplit(".", 1)[0]
                    else:
                        reason='file_name_is_not_in_correct_format'


                if reason is None:
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
                                file_count_from_db=get_count_of_image_type(item_code_in_fname,suffix_in_fname[0:3])
                                if file_count_from_db!=None:
                                    print(file_count_from_db)
                                    next_count='{0:02d}'.format(int(int(file_count_from_db)+1))
                                    if count==next_count:
                                        suffix_heading=heading(suffix_in_fname[0:3],count)
                                        reason=None
                                    else:
                                        reason='suffix_count_is_incorrect_it_should_be_'+next_count
                                else:
                                    suffix_heading=heading(suffix_in_fname[0:3],count)
                                    reason=None                                   
                        else:
                            reason='incorrect_suffix'
                if reason:
                    # move_file_with_reason(temp_public_folder,failed_public_folder,fname,reason)
                    failed_files_count+=1
                    shutil.move(os.path.join(dirpath, filename),os.path.join(failed_public_folder, filename))
                    os.rename(os.path.join(failed_public_folder, filename), os.path.join(failed_public_folder, (filename+'_'+reason)))
                    frappe.publish_realtime("file_upload_progress", {"progress": str(int(processed_files_count * 100/total_files_count))}, user=frappe.session.user)
                else:
                    # move_file_to_public_folder(temp_public_folder,fname,public_files_path)

                    path = os.path.join(dirpath, fname)
                    print(path)
                    file_size = os.stat(os.path.join(dirpath, filename)).st_size # in bytes


                    if not frappe.db.exists("File", {"file_name": item_code_in_fname}):
                        create_new_folder(item_code_in_fname,'Home/item_pics')

                    if not suffix_in_fname:
                        attached_to_doctype='Item'
                        attached_to_name=item_code_in_fname
                        folder_name='Home/item_pics/'+item_code_in_fname
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

                    fileobj=open(os.path.join(dirpath, filename), 'rb')
                    content=fileobj.read()

                    file_name = frappe.db.get_value('File', fname)
                    if file_name:
                        file_doc = frappe.get_doc('File', file_name)
                    else:
                        file_doc = frappe.new_doc("File")

                    path = os.path.join(dirpath, fname)
                    print(path)
                    file_size = os.stat(os.path.join(dirpath, filename)).st_size # in bytes

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
                        clear_cache()
                    if os.path.exists(os.path.join(dirpath, filename)):
                        os.remove(os.path.join(dirpath, filename))
                    
                    successful_files_count=successful_files_count+1
                    print('for loop processed_files_count',processed_files_count)
                pending_files_count=pending_files_count-1
                processed_files_count =processed_files_count+1
                frappe.publish_realtime("file_upload_progress", {"progress": str(int(processed_files_count * 100/total_files_count))}, user=frappe.session.user)
    except Exception as e:
        print('ex processed_files_count',processed_files_count)
        system_error = True
        err_msg=cstr(e)+"\n"+cstr(fname)+"\n"+frappe.get_traceback()
        error_log = frappe.log_error(err_msg, _("File Photo Upload Failure"))
    finally:
        # frappe.db.set_value(photo_upload_utility, photo_upload_utility, "total_files_count", total_files_count)
        # frappe.db.set_value(photo_upload_utility, photo_upload_utility, "processed_files_count", processed_files_count)
        # frappe.db.set_value(photo_upload_utility, photo_upload_utility, "failed_files_count", failed_files_count)
        # frappe.db.set_value(photo_upload_utility, photo_upload_utility, "system_error", system_error)
        print('fin processed_files_count',processed_files_count)
        doc=frappe.get_doc(photo_upload_utility)
        doc.total_files_count=total_files_count
        doc.processed_files_count=processed_files_count
        doc.failed_files_count=failed_files_count
        doc.system_error=system_error
        doc.pending_files_count=pending_files_count
        doc.successful_files_count=successful_files_count
        if system_error==True:
            doc.photo_upload_status="System Error"
        else:
            doc.photo_upload_status="Completed"
        doc.save()
        doc.notify_update()
        doc.reload()
        frappe.publish_realtime("file_upload_progress",{"progress": "100", "reload": 1}, user=frappe.session.user)


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

@frappe.whitelist()
def zip_failed_files():
    public_files_path = frappe.get_site_path('public', 'files')
    failed_public_folder = os.path.join(public_files_path, "failed")
    cmd_string = """find %s -type d ! -empty""" % (failed_public_folder)
    print(cmd_string)
    err, out = frappe.utils.execute_in_shell(cmd_string)
    # cmd_string
    print(err,out)
    if out!=b'':

        failed_folder_path=frappe.get_site_path("public", "files")

        todays_date = now_datetime().strftime('%Y%m%d_%H%M%S')
        zip_file_name="failed"+"_"+todays_date+".tar"
        zip_file_with_path=os.path.join(frappe.get_site_path("public", "files"),zip_file_name)
        print(zip_file_with_path)

        directory_argument="--directory="+failed_folder_path+" failed"
        print(directory_argument)

        cmd_string = """tar -czf %s %s""" % (zip_file_with_path,directory_argument)

        print(cmd_string)
        err, out = frappe.utils.execute_in_shell(cmd_string)
        # cmd_string
        print(err,out)
        if err==b'':
            print(zip_file_name)
            return zip_file_name
        else:
            print('failed')
            return failed
    else:
        print('no file failed')
        return 'empty failed folder'
    # tar -cvzf ./arty_develop/public/files/g.tar --directory=./arty_develop/public/files failed
    # err, out = frappe.utils.execute_in_shell("pwd")
    # cmd_string
    # print(err,out)

def get_count_of_image_type(item_code,suffix):
    data = frappe.db.sql("""
    SELECT 
    SUBSTR(SUBSTRING_INDEX(SUBSTRING_INDEX(LOWER(file_name), '.', 1),'_',- 1),4,2) AS file_count_from_db
FROM
    `tabFile`
WHERE
    STRCMP(LEFT(SUBSTRING_INDEX(SUBSTRING_INDEX(LOWER(file_name), '.', 1),'_',- 1),3),%s) = 0
    AND attached_to_name = %s
    ORDER BY
    CAST(file_count_from_db AS UNSIGNED)DESC""", (suffix,item_code))
    return data[0][0] if data else None