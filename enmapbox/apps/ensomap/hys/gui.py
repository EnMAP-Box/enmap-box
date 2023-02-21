import sys
import os
from PyQt5.QtCore    import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui     import *
import numpy as np
import hys
import csv

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from scipy import stats




# class FileEdit(QLineEdit):
#     def __init__(self, action, parent = None):
#         super(FileEdit, self).__init__(parent)
#         self.setDragEnabled(True)
#         self.action = action

#     # def dragEnterEvent( self, event ):
#     #     data = event.mimeData()
#     #     urls = data.urls()
#     #     if ( urls and urls[0].scheme() == 'file' ):
#     #         event.acceptProposedAction()

#     # def dragMoveEvent( self, event ):
#     #     data = event.mimeData()
#     #     urls = data.urls()
#     #     if ( urls and urls[0].scheme() == 'file' ):
#     #         event.acceptProposedAction()

#     def dropEvent( self, event ):
#         data = event.mimeData()
#         urls = data.urls()
#         if ( urls and urls[0].scheme() == 'file' ):
#             # for some reason, this doubles up the intro slash
#             filepath = str(urls[0].path())[1:]
#             self.setText(filepath)

class WIDGET:

    def __init__(self, parent, title=None):
        
        self.gui = {}
        self.parent = parent
        self.level = []

        # setup the title of the window
        if title is None: title = "Define a title!"
        self.parent.setWindowTitle(title)
        

        base = QVBoxLayout()
        
        self.parent.setLayout(base)
        base.setSizeConstraint(QLayout.SetFixedSize)

        self.gui['base'] = base
        self.level.append(base)
    
    def center(self):
        qr = self.parent.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.parent.move(qr.topLeft())

    
    def level_down(self, wid):
        self.level.append(wid)
    
    def level_up(self):
        del self.level[-1]

    def widget_add_spacing(self, size):
        self.level[-1].addSpacing(size)

    def widget_add_stretch(self):
        self.level[-1].addStretch()

    # create a tab base
    def widget_tab(self, ID = None):
        tab = QTabWidget()
        self.level[-1].addWidget(tab)
        self.level_down(tab)
        if ID is not None:
            self.gui[ID] = tab
    
    def widget_tab_close(self):
        self.level_up()
    
    # create a tab page
    def widget_tab_page(self, title, layout = "V", alignment = Qt.AlignTop, ID = None):
        page = QWidget()
        if layout == "H": 
            page.layout = QHBoxLayout()
        else:
            page.layout = QVBoxLayout()
        page.layout.setAlignment(alignment)
        page.setLayout(page.layout)
        self.level[-1].addTab(page, title)

        # self.level_down(page)
        self.level_down(page.layout)
        if ID is not None:
            self.gui[ID] = page
    
    def widget_tab_page_close(self):
        self.level_up()

    
    def widget_group_box(self, title, layout = "V"):
        group_box = QGroupBox(title)
        self.level[-1].addWidget(group_box)
        if layout == "H":
            lay = QHBoxLayout()
        else:
            lay = QVBoxLayout()
        group_box.setLayout(lay)
        self.level_down(lay)
    
    def widget_group_box_close(self):
        self.level_up()
        

    # create a vertical layout
    def widget_column(self, ID = None, single = False, alignment = None):
        tmp = QVBoxLayout()
        self.level[-1].addLayout(tmp)
        if single is False:
            self.level_down(tmp)
        if ID is not None:
            self.gui[ID] = tmp
        if alignment is not None:
            tmp.setAlignment(alignment)
    
    def widget_column_close(self):
        self.level_up()
    
    # create a horizontal layout
    def widget_row(self, ID = None, single = False, frame = False, alignment = None, enable=True):
        if frame is True:
            frame = QFrame()
            frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        tmp = QHBoxLayout()
        if frame is True:
            frame.setLayout(tmp)
            self.level[-1].addWidget(frame)
        else:
            self.level[-1].addLayout(tmp)
        if single is False:
            self.level_down(tmp)
        if ID is not None:
            if frame is True:
                self.gui[ID] = frame
            else:
                self.gui[ID] = tmp
        if alignment is not None:
            tmp.setAlignment(alignment)
        tmp.setEnabled(enable)
    
    def widget_row_close(self):
        self.level_up()
    
    def widget_row_framed(self, ID = None, alignment = None, hide = False, style = None):
        frame = QFrame()
        if style is not None:
            frame.setFrameStyle(style)
        layout = QHBoxLayout()
        frame.setLayout(layout)
        if alignment is not None:
            layout.setAlignment(alignment)
        if ID is not None:
            self.gui[ID] = frame
        if hide is True:
            frame.hide()
        self.level[-1].addWidget(frame)
        self.level_down(layout)
    
    def widget_row_framed_close(self):
        self.level_up()

    # insert Label
    def widget_label(self, ID = None, text = None, width = None, height = None, alignment=None):
        if text is None:
            text = ''
        tmp = QLabel(text)
        if width is not None:
            tmp.setFixedWidth(width)
        if height is not None:
            tmp.setFixedHeight(height)
        if ID is not None:
            self.gui[ID] = tmp
        if alignment is not None:
            tmp.setAlignment(alignment)
        self.level[-1].addWidget(tmp)
    
    # insert field
    def widget_text(self, ID = None, text = None, width = None, edit = False):
        if text is None:
            tmp = QLineEdit()
        else:
            tmp = QLineEdit(text)
        if width is not None:
            tmp.setFixedWidth(width)
        if edit is False:
            tmp.setReadOnly(True)
        else:
            tmp.setReadOnly(False)
        if ID is not None:
            self.gui[ID] = tmp
        self.level[-1].addWidget(tmp)

    def widget_text_dd(self, ID = None, text = None, width = None, edit = False):
        tmp = FileEdit()
        if text is not None:
            tmp.setText(text)
        if width is not None:
            tmp.setFixedWidth(width)
        if edit is False:
            tmp.setReadOnly(True)
        else:
            tmp.setReadOnly(False)
        if ID is not None:
            self.gui[ID] = tmp
        self.level[-1].addWidget(tmp)


    # insert tool button
    def widget_tool_button(self, ID = None, text = None, action = None, width=None):
        tmp = QToolButton()
        if text is not None:
            tmp.setText(text)
        if action is not None:
            tmp.clicked.connect(action)
        if ID is not None:
            self.gui[ID] = tmp
        if width is not None:
            tmp.setFixedWidth(width)
        self.level[-1].addWidget(tmp)
    
    # insert push button
    def widget_push_button(self, text, ID = None, action = None, width = None):
        tmp = QPushButton(text)
        if ID is not None:
            self.gui[ID] = tmp
        if action is not None:
            tmp.clicked.connect(action)
        self.level[-1].addWidget(tmp)
    
    # insert check button
    def widget_check_button(self, text, ID = None, width = None, set_checked=False, action=None):
        tmp = QCheckBox(text)
        if ID is not None:
            self.gui[ID] = tmp
        self.level[-1].addWidget(tmp)
        if width is not None:
            tmp.setFixedWidth(width)
        if action is not None:
            tmp.clicked.connect(action)
        tmp.setChecked(set_checked)
    
    def widget_radio_button(self, text, ID = None, width = None, default=False, group=None, action=None):
        tmp = QRadioButton(text)
        if group is not None:
            group.addButton(tmp)
        if ID is not None:
            self.gui[ID] = tmp
        self.level[-1].addWidget(tmp)
        if width is not None:
            tmp.setFixedWidth(width)
        if action is not None:
            tmp.clicked.connect(action)
        tmp.setChecked(default)

    # insert progress bar
    def widget_progress(self, width = None, height = None, ID = None):
        tmp = QProgressBar()
        self.level[-1].addWidget(tmp)
        if ID is not None:
            self.gui[ID] = tmp
        if width is not None:
            tmp.setFixedWidth = width
        if height is not None:
            tmp.setFixedHeight = height
    
    def widget_list(self, width = None, height = None, ID = None):
        tmp = QListWidget()
        if width is not None:
            tmp.setFixedWidth(width)
        if height is not None:
            tmp.setFixedHeight(height)
        if ID is not None:
            self.gui[ID] = tmp
        self.level[-1].addWidget(tmp)
    
    def widget_table(self, width=None, height=None, ID=None):
        tmp = QTableWidget()
        if width is not None:
            tmp.setFixedWidth(width)
        if height is not None:
            tmp.setFixedHeight(height)
        if ID is not None:
            self.gui[ID] = tmp
        self.level[-1].addWidget(tmp)
    

    
    def widget_spinbox(self, width=None, min=None, max=None, ID=None, action=None, step=None, default=None):
        tmp = QSpinBox()
        if width is not None:
            tmp.setFixedWidth(width)
        if min is not None:
            tmp.setMinimum(min)
        if max is not None:
            tmp.setMaximum(max)
        if ID is not None:
            self.gui[ID] = tmp
        if action is not None:
            tmp.valueChanged.connect(action)
        if step is not None:
            tmp.setSingleStep(step)
        if default is not None:
            tmp.setValue(default)
        self.level[-1].addWidget(tmp)
    
    def widget_add_widget(self, wid, ID = None):
        self.level[-1].addWidget(wid)
        if ID is not None:
            self.gui[ID] = tmp



