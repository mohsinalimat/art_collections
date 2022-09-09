# -*- coding: utf-8 -*-
# Copyright (c) 2019, GreyCube Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

from frappe import _
import os,json
import shutil
from frappe.website.render import clear_cache
from frappe.core.doctype.file.file import create_new_folder,get_files_path
from frappe.utils.file_manager import upload
from frappe.utils import encode
from datetime import datetime
from frappe.utils import cstr, get_url, now_datetime,get_bench_path
from frappe.utils import update_progress_bar
from frappe.utils.background_jobs import enqueue
import zipfile
from natsort import natsorted, ns


switcher={}
file_code_seperator='-'
multi_file_suffix=[]
single_file_suffix=[]

class PhotoUploadUtility(Document):
    pass
@frappe.whitelist()    
def start_file_upload(start_time):
    frappe.publish_realtime("file_upload_progress",{"progress": "0", "reload": 1}, user=frappe.session.user)
    public_files_path = frappe.get_site_path('public', 'files')
    temp_public_folder = os.path.join(public_files_path, "temp")
    frappe.create_folder(temp_public_folder, with_init=False)
    cmd_string = """find %s -type d ! -empty""" % (temp_public_folder)
    err, out = frappe.utils.execute_in_shell(cmd_string)
    if out==b'':
    # total_files_count=sum([len(filenames) for dirpath, dirnames, filenames in os.walk(temp_public_folder) ])
    # if total_files_count==0:
        frappe.publish_realtime("file_upload_progress",{"progress": "100", "reload": 1}, user=frappe.session.user)
        temp_folder_absolute_path=get_bench_path()+temp_public_folder
        temp_folder_absolute_path=temp_folder_absolute_path.replace('.','/sites',1)

        doc=frappe.get_doc('Photo Upload Utility')
        doc.last_execution_date_time=start_time
        doc.photo_upload_status='Completed'
        doc.total_files_count=0
        doc.successful_files_count=0
        doc.failed_files_count=0
        doc.zip_file_name='empty_failed_folder'
        doc.pending_files_count=0
        doc.system_error=0
        doc.processed_files_count=0
        doc.file_dict_with_status=''
        doc.save()
        doc.reload()
        return 'empty_folder',temp_folder_absolute_path
    else:
        # upload_photo_files(start_time)
        enqueue(upload_photo_files, queue='long', timeout=600000, event='upload_photo_files',start_time=start_time)
        return 'queued'


