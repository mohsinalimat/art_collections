// Copyright (c) 2019, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Photo Upload Utility', {

	onload: function(frm) {
		console.log('onload')


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
			frappe.call('art_collections.art_collections.doctype.photo_upload_utility.photo_upload_utility.zip_failed_files', {
			}).then(r => {
				let data=r.message
				if (data) {
					if (data=='failed') {
						frappe.msgprint({
							title: __('ZIP File Status'),
							indicator: 'red',
							message: __('Zip File Download Failure Encountered.')
						})
					}
					else if(data=='empty failed folder'){
						frappe.msgprint({
							title: __('ZIP File Status'),
							indicator: 'red',
							message: __('Failed Folder is Empty, Nothing to Download.')
						})
					}
					else {
						var file_url = '/files/'+data;
						file_url = file_url.replace(/#/g, '%23');
						window.open(file_url);
					}
				}
			})
	},	
	system_error_log: function(frm) {
		frappe.set_route('List', 'Error Log',{method:'File Photo Upload Failure',seen: 'No'})
	},
	refresh: function(frm) {

		
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
				frm.successful_files_count=0
				frm.pending_files_count=0
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
								frm.successful_files_count=0
								frm.pending_files_count=0
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
