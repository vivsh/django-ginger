from django.core.management import call_command


class Compressor(object):

    def __init__(self):
        super(Compressor, self).__init__()
        self.base_dir = ""
        self.rjs_path = ""
        self.input_dir = ""
        self.output_dir = ""
        self.modules = []

    def collect(self):
        call_command("collectstatic", interactive=False)

    def pack(self):
        pass
