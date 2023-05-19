from qtpy.QtCore import Signal, Qt
from qtpy.QtWidgets import QTableWidget, QSizePolicy, QSpacerItem, QStackedWidget, QLabel, QAbstractItemView, QTableWidgetItem, QHeaderView, QHBoxLayout, \
    QVBoxLayout, QWidget, QDialog, QListWidget, QListWidgetItem, QApplication, QSplitter, QGridLayout

from pyqt_openai.inputDialog import InputDialog
from pyqt_openai.sqlite import SqliteDatabase
from pyqt_openai.svgButton import SvgButton


class PropGroupList(QWidget):
    added = Signal(int)
    deleted = Signal(int)
    currentRowChanged = Signal(int)

    def __init__(self, db: SqliteDatabase):
        super().__init__()
        self.__initVal(db)
        self.__initUi()

    def __initVal(self, db):
        self.__db = db

    def __initUi(self):
        self.__addBtn = SvgButton()
        self.__delBtn = SvgButton()

        self.__addBtn.setIcon('ico/add.svg')
        self.__delBtn.setIcon('ico/delete.svg')

        self.__addBtn.clicked.connect(self.__add)
        self.__delBtn.clicked.connect(self.__delete)

        lay = QHBoxLayout()
        lay.addWidget(QLabel('Property Group'))
        lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.MinimumExpanding))
        lay.addWidget(self.__addBtn)
        lay.addWidget(self.__delBtn)
        lay.setAlignment(Qt.AlignRight)
        lay.setContentsMargins(0, 0, 0, 0)

        topWidget = QWidget()
        topWidget.setLayout(lay)

        defaultPropPromptGroupArr = self.__db.selectPropPromptGroup()

        self.__propList = QListWidget()

        # TODO abcd
        for group in defaultPropPromptGroupArr:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, group[0])
            item.setText(group[1])
            self.__propList.addItem(item)
        self.__propList.currentRowChanged.connect(self.__currentRowChanged)

        lay = QVBoxLayout()
        lay.addWidget(topWidget)
        lay.addWidget(self.__propList)
        lay.setContentsMargins(0, 0, 5, 0)

        self.setLayout(lay)

        self.__propList.setCurrentRow(0)

    def __add(self):
        dialog = InputDialog('Add', '', self)
        reply = dialog.exec()
        if reply == QDialog.Accepted:
            text = dialog.getText()
            id = self.__db.insertPropPromptGroup(text)
            item = QListWidgetItem()
            item.setData(Qt.UserRole, id)
            item.setText(text)
            self.__propList.addItem(item)
            self.__propList.setCurrentItem(item)
            self.added.emit(id)

    def __currentRowChanged(self, r_idx):
        self.currentRowChanged.emit(self.__propList.item(r_idx).data(Qt.UserRole))

    def __delete(self):
        i = self.__propList.currentRow()
        item = self.__propList.takeItem(i)
        id = item.data(Qt.UserRole)
        self.__db.deletePropPromptGroup(id)
        self.deleted.emit(id)


