// Copyright (c) 2019, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Photo Upload Utility', {

	onload: function(frm) {
		$(frm.fields_dict['output'].wrapper)
		.html(`
		<div style="width:100%; text-align:center;">
<table style="text-align: center; display:inline-block;">
	<tr >
		<td style="width:100px; padding:8px 0;"> <img style="max-width: 50px;" src="/assets/art_collections/images/files.svg" alt="Total File Count" title="Total File Count" /> </td>
		<td></td>
		<td style="width:100px; "> <img style="max-width: 50px;" src="/assets/art_collections/images/right.svg" data-toggle="tooltip"  alt="Successful File Count" title="Successful File Count" /> </td>
		<td style="width:100px;"> <img style="max-width: 50px;" src="/assets/art_collections/images/cross.svg" data-toggle="tooltip"  alt="Failed File Count" title="Failed File Count" /> </td>
		<td style="width:100px;"> <img style="max-width: 50px;" src="/assets/art_collections/images/pending.svg" data-toggle="tooltip"  alt="Pending File Count" title="Pending File Count" /> </td>
	</tr>

	<tr>
		<td> `+frm.doc.total_files_count+` </td>
		<td> = </td>
		<td> `+frm.doc.successful_files_count+` </td>
		<td> `+frm.doc.failed_files_count+` </td>
		<td> `+frm.doc.pending_files_count+` </td>
	</tr>
</table>
</div>
`)

		frappe.realtime.on("file_upload_progress", function(data) {
			if (data.reload && data.reload === 1) {
				frm.reload_doc();
			}
			if (data.progress) {
				let progress_bar = $(cur_frm.dashboard.progress_area).find(".progress-bar");
				if (progress_bar) {
					$(progress_bar).removeClass("progress-bar-danger").addClass("progress-bar-success progress-bar-striped");
					$(progress_bar).css("width", data.progress+"%");
				}
			}
		});
	},
	download_failed_files: function(frm) {
				let data=frm.doc.zip_file_name
				if (data) {
					if (data=='failed') {
						frappe.msgprint({
							title: __('ZIP File Status'),
							indicator: 'red',
							message: __('Zip File Download Failure Encountered.')
						})
					}
					else if(data=='empty_failed_folder'){
						frappe.msgprint({
							title: __('ZIP File Status'),
							indicator: 'red',
							message: __('Failed Folder is Empty, Nothing to Download.')
						})
					}
					else {
						var file_url = '/files/failed_zip_folder/'+data;
						file_url = file_url.replace(/#/g, '%23');
						window.open(file_url);
					}
				}else{
					frappe.msgprint({
						title: __('ZIP File Status'),
						indicator: 'red',
						message: __('Failed Folder is Empty, Nothing to Download.')
					})
				}
	},	
	system_error_log: function(frm) {
		frappe.set_route('List', 'Error Log',{method:['Like','%photo%'],seen: 'No'})
	},
	refresh: function(frm) {
		frm.page.add_menu_item(__("Sanitize Folder"), function() {
			frappe.call('art_collections.art_collections.doctype.photo_upload_utility.photo_upload_utility.empty_all_folder', {
			}).then(r => 
				{	
					if (r.message=='') {
						frappe.msgprint({
							title: __('Folder Status'),
							indicator: 'green',
							message: __(`[a] Temp Folder is Emptied.`+`<br>`+
										`[b] failed_zip_folder has now latest 2 files only`)
						})					
					}

				})
		});
		frm.page.add_menu_item(__("Upload Zip"), function() {
			new frappe.ui.FileUploader({
				folder: this.current_folder,
				restrictions: {
					allowed_file_types: ['.zip']
				},
				on_success: file => {
					frappe.show_alert(__('Unzipping files...'));
					frappe.call('art_collections.art_collections.doctype.photo_upload_utility.photo_upload_utility.unzip_file', { name: file.name })
						.then((r) => {
							if (r.message) {
								frappe.show_alert(__('Unzipped {0} files', [r.message]));
								start_processing(frm)
							}
						});
						
				}
			});			

		});

		if (frm.doc.photo_upload_status=="In Process") {
			frm.dashboard.add_progress(__('Photo Upload Status'), "0");
		}


		if (frm.doc.docstatus==0 && !frm.doc.photo_upload_status || frm.doc.photo_upload_status == "Completed"
		|| frm.doc.photo_upload_status == "System Error"
		) {
			frm.add_custom_button(__('Start Photo Processing...'), function() {
				start_processing(frm)
			}, "fa fa-play", "btn-success");
		}



		frm.add_custom_button(__('Photo Status Report'), function() {
			
			frappe.set_route('query-report', 'Item Photo Status', {based_on: '< 5 Photo & not resolved'});
		}, "fa fa-play", "btn-success");

		var help_content =
			`<table class="table table-bordered" style="background-color: #f9f9f9;">
				<tr><td>
					<h4>
						<i class="fa fa-hand-right"></i>
						${__('Notes')}
					</h4>
					<ul>
					<li>Valid photo file formats(i.e. file extensions) gif, jpg, jpeg, tiff, png, svg</li>
					<li>Valid file name convention&nbsp; 
						:a) For main item :&nbsp;&nbsp;itemcode.jpg&nbsp; 
						b)&nbsp;For website
						slideshow&nbsp; : Itemcode-{suffix} ({count}).extn</li>
					<li>e.g. 34345.jpeg, 34345 (1).jpeg, 34345 (2).jpeg <br>
					34345-a.jpeg, 34345-a (1).jpeg, 34345-a (2).jpeg<br>
					34345-ba.jpeg<br>
					34345-fr.jpeg</li>
					<li>Valid suffix = {item_code}, fr, ba, a. It needs to be set in 'Art Collections Settings' under 'Photo Upload Utility' section</li>
					<li>fr and ba will be only one per item , while Ambiance (a) , Détouré ({item_code}) could be multiple with number suffix
						. e.g. 34345.jpeg, 34345 (1).jpeg, 34345-a.jpeg, 34345-a (1).jpeg</li>
					<li>Count in filename has to be serial. i.e. if system has 34345-a (1).jpeg next file name has to be 34345-a (2).jpeg. If 34345-a (4).jpeg is given it would give error</li>
					<li>Count in filename with suffix that are allowed multiple times should start with None. i.e. first file for 'a' has to be  34345-a.jpeg and not  34345-a (1).jpeg</li>
					<li>Upon successful upload , the main image gets attached with the Item and website slideslow , while
						website slideshow (with name as item_code) is created with the other item images <br>
						Upon action --> "Publish in Website" , website item gets created. 
						Select slidshow (34345) and save it. The relevant images , slideshow becomes visible on web.</li>
					<li>if you keep on uploading same file content by renaming it , it would give duplicate content error, with stating the file that has the same content. <br>
					ex. 77771.jpeg": "failed__duplicate_content_with_filename_e142275285"</li>
					<li>Each doctype has limit regarding max no of attachments it can have.It can be checked at Customize Form->Max Attachments.<br>
					ex. Items : max 50, Website Slideshow : max 10.</li>	
					<li>"Photo Status Report" shows the list of items and their count for various images available in the files folder.
					</li>
				</ul>
				<tr><td>
					<h4><i class="fa fa-question-sign"></i>
						${__('Process flow for Photo upload utility')}
					</h4>
					<h5>
					${__('There are 2 options to upload image files, depending upon the option execute the first 2 steps, rest of the steps are common.')}
					</h5>
					<ol>
					<p><b>Option 1 :</b> From "Photo Upload Utility" --> it is preferred if images are 25-50.</p>
					<li>Click on Menu > "Sanitize Folder" to clear all previous processed files</li>
					<li>Click on Menu > Upload Zip to upload the zip containing all the images.</li>
					</ol>
					<ol>
					<p><b>Option 2 :</b> From FTP (Filezilla) --> it is preferred for any number of images. default option</p>
					<li>Upload the item images to public/file/temp folder</li>
					<li>Click on "Start Photo Processing .." button</li>
					<br>
					<li>Wait till the process gets over, reload to check the status</li><li>After processing , it will output the counts for&nbsp;total file, successful,failed &amp; pending.</li><li>The failed files will be&nbsp;zipped together and will be available on&nbsp;click of "Download Failed Files" button.</li><li> System Error checkbox will be checked to show If there was any system related exception/ error while processing with the error log link.</li><li>The process log will be available against each file with its stat</li>
					</ol>
				</td></tr>
			</table>`;
		frm.set_df_property('photo_upload_help', 'options', help_content);


	}
});

