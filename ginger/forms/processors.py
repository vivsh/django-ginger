


class FormProcessor(object):

    __position = 1
    name = None

    def __init__(self):
        FormProcessor.__position += 1
        self.position = FormProcessor.__position

    def process(self, result, form):
        pass
