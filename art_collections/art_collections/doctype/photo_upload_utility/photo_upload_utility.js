// Copyright (c) 2019, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Photo Upload Utility', {

	onload: function(frm) {
		console.log('onload')
		frappe.realtime.on("file_upload__progress", function(data) {
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
	refresh: function(frm) {
		if(!frm.doc.__islocal && frm.doc.__onload && frm.doc.__onload.dashboard_info &&
			frm.doc.photo_upload_status=="Successful") {
			var info = frm.doc.__onload.dashboard_info;
			frm.dashboard.add_indicator(__('Total Collected: {0}', [format_currency(info.total_paid,
				info.currency)]), 'blue');
			frm.dashboard.add_indicator(__('Total Outstanding: {0}', [format_currency(info.total_unpaid,
				info.currency)]), info.total_unpaid ? 'orange' : 'green');
		}
		if (frm.doc.photo_upload_status=="In Process") {
			frm.dashboard.add_progress("Photo Upload Status", "1");
		}


		if (frm.doc.docstatus==0 && !frm.doc.photo_upload_status || frm.doc.photo_upload_status == "Failed"
		|| frm.doc.photo_upload_status == "In Process"
		) {
			frm.add_custom_button(__('Create Fees'), function() {
				frappe.call({
					method: "create_fees",
					doc: frm.doc,
					callback: function() {
						frm.refresh();
					}
				});
			}, "fa fa-play", "btn-success");
		}
	}
});