class CAL_EST(QWidget):
    def __init__(self, maingui, X, Y, parent=None):
        super(CAL_EST, self).__init__(parent=parent)
        self.maingui = maingui
        gain, offset, r_value, p_value, std_err = stats.linregress(X, Y)
        self.gain = gain
        self.offset = offset

        self.gui = hys.WIDGET(self, 'Scatter Plot')
         # a figure instance to plot on
        figure = plt.figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        canvas = FigureCanvas(figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        toolbar = NavigationToolbar(canvas, self)

        self.gui.widget_column()
        self.gui.widget_add_widget(toolbar)
        self.gui.widget_add_widget(canvas)
        
        self.gui.widget_column()
        self.gui.widget_row(alignment=Qt.AlignLeft)
        self.gui.widget_label(text="Gain = ", width=80)
        self.gui.widget_text(text=str(gain))
        self.gui.widget_row_close()
        self.gui.widget_row()
        self.gui.widget_label(text='Offset = ', width=80)
        self.gui.widget_text(text=str(offset))
        self.gui.widget_row_close()
        self.gui.widget_row()
        self.gui.widget_label(text='R<sup>2</sub>', width=80)
        self.gui.widget_text(text=str(r_value**2))
        self.gui.widget_row_close()
        self.gui.widget_column_close()
        self.gui.widget_row_framed(alignment=Qt.AlignLeft, style = QFrame.StyledPanel | QFrame.Raised)
        self.gui.widget_push_button('Select', action=self.select)
        self.gui.widget_push_button('Clear', action=self.clear)
        self.gui.widget_push_button('Close', action=self.cancel)
        self.gui.widget_row_close()
        self.gui.widget_row_framed_close()

        # # Just some button connected to `plot` method
        # button = QPushButton('Close')
        # button.clicked.connect(self.cancel)

        # # set the layout
        # layout = QVBoxLayout()
        # layout.addWidget(toolbar)
        # layout.addWidget(canvas)
        # layout.addWidget(button)
        # self.setLayout(layout)
        
        # plot the function
        figure.clear()
        ax = figure.add_subplot(111)
        ax.scatter(X, Y, marker='o')

        # estimate gain/offset/R2

        # axes = plt.gca()
        xx = np.linspace(X.min(), X.max(), 100)
        ax.plot(xx, gain * xx + offset, '-')
        canvas.draw()
        self.maingui.setEnabled(False)
        self.show()

    def select(self):
        self.maingui.gui.gui['cal_txt_gain'].setText(str(self.gain))
        self.maingui.gui.gui['cal_txt_offset'].setText(str(self.offset))

    def clear(self):
        self.maingui.gui.gui['cal_txt_gain'].setText("")
        self.maingui.gui.gui['cal_txt_offset'].setText("")

    def closeEvent(self, event):
        self.maingui.setEnabled(True)
    
    def cancel(self):
        self.close()


class CSV(QWidget):

    def __init__(self, dname, widParent, widButID, widLabID, csv_data, parent=None):
        super(CSV, self).__init__(parent=parent)
        self.widParent = widParent # parent interface to freeze when CSV is launched
        self.csv_data = csv_data
        
        # setup the cancel product
        self.csv_data_cancel = hys.CSV_DATA()
        self.csv_data_cancel.copy_from(self.csv_data)

        self.dname = dname
        self.widLabID = widLabID
        self.widButID = widButID

        # design the interface
        self.gui = hys.WIDGET(self, self.widParent.app_name + ' - Import CSV')
        
        self.gui.widget_column()

        self.gui.widget_group_box('SOURCE')
        self.gui.widget_row()
        self.gui.widget_text(ID='csv_field_fname')
        self.gui.widget_tool_button(text='...', action=self.open_csv)
        self.gui.widget_tool_button(text='Reset')
        self.gui.widget_tool_button(text='Clear', action=self.clear)
        self.gui.widget_row_close()
        self.gui.widget_group_box_close()

        self.gui.widget_add_spacing(10)
        
        self.gui.widget_row()
        self.gui.widget_column()
        self.gui.widget_group_box('DELIMITERS')
        self.gui.widget_column(ID='group_delimiters')
        groupDelimiter = QButtonGroup(self.gui.gui['group_delimiters'])
        self.gui.widget_radio_button('Tab',       group=groupDelimiter, ID='but_tab',               action=self.set_delimiter)
        self.gui.widget_radio_button('Semicolon', group=groupDelimiter, ID='but_smc',               action=self.set_delimiter)
        self.gui.widget_radio_button('Colon',     group=groupDelimiter, ID='but_col',               action=self.set_delimiter)
        self.gui.widget_radio_button('Comma',     group=groupDelimiter, ID='but_com', default=True, action=self.set_delimiter)
        self.gui.widget_column_close()
        self.gui.widget_group_box_close()
        self.gui.widget_column_close()
        self.gui.widget_column()
        self.gui.widget_group_box('HEADER')
        self.gui.widget_row(alignment=Qt.AlignLeft)
        self.gui.widget_label(text='Starting row:')
        self.gui.widget_spinbox(min=0, default=0, ID='n_head_line')
        self.gui.widget_row_close()
        self.gui.widget_group_box_close()
        self.gui.widget_group_box('COORDINATES')
        self.gui.widget_column(ID='group_coordinates')
        groupCoordinates = QButtonGroup(self.gui.gui['group_coordinates'])
        self.gui.widget_radio_button('Geographical (lat/lon, UTM, etc.)', group=groupCoordinates, ID='but_geo', default=True, action=self.set_coordinates)
        self.gui.widget_radio_button('Image (X, Y)',                      group=groupCoordinates, ID='but_img',               action=self.set_coordinates)
        self.gui.widget_column_close()
        self.gui.widget_group_box_close()
        self.gui.widget_column_close()
        self.gui.widget_row_close()

        self.gui.widget_add_spacing(10)
        self.gui.widget_group_box('DATA PREVIEW')
        self.gui.widget_table(ID='wid_tab', width=700, height=400)
        self.gui.widget_group_box_close()

        self.gui.widget_add_spacing(10)
        self.gui.widget_row_framed(alignment=Qt.AlignLeft, style = QFrame.StyledPanel | QFrame.Raised)
        self.gui.widget_push_button('OK', action=self.ok)
        self.gui.widget_push_button('Cancel', action=self.cancel)
        self.gui.widget_row_framed_close()

        self.gui.widget_column_close()

        self.widParent.setEnabled(False)
        self.show()
        self.gui.center()

        if self.csv_data.rows != []:
            self.gui.gui['csv_field_fname'].setText(os.path.basename(self.csv_data.fname))
            if   self.csv_data.delimiter == '\t': but_delim = [True, False, False, False]
            elif self.csv_data.delimiter == ';':  but_delim = [False, True, False, False]
            elif self.csv_data.delimiter == ':':  but_delim = [False, False, True, False]
            else:                                 but_delim = [False, False, False, True]
            self.gui.gui['but_tab'].setChecked(but_delim[0])
            self.gui.gui['but_smc'].setChecked(but_delim[1])
            self.gui.gui['but_col'].setChecked(but_delim[2])
            self.gui.gui['but_com'].setChecked(but_delim[3])
            self.gui.gui['n_head_line'].setValue(self.csv_data.n_header)
            if self.csv_data.coordinates == 1: but_coord = [True, False]
            else:                              but_coord = [False, True]
            self.gui.gui['but_geo'].setChecked(but_coord[0])
            self.gui.gui['but_img'].setChecked(but_coord[1])
            self.display_table()

        self.gui.gui['n_head_line'].valueChanged.connect(self.update_n_header)

        # self.display_table()

    def display_table(self):
        self.csv_data.load()
        # print('delimiter = ', self.csv_data.delimiter)
        # print('n_rows    = ', self.csv_data.n_rows)
        # print('n_cols    = ', self.csv_data.n_cols)
        print(self.csv_data.hrows)
        self.gui.gui['wid_tab'].setRowCount(self.csv_data.n_rows)
        self.gui.gui['wid_tab'].setColumnCount(self.csv_data.n_cols)
        for kr in range(self.csv_data.n_rows):
            for kl in range(self.csv_data.n_cols):
                item = QTableWidgetItem()
                item.setFlags(Qt.ItemIsEnabled)
                item.setText((self.csv_data.rows[kr])[kl])
                self.gui.gui['wid_tab'].setItem(kr,kl, item)


    ###
    # OPEN CSV DATA
    ###
    def open_csv(self):
        title = self.widParent.app_name + " - Open CSV file"
        filename = hys.pick_file(self, title=title, dname=self.dname, filter='*.csv')
        if filename == "":
            return
        self.dname = os.path.dirname(filename)
        self.csv_data.load(filename=filename)
        self.gui.gui['csv_field_fname'].setText(os.path.basename(filename))
        self.display_table()

    def set_delimiter(self):
        if self.csv_data.rows == []:
            self.gui.gui['but_tab'].setChecked(False)
            self.gui.gui['but_smc'].setChecked(False)
            self.gui.gui['but_col'].setChecked(False)
            self.gui.gui['but_com'].setChecked(True)
            return
        if self.gui.gui['but_tab'].isChecked():
            self.csv_data.set_delimiter('\t')
        elif self.gui.gui['but_com'].isChecked():
            self.csv_data.set_delimiter(',')
        elif self.gui.gui['but_smc'].isChecked():
            self.csv_data.set_delimiter(';')
        elif self.gui.gui['but_col'].isChecked():
            self.csv_data.set_delimiter(':')
        else:
            return
        self.display_table()

    def update_n_header(self):
        # This functin is call when created, to avoid error we have to check if a data is loaded
        if self.csv_data.rows == []:
            return
        n_header = self.gui.gui['n_head_line'].value()
        self.csv_data.set_n_header(n_header)
        self.display_table()
        
    def set_coordinates(self):
        if self.csv_data.rows == []:
            self.gui.gui['but_geo'].setChecked(True)
            self.gui.gui['but_img'].setChecked(False)
            return
        if self.gui.gui['but_geo'].isChecked():
            self.csv_data.set_coordinates(1)
        elif self.gui.gui['but_img'].isChecked():
            self.csv_data.set_coordinates(0)
        else:
            return


    # this function return a msg containing information to be displayed in the label
    def get_info(self):
        if self.csv_data.rows == []:
            return 'No data loaded'
        msg = 'Ref data (' + str(self.csv_data.n_rows) + ' points with ' + str(self.csv_data.n_cols) + ' elements) in '
        if self.csv_data.coordinates == 1:
            msg += 'geographical'
        elif self.csv_data.coordinates == 0:
            msg += 'image'
        else:
            msg += ''
        msg += ' coordinates'
        return msg
    
    def clear(self):
        self.csv_data.reset()
        self.gui.gui['csv_field_fname'].setText('')
        self.gui.gui['csv_field_fname'].repaint()
        self.gui.gui['but_tab'].setChecked(False)
        self.gui.gui['but_tab'].repaint()
        self.gui.gui['but_smc'].setChecked(False)
        self.gui.gui['but_smc'].repaint()
        self.gui.gui['but_col'].setChecked(False)
        self.gui.gui['but_col'].repaint()
        self.gui.gui['but_com'].setChecked(True)
        self.gui.gui['but_com'].repaint()
        self.gui.gui['n_head_line'].setValue(1)
        self.gui.gui['n_head_line'].repaint()
        self.gui.gui['but_geo'].setChecked(True)
        self.gui.gui['but_geo'].repaint()
        self.gui.gui['but_img'].setChecked(False)
        self.gui.gui['but_img'].repaint()
        self.gui.gui['wid_tab'].setColumnCount(0)
        self.gui.gui['wid_tab'].setRowCount(0)
        self.gui.gui['wid_tab'].repaint()

    def ok(self):
        self.widParent.gui.gui[self.widLabID].setText(self.get_info())
        if self.csv_data.rows == []:
            self.widParent.gui.gui[self.widButID].setText('Load')
        else:
            self.widParent.gui.gui[self.widButID].setText('View')
        self.close()

    def closeEvent(self, event):
        self.widParent.setEnabled(True)
    
    def cancel(self):
        self.csv_data.copy_from(self.csv_data_cancel)
        self.close()        