@frappe.whitelist()
def upload_photo_files(start_time):
    heading('for_initialization',0)
    # get abbreviation details

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
    failed_zip_folder = os.path.join(public_files_path, "failed_zip_folder")
    
    #create folder if it doesn't exist
    frappe.create_folder(failed_public_folder, with_init=False)
    frappe.create_folder(failed_zip_folder, with_init=False)    

    # take  backup of last state of failed folder
    # zip_failed_files()
    
    #del all files from failed folder
    failed_files_path = os.path.join(public_files_path, "failed/*")
    cmd_string = """rm -r %s""" % (failed_files_path)
    err, out = frappe.utils.execute_in_shell(cmd_string)

   

    # total_files_count=sum([len(filenames) for dirpath, dirnames, filenames in os.walk(temp_public_folder) ])
    sorted_file_name_list=[]
    dirpath=None
    dirnames=None
    for dirpath, dirnames, filenames in os.walk(temp_public_folder):
        sorted_file_name_list.extend(filenames)
        dirpath=dirpath
        dirnames=dirnames

    sorted_file_name_list=natsorted(sorted_file_name_list, alg=ns.PATH)
    total_files_count=len(sorted_file_name_list)
    pending_files_count=total_files_count
    # get list of item codes
    list_of_item_code = frappe.get_list('Item', filters={'docstatus': 0}, fields=['name'], order_by='name')
    list_of_item_code = [x['name'].lower() for x in list_of_item_code] # convert item_codes in lower case

    # create virtual folder item_pics in file list if not exist
    if not frappe.db.exists("File", {"file_name": 'item_pics'}):
        create_new_folder('item_pics','Home')


    # create a file_dict_with_status - this is a log
    file_dict_with_status = {}
    filenames_list_for_log=[]
    filenames_list_for_log=sorted_file_name_list
    for filename in filenames_list_for_log:
        file_dict_with_status[filename] = "pending"    
    
    filenames_list=[]
    filenames_list=sorted_file_name_list
    walk_folder=os.walk(temp_public_folder)
    for filename in filenames_list:
        try:
            item_code_in_fname=None
            suffix_in_fname=None
            reason=None
            fname=filename

            # Extract suffix and item_code from file name
            item_code_in_fname,suffix_in_fname,count_in_fname,extn,reason=extract_meta_from_filename(fname)
            if reason is None:
                if extn not in ['gif','jpg','jpeg','tiff','png','svg'] or extn==None:
                    reason='not_an_image_file'
                elif frappe.db.exists("File", {"file_name": fname}):
                    reason='duplicate_entry'
                elif ((suffix_in_fname not in single_file_suffix) and (suffix_in_fname not in multi_file_suffix)):   
                    reason='not_a_valid_suffix' 
                elif check_duplicate_content(dirpath, filename)!=None:
                    reason=check_duplicate_content(dirpath, filename)
                elif item_code_in_fname not in list_of_item_code:
                    reason='item_code_doesnot_exist'
                elif suffix_in_fname:
                    if (suffix_in_fname in single_file_suffix):
                        reason=None
                        suffix_heading=heading(suffix_in_fname,count_in_fname)
                    elif (suffix_in_fname in multi_file_suffix ):
                        file_count_from_db=get_count_of_image_type(item_code_in_fname,suffix_in_fname)
                        if file_count_from_db!=None:
                            next_count=int(int(file_count_from_db)+1)
                        else:
                            next_count=None
                        if int(count_in_fname)>0: 
                            if count_in_fname==next_count:
                                suffix_heading=heading(suffix_in_fname,count_in_fname)
                                reason=None
                            else:
                                reason='incorrect_suffix_count_it_should_be_'+str(next_count)
                        elif int(count_in_fname)==0 and next_count==None:
                                suffix_heading=heading(suffix_in_fname,count_in_fname)
                                reason=None                                         
                        else:
                            reason='incorrect_suffix_count. count should be '+ str(next_count)
                    else:
                        reason='incorrect_suffix'
            if reason:
                # move_file_with_reason(temp_public_folder,failed_public_folder,fname,reason)
                failed_files_count+=1
                file_dict_with_status[filename]='failed__'+reason
                shutil.move(os.path.join(dirpath, filename),os.path.join(failed_public_folder, filename))
                os.rename(os.path.join(failed_public_folder, filename), os.path.join(failed_public_folder, (filename+'__'+reason)))
                # frappe.publish_realtime("file_upload_progress", {"progress": str(int(processed_files_count * 100/total_files_count))}, user=frappe.session.user)
            else:
                # move_file_to_public_folder(temp_public_folder,fname,public_files_path)

                if not frappe.db.exists("File", {"file_name": item_code_in_fname}):
                    create_new_folder(item_code_in_fname,'Home/item_pics')

                # create slideshow doctype if it doesn't exist
                if not frappe.db.exists("Website Slideshow", item_code_in_fname):
                    slideshow_doc = frappe.get_doc({
                        "doctype": "Website Slideshow",
                        "slideshow_name": item_code_in_fname,
                    })
                    slideshow_doc.insert()
                else:
                    slideshow_doc =frappe.get_doc('Website Slideshow', item_code_in_fname)

                # set slidshow value in website item
                website_item=frappe.db.exists("Website Item", {"item_code": item_code_in_fname})
                if website_item:
                    website_item_slideshow = frappe.db.get_value("Website Item", website_item, 'slideshow')
                    if (not website_item_slideshow) or (website_item_slideshow!=slideshow_doc.name):
                        frappe.db.set_value("Website Item", website_item, 'slideshow', slideshow_doc.name) 

                # if suffix_in_fname=='item_code' and count_in_fname==0:
                #     attached_to_doctype='Item'
                #     attached_to_name=item_code_in_fname
                #     folder_name='Home/item_pics/'+item_code_in_fname
                # else:
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
                if suffix_in_fname=='item_code' and count_in_fname==0:
                    item_doc.image=file_doc.file_url
                    item_doc.save()
                    item_doc.run_method('validate_website_image')
                    item_doc.run_method('make_thumbnail')
                    
                    # attach main image to slide show also
                    row=slideshow_doc.append("slideshow_items",{})
                    row.image=file_doc.file_url 
                    row.heading=suffix_heading
                    slideshow_doc.save()
                    rearrange_last_row_to_top(slideshow_doc.name)
                    item_doc.slideshow=slideshow_doc.name
                    item_doc.save()
                    clear_cache()

                    # attach main image to website item
                    website_item=frappe.db.exists("Website Item", {"item_code": item_code_in_fname})
                    if website_item:       
                        website_item=frappe.get_doc("Website Item",website_item)
                        website_item.website_image = item_doc.image
                        website_item.save()


                else:
                    row=slideshow_doc.append("slideshow_items",{})
                    row.image=file_doc.file_url 
                    row.heading=suffix_heading
                    slideshow_doc.save()
                    rearrange_last_row_to_top(slideshow_doc.name)
                    item_doc.slideshow=slideshow_doc.name
                    item_doc.save()
                    clear_cache()
                if os.path.exists(os.path.join(dirpath, filename)):
                    os.remove(os.path.join(dirpath, filename))
                
                successful_files_count=successful_files_count+1
                file_dict_with_status[filename]='successful'
            pending_files_count=pending_files_count-1
            processed_files_count =processed_files_count+1
            frappe.publish_realtime("file_upload_progress", {"progress": str(int(processed_files_count * 100/total_files_count))}, user=frappe.session.user)
        except frappe.DuplicateEntryError:
            failed_files_count+=1
            reason='image_with_same_content_exist_in_doctype'
            file_dict_with_status[filename]='failed__'+reason
            shutil.move(os.path.join(dirpath, filename),os.path.join(failed_public_folder, filename))
            os.rename(os.path.join(failed_public_folder, filename), os.path.join(failed_public_folder, (filename+'__'+reason)))
            pending_files_count=pending_files_count-1
            processed_files_count =processed_files_count+1
            frappe.publish_realtime("file_upload_progress", {"progress": str(int(processed_files_count * 100/total_files_count))}, user=frappe.session.user)
            continue
        
        except Exception as e:
            system_error = True
            file_dict_with_status[filename]='system_error'+'_'+cstr(e)
            err_msg=cstr(e)+"\n"+cstr(fname)+"\n"+frappe.get_traceback()
            error_log = frappe.log_error(err_msg, _("File Photo Upload Failure"))
        finally:
            doc=frappe.get_doc('Photo Upload Utility')
            doc.total_files_count=total_files_count
            doc.processed_files_count=processed_files_count
            doc.failed_files_count=failed_files_count
            doc.system_error=system_error
            doc.pending_files_count=pending_files_count
            doc.successful_files_count=successful_files_count
            doc.last_execution_date_time=start_time
            doc.file_dict_with_status=json.dumps(file_dict_with_status,indent=0)
            if system_error==True:
                doc.photo_upload_status="System Error"
            else:
                doc.photo_upload_status="Completed"
            if failed_files_count>0:
                doc.zip_file_name=zip_failed_files()
            else:
                doc.zip_file_name='empty_failed_folder'
            doc.save()
            # doc.notify_update()
            frappe.publish_realtime("file_upload_progress",{"progress": "100", "reload": 1}, user=frappe.session.user)
            doc.reload()

