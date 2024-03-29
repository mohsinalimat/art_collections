// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Supplier Packing List Art', {
	onload_post_render: function (frm) {

		// download code
		frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-download').addClass('hide')
		let download_art = frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-download-art')
		if (download_art.length == 0) {
			let btn = document.createElement('a');
			btn.innerText = 'Download ART';
			btn.className = 'grid-download-art btn btn-xs btn-secondary';
			frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-download').parent().append(btn);
			btn.addEventListener("click", function () {
				let title = cur_frm.grids[0].df.label || frappe.model.unscrub(cur_frm.grids[0].df.fieldname);
				var data = [];
				var docfields = [];
				data.push([]);
				$.each(frappe.get_meta(cur_frm.grids[0].df.options).fields, (i, df) => {
					// don't include the read-only field in the template
					if (frappe.model.is_value_type(df.fieldtype)) {
						data[0].push(df.fieldname);
						// let description = (df.description || "") + ' ';
						// if (df.fieldtype === "Date") {
						// 	description += frappe.boot.sysdefaults.date_format;
						// }
						// data[3].push(description);
						docfields.push(df);
					}
				});
	
				// add data
				$.each(cur_frm.grids[0].frm.doc[cur_frm.grids[0].df.fieldname] || [], (i, d) => {
					var row = [];
					$.each(data[0], (i, fieldname) => {
						var value = d[fieldname];
						// format date
						if (docfields[i].fieldtype === "Date" && value) {
							value = frappe.datetime.str_to_user(value);
						}
						row.push(value || "");
					});
					data.push(row);
				});
				function download_items() {
					const worksheet = XLSX.utils.aoa_to_sheet(data);
					const workbook = XLSX.utils.book_new();
					XLSX.utils.book_append_sheet(workbook, worksheet, title);
					XLSX.writeFile(workbook, title+".xlsx");
				}
				download_items()
				return false;				
			})}	


		// upload code
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
				new frappe.ui.FileUploader({
					as_dataurl: true,
					allow_multiple: false,
					on_success(file) {
						var reader = new FileReader();
						reader.onload = function (e) {
						var workbook = XLSX.read(e.target.result);
						var csv = XLSX.utils.sheet_to_csv(workbook.Sheets['Supplier Packing List Detail']);
						var data = frappe.utils.csv_to_array(csv);
						let excel_uploaded_data = []
						// row #0 contains fieldnames;
						var fieldnames = data[0];
						$.each(data, (i, row) => {
							if (i > 0) {
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
					reader.readAsArrayBuffer(file.file_obj)
					}
				});
				return false;
			});
		}

	
	},
	refresh: function (frm) {
		//  show download/upload only after save
		if (!frm.doc.__islocal) {
			// frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-download').removeClass('hide')
			frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-upload-art').removeClass('hide')
			frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-download-art').removeClass('hide')
		} else {
			setTimeout(() => {
				// frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-download').addClass('hide')
				frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-upload-art').addClass('hide')		
				frm.fields_dict.supplier_packing_list_detail.grid.wrapper.find('.grid-download-art').addClass('hide')	
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