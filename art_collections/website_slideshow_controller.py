from __future__ import unicode_literals
import frappe
from frappe import throw, _


# def order_slideshow_as_per_photo_type(self, method):
#     headings_list = frappe.db.get_list(
#         "Art Photo Type Detail",
#         filters={"parentfield": "art_photo_types"},
#         fields=["heading"],
#         order_by="idx",
#         pluck="heading",
#     )
#     out = {}
    
#     for heading in headings_list:
#         out[heading] = list(
#             filter(lambda x: str(x.heading).startswith(heading), self.slideshow_items)
#         )
#         out[heading].sort(key=lambda x: x.heading, reverse=True)

#     #  replung left out 
#     remaining=[]
#     new_photo_type_list=[x for d in out.values() for x in d]
#     for row in self.slideshow_items:
#         found=False
#         for new_photo in new_photo_type_list:
#             if row.name==new_photo.name:
#                 found=True
#         if found==False:
#             remaining.append(row)


#     self.slideshow_items =  new_photo_type_list+ remaining

#     #  correct idx
#     for i, d in enumerate(self.slideshow_items):
#         d.idx = i + 1

#     self.slideshow_items.sort(key=lambda x: x.idx)