def rearrange_last_row_to_top(slide_show_name):
    slide_show=frappe.get_doc('Website Slideshow',slide_show_name)
    slide_show_items=slide_show.get("slideshow_items")
    table_length=len(slide_show_items)
    if table_length>1:
        for row in slide_show_items:
            if row.idx==table_length:
                row.idx=1
            else:
                row.idx=row.idx+1
        slide_show.save()


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

def check_duplicate_content(dirpath, filename):
    from frappe.core.doctype.file.file import get_content_hash

    fileobj=open(os.path.join(dirpath, filename), 'rb')
    content=fileobj.read()
    content_hash = get_content_hash(content)
    duplicate_file = frappe.get_value(
        "File",
        {"content_hash": content_hash},
        ["file_url", "name"],
        as_dict=True,
    )

    if duplicate_file:
        reason='duplicate_content_with_filename_'+duplicate_file.name    
    else:
        reason=None
    return reason

def heading(i,count=None):
    if not bool(switcher):
        header_seperator='_'
        photo_abb_details = frappe.db.sql("SELECT code,heading, multi from `tabArt Photo Type Detail` where parentfield ='art_photo_types' ", as_dict=1)
        if len(photo_abb_details)>0:
            for data in photo_abb_details:
                if data.multi == 1 :
                    switcher[data.code]=data.heading+cstr(header_seperator)
                    multi_file_suffix.append(data.code)
                else:
                    switcher[data.code]=data.heading
                    single_file_suffix.append(data.code)
    if count!=None:
        header=switcher.get(i,"Incorrect header")
        if i in multi_file_suffix:
            header=header+cstr(count)
        return header
    else:
        return switcher.get(i,"Incorrect header")

