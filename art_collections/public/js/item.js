frappe.ui.form.on('Item', {
    refresh: function (frm) {
     if (frm.doc.__islocal==1) 
     {
        setTimeout(() => {
			frm.set_value('country_of_origin', 'China')
        }, 100);
     }
    }
 });