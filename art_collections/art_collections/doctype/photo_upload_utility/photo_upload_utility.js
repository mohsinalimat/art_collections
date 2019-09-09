// Copyright (c) 2019, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Photo Upload Utility', {

	onload: function(frm) {
		$(frm.fields_dict['output'].wrapper)
		.html(`
		<table style="text-align: center">
		<tr >
			<td> <img style="max-width: 40px;" src="/assets/art_collections/images/files.svg" /> </td>
			<td></td>
			<td> <img style="max-width: 40px;" src="/assets/art_collections/images/right.svg" /> </td>
			<td> <img style="max-width: 40px;" src="/assets/art_collections/images/cross.svg" /> </td>
			<td> <img style="max-width: 40px;" src="/assets/art_collections/images/pending.svg" /> </td>
		</tr>
		<tr>
			<td> `+frm.doc.total_files_count+` </td>
			<td> = </td>
			<td> `+frm.doc.successful_files_count+` </td>
			<td> `+frm.doc.failed_files_count+` </td>
			<td> `+frm.doc.pending_files_count+` </td>
		</tr>
	</table>
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
		
		if (frm.doc.photo_upload_status=="In Process") {
			frm.dashboard.add_progress(__('Photo Upload Status'), "0");
		}


		if (frm.doc.docstatus==0 && !frm.doc.photo_upload_status || frm.doc.photo_upload_status == "Completed"
		|| frm.doc.photo_upload_status == "System Error"
		) {
			frm.add_custom_button(__('Start Photo Processing...'), function() {
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
					}
				});
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
<ul><li>valid Photo file formats gif, jpg, jpeg,tiff,pn,svg</li><li>valid File name convention&nbsp; : a) For main item :&nbsp;&nbsp;itemcode.jpg&nbsp; b)&nbsp;For website slideshow&nbsp; : Itemcode_suffix.extn</li><li>e.g. itemcode = 7878</li><li>valid suffix = fr, ba, sit, det</li><li>fr and ba will be only one per item , while situation (sit) , details (det) could be multiple with number suffix . e.g. 7878_sit01.jpg , 7878_sit02.png</li><li>upon successful upload , the main image images gets attached with the Item along with its thumbnail , while website slideshow is created with the other item images and the website slideshow gets linked with the item , Upon publishing the Item for website , the relevant images , slideshow becomes visible.</li>
<li>"Photo Status Report" shows the list of items and their count for various images available in the files folder.</li>
</ul>
				<tr><td>
					<h4><i class="fa fa-question-sign"></i>
						${__('Process flow for file upload utility')}
					</h4>
					<ol>
					<li>Upload the item images to public/file/temp folder</li><li>Click on "Start Photo Processing .." button</li><li>Wait till the process gets over, reload to check the status</li><li>After processing , it will output the counts for&nbsp;total file, successful,failed &amp; pending.</li><li>The failed files will be&nbsp;zipped together and will be available on&nbsp;click of "Download Failed Files" button.</li><li> System Error checkbox will be checked to show If there was any system related exception/ error while processing with the error log link.</li><li>The process log will be available against each file with its stat</li>
					</ol>
				</td></tr>
			</table>`;
		frm.set_df_property('photo_upload_help', 'options', help_content);


	}
});
