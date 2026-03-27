from django.forms.widgets import ClearableFileInput


class AdminDropzoneFileInput(ClearableFileInput):
    template_name = "admin/widgets/dropzone_file_input.html"


class AdminDropzoneMultipleFileInput(AdminDropzoneFileInput):
    allow_multiple_selected = True
