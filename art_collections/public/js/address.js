frappe.ui.form.on('Address', {

   validate: function (frm) {
    if (frm.doc.art_county) 
    {
        frm.doc.county=frm.doc.art_county
    }
    if (frm.doc.art_state) 
    {
        frm.doc.state=frm.doc.art_state
    }
   }
});