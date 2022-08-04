// Copyright (c) 2022, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Photo Quotation', {
	refresh: function (frm) {
		make_items_grid(frm);

		frm.add_custom_button(__("Bulk Photo Import"), function () {
			new frappe.ui.FileUploader({
				method: "art_collections.art_collections.doctype.photo_quotation.photo_quotation.upload_lead_items",
				doctype: frm.doctype,
				docname: frm.docname,
				frm: frm,
				folder: 'Home/Attachments',
				on_success: (file_doc) => {
					// console.log(file_doc);
				}
			})
		});

		// frm.add_custom_button(__("Refresh Items"), function () {
		// 	make_items_grid(frm);
		// });
	},
	before_save: function (frm) {
		let data = window.items_table.getData();
		console.log(data);

		return frm.call({
			method: 'update_lead_items',
			doc: frm.doc,
			args: {
				items: data
			}
		});
	},

	upload_items: function (frm) {
		new frappe.ui.FileUploader({
			as_dataurl: true,
			allow_multiple: false,
			on_success(file) {
				var reader = new FileReader();
				reader.onload = function (e) {
					var workbook = XLSX.read(e.target.result);
					var csv = XLSX.utils.sheet_to_csv(workbook.Sheets['Lead Items']);
					var data = frappe.utils.csv_to_array(csv);
					window.items_table.setData(data.slice(1));
					frm.dirty();
				}
				reader.readAsArrayBuffer(file.file_obj)
			}
		})
	}
	,

	download_items: function () {
		let data = [window.items_table.getHeaders().split(",")].concat(window.items_table.getData());
		const worksheet = XLSX.utils.aoa_to_sheet(data);
		const workbook = XLSX.utils.book_new();
		XLSX.utils.book_append_sheet(workbook, worksheet, 'Lead Items');
		XLSX.writeFile(workbook, cur_frm.doc.name + "-Lead Items.xlsx");
	}
});



function make_items_grid(frm) {
	if (window.items_table)
		jspreadsheet.destroy(document.getElementById('items-table'), false);
	// 
	const tmpl = `<div id="items-table"></div>`;
	let items_html = frm.fields_dict["items_html"];
	items_html.$wrapper.html(tmpl)
	let width = items_html.$wrapper.closest('div.section-body').width()

	frm.call({
		method: 'get_lead_items',
		doc: frm.doc,
		args: {}
	}).then((r) => {

		let columns = r.message.columns.map(t => {
			return {
				title: t.label,
				type: t.fieldtype
			}
		})

		let items_table = jspreadsheet(document.getElementById('items-table'), {
			filters: true,
			columns: columns,
			// minDimensions: [30, 10],
			defaultColWidth: 100,
			tableOverflow: true,
			tableWidth: `${width - 30}px`,
			tableHeight: "500px",
			search: true,
			// pagination: 10,

			updateTable: function (instance, cell, col, row, val, id) {
				if (col == 1 && val) {
					cell.innerHTML = '<img src="' + val + '" style="width:40px;height:40px">';
				}
			},

			onafterchanges: function (instance) {
				console.log(instance);
				frm.dirty();
			}
		});

		items_table.setData(r.message.data)

		$(`
		<div>
			<button onclick="cur_frm.events.download_items()">Supplier Items</button>
			<button onclick="cur_frm.events.download_items()">Artyfetes Items</button>
			<button onclick="cur_frm.events.download_items()">Create Items</button>
			<button onclick="cur_frm.events.download_items()">Sample Request</button>
			<button onclick="cur_frm.events.upload_items(cur_frm)">Upload</button>
			<button onclick="cur_frm.events.download_items()">Download</button>
		</div>
		`).appendTo('.jexcel_filter')
		$('.jexcel_filter').css('justify-content', 'right')

		window.items_table = items_table;

	});

}
