
from django.apps import AppConfig
from ginger.template import prep


class GingerConfig(AppConfig):

    name = "ginger"
    verbose_name = "ginger"
    __once = False

    def ready(self):
        if not self.__once:
            self.__once = True
        prep.setup()