var start_processing=function(frm) {
	frm.doc.photo_upload_status='In Process'
	frm.doc.total_files_count=0
	frm.doc.processed_files_count=0
	frm.doc.failed_files_count=0
	frm.doc.system_error=0
	frm.doc.successful_files_count=0
	frm.doc.pending_files_count=0
	frm.doc.file_dict_with_status=''
	frm.doc.zip_file_name='empty_failed_folder'
	$(frm.fields_dict['output'].wrapper).html(``)
	frm.doc.last_execution_date_time=frappe.datetime.now_datetime()
	frm.refresh_fields()
	frappe.call({
		method: "art_collections.art_collections.doctype.photo_upload_utility.photo_upload_utility.start_file_upload",
		args: {start_time:frm.doc.last_execution_date_time},
		callback: function(r) {
			if (r) {
				console.log(r)
				let message=r.message
				if (message[0]=='empty_folder') {
					frappe.msgprint('Empty Folder ---> '+message[1]+'<br><br> Please upload file in temp folder','Error')
				} else if(message=='queued'){
					frappe.show_alert({message:__('Your Process is queued'), indicator:'green'},2);
				}
				else {
					console.log(r)
				}
				
			}
			console.log(r)
			frm.refresh();
			frm.reload_doc()
		}
	});	
}