@frappe.whitelist()
def zip_failed_files():
    public_files_path = frappe.get_site_path('public', 'files')
    failed_public_folder = os.path.join(public_files_path, "failed")
    cmd_string = """find %s -type d ! -empty""" % (failed_public_folder)
    err, out = frappe.utils.execute_in_shell(cmd_string)
    if out!=b'':

        failed_folder_path=frappe.get_site_path("public", "files")

        todays_date = now_datetime().strftime('%Y%m%d_%H%M%S')
        zip_file_name="failed"+"_"+todays_date+".tar"
        failed_zip_folder = os.path.join(public_files_path, "failed_zip_folder")
        zip_file_with_path=os.path.join(failed_zip_folder,zip_file_name)
        

        directory_argument="--directory="+failed_folder_path+" failed"

        cmd_string = """tar -caf %s %s""" % (zip_file_with_path,directory_argument)

        err, out = frappe.utils.execute_in_shell(cmd_string)
        if err==b'':
            return zip_file_name
        else:
            return 'failed'
    else:
        return 'empty_failed_folder'

def get_count_of_image_type(item_code,suffix):
    if suffix=='item_code':
        data = frappe.db.sql("""
    select
        IF (STRCMP(SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(LOWER(file_url), '/files/', -1), '(', -1), ')', 1), SUBSTRING_INDEX(LOWER(file_url), '/files/', -1))= 0,
        '0',
        SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(LOWER(file_url), '/files/', -1), '(', -1), ')', 1)) as file_count_from_db	
    FROM
        `tabFile`
    where
        STRCMP(IF(STRCMP(SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(LOWER(file_url), '/files/', -1), '-', -1),'.',1),' ',1),attached_to_name)=0,'item_code',SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(LOWER(file_url), '/files/', -1), '-', -1),'.',1)), %s)= 0 
        and
        attached_to_name =  %s
    ORDER BY
        CAST(file_count_from_db AS UNSIGNED)DESC""", (suffix,item_code))
        return data[0][0] if data else None        
    else:    
        data = frappe.db.sql("""
    select
        IF (STRCMP(SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(LOWER(file_url), '/files/', -1), '(', -1), ')', 1), SUBSTRING_INDEX(LOWER(file_url), '/files/', -1))= 0,
        '0',
        SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(LOWER(file_url), '/files/', -1), '(', -1), ')', 1)) as file_count_from_db
    FROM
        `tabFile`
    where
        STRCMP(SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(SUBSTRING_INDEX(LOWER(file_url), '/files/', -1), '-', -1), '.', 1), ' ', 1), %s)= 0
        and attached_to_name =  %s
    ORDER BY
        CAST(file_count_from_db AS UNSIGNED)DESC""", (suffix,item_code))
        return data[0][0] if data else None

