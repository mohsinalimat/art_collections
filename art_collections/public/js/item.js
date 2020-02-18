frappe.ui.form.on('Item', {

   is_pre_item_art: function (frm) {
      if (frm.doc.is_pre_item_art==1 && frm.doc.item_name==undefined) {
            frm.set_df_property('item_name', 'reqd', 1)   
      }else{
         frm.set_df_property('item_name', 'reqd', 0)
      }
   },
   before_save: function (frm) {
      if (frm.doc.is_pre_item_art==1) {
         frm.set_value('item_code', 'pre')
      }
   },
    refresh: function (frm) {
     if (frm.doc.__islocal==1) 
     {
        setTimeout(() => {
			frm.set_value('country_of_origin', 'China')
        }, 100);
     }
    }
 });