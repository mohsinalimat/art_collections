// Copyright (c) 2019, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Photo Upload Utility', {

	onload: function(frm) {
		console.log('onload')
		$(frm.fields_dict['output'].wrapper)
		.html(`<ul>
		<li><span >Total File Count #`+frm.doc.total_files_count+`</span>
		  <ul class="nested">
			<li><span >Processed File</span>
			  <ul class="nested">
			  <li>Successful File Count #`+frm.doc.successful_files_count+`</li>
			  <li>Failed File Count #`+frm.doc.failed_files_count+`</li>
			  </ul>
			</li>
			<li>Pending File Count #`+frm.doc.pending_files_count+`</li>
		  </ul>
		</li>
	  </ul>`)

		frappe.realtime.on("file_upload_progress", function(data) {
			console.log(data,'data')
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
			// frappe.call('art_collections.art_collections.doctype.photo_upload_utility.photo_upload_utility.zip_failed_files', {
			// }).then(r => 
			// 	{
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
			// }
			// )
	},	
	system_error_log: function(frm) {
		frappe.set_route('List', 'Error Log',{method:['Like','%photo%'],seen: 'No'})
	},
	refresh: function(frm) {
		frm.page.add_menu_item(__("Sanitize Folder"), function() {
			frappe.call('art_collections.art_collections.doctype.photo_upload_utility.photo_upload_utility.empty_all_folder', {
			}).then(r => 
				{	console.log(r)
					if (r.message=='') {
						frappe.msgprint({
							title: __('Folder Status'),
							indicator: 'green',
							message: __(`Temp Folder is Emptied.`+`\\n`+
										`failed_zip_folder has latest 2 files only`)
						})					
					}

				})
		});
		
		if(!frm.doc.__islocal && frm.doc.__onload &&
			frm.doc.photo_upload_status=="Completed") {

		}
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
				frm.refresh_fields()
				// frm.refresh_field('photo_upload_status')
				frappe.call({
					method: "start_file_upload",
					doc: frm.doc,
					callback: function(r) {
						if (r) {
							console.log(r)
							let message=r.message
							if (message[0]=='empty_folder') {
								frm.doc.photo_upload_status='Completed'
								frm.doc.total_files_count=0
								frm.doc.processed_files_count=0
								frm.doc.failed_files_count=0
								frm.doc.system_error=0
								frm.doc.successful_files_count=0
								frm.doc.pending_files_count=0
								frm.doc.file_dict_with_status=''
								frm.doc.zip_file_name='empty_failed_folder'
								$(frm.fields_dict['output'].wrapper).html(``)
								frm.refresh_fields()								
								frappe.msgprint(message[1]+' folder is empty','Error')
							} else if(message=='queued'){
								frappe.msgprint('Your Process is queued','Information')
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

	}
});
