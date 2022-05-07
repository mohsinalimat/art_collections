// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Supplier Packing List Art', {
	onload_post_render: function (frm) {
		frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-upload').addClass('hide')
		let upload_art = frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-upload-art')
		if (upload_art.length == 0) {
			let btn = document.createElement('a');
			btn.innerText = 'Upload ART';
			btn.className = 'grid-upload-art btn btn-xs btn-default';
			frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-upload').parent().append(btn);
			btn.addEventListener("click", function () {
				let me = this;
				frappe.flags.no_socketio = true;
				// $(this.wrapper).find(".grid-upload").removeClass('hidden').on("click", () => {
				new frappe.ui.FileUploader({
					as_dataurl: true,
					allow_multiple: false,
					on_success(file) {
						var data = frappe.utils.csv_to_array(frappe.utils.get_decoded_string(file.dataurl));
						let excel_uploaded_data = []
						// row #2 contains fieldnames;
						var fieldnames = data[2];
						$.each(data, (i, row) => {
							if (i > 6) {
								let result = {
									"excel_id": i + 1,
									"action": "",
									"message": ""
								}
								var blank_row = true;
								$.each(row, function (ci, value) {
									if (value) {
										blank_row = false;
										return false;
									}
								});
								if (!blank_row) {
									let my_row = {}
									for (let index = 0; index < fieldnames.length; index++) {
										const element = fieldnames[index];
										my_row[fieldnames[index]] = row[index]
									}
									excel_uploaded_data.push(my_row)
								}
							}
						});
						if (excel_uploaded_data.length > 0) {
							frm.clear_table('spl_unknown_item');
							frm.call({
								method: 'validate_excel_uploaded_data_with_po',
								doc: frm.doc,
								args: {
									excel_data: excel_uploaded_data
								}
							}).then(() => {
								frm.refresh();
							});
						}
					}
				});
				return false;
			});
		}
	},
	refresh: function (frm) {
		//  show download/upload only after save
		if (!frm.doc.__islocal) {
			frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-download').removeClass('hide')
			frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-upload-art').removeClass('hide')
		} else {
			setTimeout(() => {
				frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-download').addClass('hide')
				frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-upload-art').addClass('hide')		
			}, 500);

		}

		if (!frm.doc.__islocal && frm.doc.docstatus == 1) {
			frm.add_custom_button(__('Update PO Item qty'), function () {
				frappe.call({
					method: 'art_collections.art_collections.doctype.supplier_packing_list_art.supplier_packing_list_art.update_po_item_qty_based_on_qty_as_per_spl',
					args: {
						spl_packing_list: frm.doc.name
					},
					callback: function (r) {}
				});
			}).addClass('btn-primary');
		}

		frm.trigger('show_import_log');

		if (frm.doc.docstatus == 0) {
			frm.add_custom_button(__('Purchase Order'),
				function () {
					frm.refresh_field('supplier_packing_list_detail')
					if (!frm.doc.supplier) {
						frappe.throw({
							title: __("Mandatory"),
							message: __("Please Select a Supplier")
						});
					}
					erpnext.utils.map_current_doc({
						method: "art_collections.art_collections.doctype.supplier_packing_list_art.supplier_packing_list_art.make_supplier_packing_list",
						source_doctype: "Purchase Order",
						target: frm,
						setters: {
							supplier: frm.doc.supplier,
							schedule_date: undefined
						},
						get_query_filters: {
							docstatus: 1,
							status: ["not in", ["Closed", "On Hold"]],
							per_received: ["<", 99.99],
							company: frm.doc.company
						}
					})
				}, __("Get Items From"));
		}
	},
	show_import_log(frm) {
		let import_log = JSON.parse(frm.doc.import_log || '[]');
		let logs = import_log;
		frm.toggle_display('import_log', false);
		let rows = logs
			.map(log => {
				let html = '';
				let indicator_color = log.action == 'moved to unknown items' ? 'red' : 'yellow';

				return `<tr>
						<td>${log.excel_id}</td>
						<td ><div class="indicator ${indicator_color}">${log.action}</div></td>
						<td>${log.message}</td>
					</tr>`;
			})
			.join('');

		if (!rows) {
			rows = `<tr><td class="text-center text-muted" colspan=3>
					${__('No failed upload logs')}
				</td></tr>`;
		}

		frm.get_field('import_log_preview').$wrapper.html(`
				<table class="table table-bordered">
					<tr class="text-muted">
						<th width="10%">${__('Excel Row #')}</th>
						<th width="15%">${__('Action')}</th>
						<th width="75%">${__('Message')}</th>
					</tr>
					${rows}
				</table>
			`);
		frm.refresh_field('import_log_preview')
	}
});