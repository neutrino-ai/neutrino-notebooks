from .cell import Cell


class CodeCell(Cell):
    def __init__(self, source: str):
        super().__init__('Code')
        self.source = source

    def __str__(self):
        return self.source
