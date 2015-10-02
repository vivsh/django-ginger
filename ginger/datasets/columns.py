import inspect

class DataSet(object):

    def rows(self):
        pass

    def cells(self):
        pass

    def __iter__(self):
        return iter(self.rows())

    def columns(self):
        return

    def column(self, name):
        return

    def row(self, index):
        return

    def cell(self, row, column):
        return

    def __len__(self):
        return


class Aggregate(object):

    def __init__(self, dataset):
        self.dataset = dataset

    def fill(self):
        dataset = self.dataset
        row = dataset.aggregate.empty_row
        methods = {}
        column_names = set()
        for name, method in inspect.getmembers(self, inspect.ismethod):
            head = "fill_"
            tail = name[len(head):]
            if name.startswith(head) and tail in column_names:
                methods[name] = method
        for name, values in dataset.columns():
            value = methods[name](name, values)
            setattr(row, name, value)

    def fill_name(self, values):
        return self.sum("name")

    def sum(self, colname):
        return

    def mean(self, colname):
        return

    def median(self, colname):
        return