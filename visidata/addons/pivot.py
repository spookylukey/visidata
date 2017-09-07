from visidata import *

globalCommand('W', 'vd.push(SheetPivot(sheet, [cursorCol]))', 'push a sheet pivoted on the current column')

# rowdef: (tuple(keyvalues), dict(variable_value -> list(rows)))
class SheetPivot(Sheet):
    'Summarize key columns in pivot table and display as new sheet.'
    commands = [
        Command(ENTER, 'vs = vd.push(copy(source)); vs.name += "_%s"%cursorCol.aggvalue; vs.rows=cursorRow[1].get(cursorCol.aggvalue, [])',
                      'push sheet of source rows aggregated in this cell')
               ]
    def __init__(self, srcsheet, variableCols):
        super().__init__(srcsheet.name+'_pivot', srcsheet)

        self.nonpivotKeyCols = []
        self.variableCols = variableCols
        for colnum, col in enumerate(srcsheet.keyCols):
            if col not in variableCols:
                newcol = Column(col.name, getter=lambda r, colnum=colnum: r[0][colnum])
                newcol.srccol = col
                self.nonpivotKeyCols.append(newcol)


    @async
    def reload(self):
        self.columns = copy(self.nonpivotKeyCols)
        self.nKeys = len(self.nonpivotKeyCols)
        for aggcol in self.source.columns:
            if not hasattr(aggcol, 'aggregator'):
                continue

            for col in self.variableCols:
                allValues = set(col.values(self.source.rows))
                for value in self.genProgress(allValues):
                    c = Column('_'.join([value, aggcol.name, aggcol.aggregator.__name__]),
                               type=aggcol.aggregator.type or aggcol.type,
                               getter=lambda r,aggcol=aggcol,aggvalue=value: aggcol.aggregator(aggcol.values(r[1].get(aggvalue, []))))
                    c.aggvalue = value
                    self.columns.append(c)

        rowidx = {}
        self.rows = []
        for r in self.genProgress(self.source.rows):
            keys = tuple(keycol.srccol.getValue(r) for keycol in self.nonpivotKeyCols)

            pivotrow = rowidx.get(keys)
            if pivotrow is None:
                pivotrow = (keys, {})
                rowidx[keys] = pivotrow
                self.addRow(pivotrow)

            for col in self.variableCols:
                varval = col.getValue(r)
                matchingRows = pivotrow[1].get(varval)
                if matchingRows is None:
                    pivotrow[1][varval] = [r]
                else:
                    matchingRows.append(r)