@frappe.whitelist()
def empty_all_folder():
    public_files_path = frappe.get_site_path('public', 'files')
    temp_public_folder = os.path.join(public_files_path, "temp")
    failed_public_folder = os.path.join(public_files_path, "failed")
    failed_zip_folder = os.path.join(public_files_path, "failed_zip_folder")
    #del old failed tar files other than last 2
    cmd_string = """find %s -type f -name "failed_*.tar" | sort -nr | tail -n +3 | xargs rm """ % (failed_zip_folder)
    err, out = frappe.utils.execute_in_shell(cmd_string)

    #del all files from temp folder
    temp_files_path = os.path.join(public_files_path, "temp/*")
    cmd_string = """rm -r %s""" % (temp_files_path)
    err, out = frappe.utils.execute_in_shell(cmd_string)
    return out

@frappe.whitelist()
def unzip_file(name):
    '''Unzip the given file and make file records for each of the extracted files'''
    file_obj = frappe.get_doc('File', name)
    files = unzip(file_obj)
    return len(files)

def unzip(self):
    '''Unzip current file and replace it by its children'''
    if not ".zip" in self.file_name:
        frappe.msgprint(_("Not a zip file"))
        return

    public_files_path = frappe.get_site_path('public', 'files')
    temp_public_folder = os.path.join(public_files_path, "temp")

    zip_path = frappe.get_site_path(self.file_url.strip('/'))
    base_url = os.path.dirname(self.file_url)

    files = []
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(temp_public_folder)
        for info in zf.infolist():
            files.append(info.filename)
    frappe.delete_doc('File', self.name)
    return files   

def extract_meta_from_filename(fname):
    item_code_in_fname=None
    suffix_in_fname=None
    count_in_fname=None
    reason=None
    extn=None

    if int(fname.find('.'))!=-1:
        fname_wo_ext=fname.rsplit(".", 1)[0]
        extn=fname.rsplit(".", 1)[1]

    if int(fname_wo_ext.find(' '))!=-1:
        fname_before_space=fname_wo_ext.rsplit(" ", 1)[0]
        fname_after_space=fname_wo_ext.rsplit(" ", 1)[1]

        if fname_after_space:
            bracket_start_index=int(fname_after_space.find('('))
            bracket_end_index=int(fname_after_space.find(')'))
            if bracket_start_index!=-1 and  bracket_end_index!=-1:
                count_in_fname=int(fname_after_space[bracket_start_index+1:bracket_end_index])  
            else:
                reason='incorrect_filename_count_format'     
        
            if fname_before_space:
                if int(fname_before_space.find('-'))!=-1:
                    fname_before_dash=fname_before_space.rsplit("-", 1)[0]
                    fname_after_dash=fname_before_space.rsplit("-", 1)[1]
                    suffix_in_fname=fname_after_dash
                    item_code_in_fname=fname_before_dash
                else:
                    suffix_in_fname='item_code'
                    item_code_in_fname=fname_before_space
    elif int(fname_wo_ext.find('-'))!=-1:     
        fname_before_dash=fname_wo_ext.rsplit("-", 1)[0]
        fname_after_dash=fname_wo_ext.rsplit("-", 1)[1]        
        suffix_in_fname=fname_after_dash
        item_code_in_fname=fname_before_dash    
        count_in_fname=int(0)
    else:
       item_code_in_fname=fname_wo_ext
       count_in_fname=int(0)
       suffix_in_fname='item_code'
    return item_code_in_fname,suffix_in_fname,count_in_fname,extn,reason