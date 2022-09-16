frappe.ready(function() {
	frappe.web_form.delete = function() {
		frappe.confirm(
		  "Are you sure you want to delete this document?",
		  function() {
			frappe.call({
			  type: "POST",
			  method: "frappe.website.doctype.web_form.web_form.delete",
			  args: {
				web_form_name: frappe.web_form.name,
				docname: frappe.web_form.doc.name
			  },
			  callback: function(){
			  window.location = frappe.web_form.success_url;
			  }
			});
		  },
		);
	  };
})