class PropTable(QWidget):
    """
    benchmarked https://gptforwork.com/tools/prompt-generator
    """
    updated = Signal(str)

    def __init__(self, db: SqliteDatabase, id):
        super().__init__()
        self.__initVal(db, id)
        self.__initUi()

    def __initVal(self, db, id):
        self.__db = db

        self.__title = self.__db.selectPropPromptGroupId(id)[1]
        self.__previousPromptPropArr = self.__db.selectPropPromptAttribute(id)

    def __initUi(self):
        self.__addBtn = SvgButton()
        self.__delBtn = SvgButton()

        self.__addBtn.setIcon('ico/add.svg')
        self.__delBtn.setIcon('ico/delete.svg')

        self.__addBtn.clicked.connect(self.__add)
        self.__delBtn.clicked.connect(self.__delete)

        lay = QHBoxLayout()
        lay.addWidget(QLabel(self.__title))
        lay.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.MinimumExpanding))
        lay.addWidget(self.__addBtn)
        lay.addWidget(self.__delBtn)
        lay.setAlignment(Qt.AlignRight)
        lay.setContentsMargins(0, 0, 0, 0)

        topWidget = QWidget()
        topWidget.setLayout(lay)

        self.__table = QTableWidget()
        self.__table.setColumnCount(2)
        self.__table.setRowCount(len(self.__previousPromptPropArr))
        self.__table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.__table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__table.setHorizontalHeaderLabels(['Name', 'Value'])

        for i in range(len(self.__previousPromptPropArr)):
            name = self.__previousPromptPropArr[i][2]
            value = self.__previousPromptPropArr[i][3]
            item1 = QTableWidgetItem(name)
            item1.setData(Qt.UserRole, self.__previousPromptPropArr[i][0])
            item2 = QTableWidgetItem(value)

            item1.setTextAlignment(Qt.AlignCenter)
            item2.setTextAlignment(Qt.AlignCenter)

            self.__table.setItem(i, 0, item1)
            self.__table.setItem(i, 1, item2)

        self.__table.itemChanged.connect(self.__itemChanged)

        lay = QVBoxLayout()
        lay.addWidget(topWidget)
        lay.addWidget(self.__table)
        lay.setContentsMargins(5, 0, 0, 0)

        self.setLayout(lay)

    def __itemChanged(self, item: QTableWidgetItem):
        if item.column() == 1:
            prompt_text = ''
            for i in range(self.__table.rowCount()):
                if self.__table.item(i, 1).text().strip():
                    prompt_text += f'{self.__table.item(i, 0).text()}: {self.__table.item(i, 1).text()}\n'
            self.updated.emit(prompt_text)

    def __add(self):
        dialog = InputDialog('Name', '', self)
        reply = dialog.exec()
        if reply == QDialog.Accepted:
            text = dialog.getText()
            self.__table.setRowCount(self.__table.rowCount()+1)
            item1 = QTableWidgetItem(text)
            item1.setTextAlignment(Qt.AlignCenter)
            self.__table.setItem(self.__table.rowCount()-1, 0, item1)

            item2 = QTableWidgetItem('')
            item2.setTextAlignment(Qt.AlignCenter)
            self.__table.setItem(self.__table.rowCount()-1, 1, item2)

    def __delete(self):
        for i in sorted(set([i.row() for i in self.__table.selectedIndexes()]), reverse=True):
            self.__table.removeRow(i)


class PropPage(QWidget):
    updated = Signal(str)

    def __init__(self, db: SqliteDatabase):
        super().__init__()
        self.__initVal(db)
        self.__initUi()

    def __initVal(self, db):
        self.__db = db

    def __initUi(self):
        leftWidget = PropGroupList(self.__db)
        leftWidget.added.connect(self.__propGroupAdded)
        leftWidget.deleted.connect(self.__propGroupDeleted)
        leftWidget.currentRowChanged.connect(self.__showProp)

        propTable = PropTable(self.__db, id=1)
        propTable.updated.connect(self.updated)

        self.__rightWidget = QStackedWidget()
        self.__rightWidget.addWidget(propTable)

        mainWidget = QSplitter()
        mainWidget.addWidget(leftWidget)
        mainWidget.addWidget(self.__rightWidget)
        mainWidget.setChildrenCollapsible(False)
        mainWidget.setSizes([300, 700])

        lay = QGridLayout()
        lay.addWidget(mainWidget)

        self.setLayout(lay)

    def __propGroupAdded(self, id):
        propTable = PropTable(self.__db, id)
        propTable.updated.connect(self.updated)
        self.__rightWidget.addWidget(propTable)

    def __propGroupDeleted(self, n):
        # n-1 because the index starts with zero
        w = self.__rightWidget.widget(n-1)
        self.__rightWidget.removeWidget(w)

    def __showProp(self, n):
        # n-1 because the index starts with zero
        self.__rightWidget.setCurrentIndex(n-1)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    w = PropPage()
    w.show()
    sys.exit(app.exec_())
