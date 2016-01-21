
import abc


class _ColumnSet(object):
    pass

class _RowSet(object):
    pass

class DataTable(object):

    @property
    def rows(self):
        return

    @property
    def columns(self):
        return

    @property
    def cells(self):
        return

class ModelDataTable(DataTable):
    pass