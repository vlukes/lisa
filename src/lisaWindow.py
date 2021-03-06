# /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

import sys
import os
import numpy as np

import time

import datareader
import segmentation
from seg2mesh import gen_mesh_from_voxels, mesh2vtk, smooth_mesh
import virtual_resection

try:
    from viewer import QVTKViewer
    viewer3D_available = True

except ImportError:
    viewer3D_available = False
path_to_script = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(path_to_script, "../extern/pyseg_base/src"))

from PyQt4.QtGui import QApplication, QMainWindow, QWidget,\
    QGridLayout, QLabel, QPushButton, QFrame, \
    QFont, QPixmap
from PyQt4.Qt import QString
from seed_editor_qt import QTSeedEditor


# GUI
class OrganSegmentationWindow(QMainWindow):

    def __init__(self, oseg=None):

        self.oseg = oseg

        QMainWindow.__init__(self)
        self.initUI()

        if oseg is not None:
            if oseg.data3d is not None:
                self.setLabelText(self.text_dcm_dir, self.oseg.datapath)
                self.setLabelText(self.text_dcm_data, self.getDcmInfo())

        self.statusBar().showMessage('Ready')

    def initUI(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        grid = QGridLayout()
        grid.setSpacing(10)

        # status bar
        self.statusBar().showMessage('Ready')

        font_label = QFont()
        font_label.setBold(True)
        font_info = QFont()
        font_info.setItalic(True)
        font_info.setPixelSize(10)

        # # # # # # #
        # #  LISA logo
        # font_title = QFont()
        # font_title.setBold(True)
        # font_title.setSize(24)

        lisa_title = QLabel('LIver Surgery Analyser')
        info = QLabel('Developed by:\n' +
                      'University of West Bohemia\n' +
                      'Faculty of Applied Sciences\n' +
                      QString.fromUtf8('M. Jiřík, V. Lukeš - 2013') +
                      '\n\nVersion: ' + self.oseg.version
                      )
        info.setFont(font_info)
        lisa_title.setFont(font_label)
        lisa_logo = QLabel()
        logopath = os.path.join(path_to_script, "../applications/LISA256.png")
        logo = QPixmap(logopath)
        lisa_logo.setPixmap(logo)  # scaledToWidth(128))
        grid.addWidget(lisa_title, 0, 1)
        grid.addWidget(info, 1, 1)
        grid.addWidget(lisa_logo, 0, 2, 2, 2)
        # rid.setColumnMinimumWidth(1, logo.width()/2)
        # rid.setColumnMinimumWidth(2, logo.width()/2)
        # rid.setColumnMinimumWidth(3, logo.width()/2)

        # # dicom reader
        rstart = 2
        hr = QFrame()
        hr.setFrameShape(QFrame.HLine)
        text_dcm = QLabel('DICOM reader')
        text_dcm.setFont(font_label)
        btn_dcmdir = QPushButton("Load DICOM", self)
        btn_dcmdir.clicked.connect(self.loadDataDir)

        btn_datafile = QPushButton("Load file", self)
        btn_datafile.clicked.connect(self.loadDataFile)

        btn_dcmcrop = QPushButton("Crop", self)
        btn_dcmcrop.clicked.connect(self.cropDcm)

        # voxelsize gui comment
        # elf.scaling_mode = 'original'
        # ombo_vs = QComboBox(self)
        # ombo_vs.activated[str].connect(self.changeVoxelSize)
        # eys = scaling_modes.keys()
        # eys.sort()
        # ombo_vs.addItems(keys)
        # ombo_vs.setCurrentIndex(keys.index(self.scaling_mode))
        # elf.text_vs = QLabel('Voxel size:')
        # end-- voxelsize gui
        self.text_dcm_dir = QLabel('DICOM dir:')
        self.text_dcm_data = QLabel('DICOM data:')
        grid.addWidget(hr, rstart + 0, 2, 1, 4)
        grid.addWidget(text_dcm, rstart + 0, 1, 1, 3)
        grid.addWidget(btn_dcmdir, rstart + 1, 1)
        grid.addWidget(btn_datafile, rstart + 1, 2)
        grid.addWidget(btn_dcmcrop, rstart + 1, 3)
        # voxelsize gui comment
        # grid.addWidget(self.text_vs, rstart + 3, 1)
        # grid.addWidget(combo_vs, rstart + 4, 1)
        grid.addWidget(self.text_dcm_dir, rstart + 6, 1, 1, 3)
        grid.addWidget(self.text_dcm_data, rstart + 7, 1, 1, 3)
        rstart += 9

        # # # # # # # # #  segmentation
        hr = QFrame()
        hr.setFrameShape(QFrame.HLine)
        text_seg = QLabel('Segmentation')
        text_seg.setFont(font_label)
        btn_mask = QPushButton("Mask region", self)
        btn_mask.clicked.connect(self.maskRegion)
        btn_segauto = QPushButton("Automatic seg.", self)
        btn_segauto.clicked.connect(self.autoSeg)
        btn_segman = QPushButton("Manual seg.", self)
        btn_segman.clicked.connect(self.manualSeg)
        self.text_seg_data = QLabel('segmented data:')
        grid.addWidget(hr, rstart + 0, 2, 1, 4)
        grid.addWidget(text_seg, rstart + 0, 1)
        grid.addWidget(btn_mask, rstart + 1, 1)
        grid.addWidget(btn_segauto, rstart + 1, 2)
        grid.addWidget(btn_segman, rstart + 1, 3)
        grid.addWidget(self.text_seg_data, rstart + 2, 1, 1, 3)
        rstart += 3

        # # # # # # # # #  save/view
        # hr = QFrame()
        # hr.setFrameShape(QFrame.HLine)
        btn_segsave = QPushButton("Save", self)
        btn_segsave.clicked.connect(self.saveOut)
        btn_segsavedcm = QPushButton("Save Dicom", self)
        btn_segsavedcm.clicked.connect(self.saveOutDcm)
        btn_segview = QPushButton("View3D", self)
        if viewer3D_available:
            btn_segview.clicked.connect(self.view3D)

        else:
            btn_segview.setEnabled(False)

        grid.addWidget(btn_segsave, rstart + 0, 1)
        grid.addWidget(btn_segview, rstart + 0, 3)
        grid.addWidget(btn_segsavedcm, rstart + 0, 2)
        rstart += 2

        # # # # Virtual resection

        hr = QFrame()
        hr.setFrameShape(QFrame.HLine)
        rstart += 1

        hr = QFrame()
        hr.setFrameShape(QFrame.HLine)
        text_resection = QLabel('Virtual resection')
        text_resection.setFont(font_label)

        btn_vesselseg = QPushButton("Vessel segmentation", self)
        btn_vesselseg.clicked.connect(self.btnVesselSegmentation)

        btn_lesions = QPushButton("Lesions localization", self)
        btn_lesions.clicked.connect(self.btnLesionLocalization)

        btn_resection = QPushButton("Virtual resection", self)
        btn_resection.clicked.connect(self.btnVirtualResection)

        grid.addWidget(hr, rstart + 0, 2, 1, 4)
        grid.addWidget(text_resection, rstart + 0, 1)
        grid.addWidget(btn_vesselseg, rstart + 1, 1)
        grid.addWidget(btn_lesions, rstart + 1, 2)
        grid.addWidget(btn_resection, rstart + 1, 3)

        # # # # # # #

        hr = QFrame()
        hr.setFrameShape(QFrame.HLine)
        # rid.addWidget(hr, rstart + 0, 0, 1, 4)

        rstart += 3
        # quit
        btn_quit = QPushButton("Quit", self)
        btn_quit.clicked.connect(self.quit)
        grid.addWidget(btn_quit, rstart + 1, 1, 1, 2)

        cw.setLayout(grid)
        self.setWindowTitle('LISA')
        self.show()

    def quit(self, event):
        self.close()

    def changeVoxelSize(self, val):
        self.scaling_mode = str(val)

    def setLabelText(self, obj, text):
        dlab = str(obj.text())
        obj.setText(dlab[:dlab.find(':')] + ': %s' % text)

    def getDcmInfo(self):
        vx_size = self.oseg.voxelsize_mm
        vsize = tuple([float(ii) for ii in vx_size])
        ret = ' %dx%dx%d,  %fx%fx%f mm' % (self.oseg.data3d.shape + vsize)

        return ret

    # def setVoxelVolume(self, vxs):
    #     self.voxel_volume = np.prod(vxs)

    def __get_datafile(self, app=False, directory=''):
        """
        Draw a dialog for directory selection.
        """

        from PyQt4.QtGui import QFileDialog
        if app:
            dcmdir = QFileDialog.getOpenFileName(
                caption='Select Data File',
                directory=directory
                # ptions=QFileDialog.ShowDirsOnly,
            )
        else:
            app = QApplication(sys.argv)
            dcmdir = QFileDialog.getOpenFileName(
                caption='Select DICOM Folder',
                # ptions=QFileDialog.ShowDirsOnly,
                directory=directory
            )
            # pp.exec_()
            app.exit(0)
        if len(dcmdir) > 0:

            dcmdir = "%s" % (dcmdir)
            dcmdir = dcmdir.encode("utf8")
        else:
            dcmdir = None
        return dcmdir

    def __get_datadir(self, app=False, directory=''):
        """
        Draw a dialog for directory selection.
        """

        from PyQt4.QtGui import QFileDialog
        if app:
            dcmdir = QFileDialog.getExistingDirectory(
                caption='Select DICOM Folder',
                options=QFileDialog.ShowDirsOnly,
                directory=directory
            )
        else:
            app = QApplication(sys.argv)
            dcmdir = QFileDialog.getExistingDirectory(
                caption='Select DICOM Folder',
                options=QFileDialog.ShowDirsOnly,
                directory=directory
            )
            # pp.exec_()
            app.exit(0)
        if len(dcmdir) > 0:

            dcmdir = "%s" % (dcmdir)
            dcmdir = dcmdir.encode("utf8")
        else:
            dcmdir = None
        return dcmdir

    def loadDataFile(self):
        self.statusBar().showMessage('Reading data file...')
        QApplication.processEvents()

        oseg = self.oseg
        # f oseg.datapath is None:
        #     seg.datapath = dcmreader.get_dcmdir_qt(
        #        app=True,
        #        directory=self.oseg.input_datapath_start
        #
        oseg.datapath = self.__get_datafile(
            app=True,
            directory=self.oseg.input_datapath_start
        )

        if oseg.datapath is None:
            self.statusBar().showMessage('No data path specified!')
            return
        self.importDataWithGui()

    def loadDataDir(self):
        self.statusBar().showMessage('Reading DICOM directory...')
        QApplication.processEvents()

        oseg = self.oseg
        # f oseg.datapath is None:
        #     seg.datapath = dcmreader.get_dcmdir_qt(
        #        app=True,
        #        directory=self.oseg.input_datapath_start
        #
        oseg.datapath = self.__get_datadir(
            app=True,
            directory=self.oseg.input_datapath_start
        )

        if oseg.datapath is None:
            self.statusBar().showMessage('No DICOM directory specified!')
            return

        self.importDataWithGui()

    def importDataWithGui(self):
        oseg = self.oseg

        reader = datareader.DataReader()

        # seg.data3d, metadata =
        datap = reader.Get3DData(oseg.datapath, dataplus_format=True)
        # rint datap.keys()
        # self.iparams['series_number'] = self.metadata['series_number']
        # self.iparams['datapath'] = self.datapath
        oseg.import_dataplus(datap)
        self.setLabelText(self.text_dcm_dir, oseg.datapath)
        self.setLabelText(self.text_dcm_data, self.getDcmInfo())
        self.statusBar().showMessage('Ready')

    def cropDcm(self):
        oseg = self.oseg

        if oseg.data3d is None:
            self.statusBar().showMessage('No DICOM data!')
            return

        self.statusBar().showMessage('Cropping DICOM data...')
        QApplication.processEvents()

        pyed = QTSeedEditor(oseg.data3d, mode='crop',
                            voxelSize=oseg.voxelsize_mm)
        # @TODO
        mx = self.oseg.viewermax
        mn = self.oseg.viewermin
        width = mx - mn
        # enter = (float(mx)-float(mn))
        center = np.average([mx, mn])
        logger.debug("window params max %f min %f width, %f center %f" %
                     (mx, mn, width, center))
        pyed.changeC(center)
        pyed.changeW(width)
        pyed.exec_()

        crinfo = pyed.getROI()
        if crinfo is not None:
            tmpcrinfo = []
            for ii in crinfo:
                tmpcrinfo.append([ii.start, ii.stop])

            # seg.data3d = qmisc.crop(oseg.data3d, oseg.crinfo)
            oseg.crop(tmpcrinfo)

        self.setLabelText(self.text_dcm_data, self.getDcmInfo())
        self.statusBar().showMessage('Ready')

    def maskRegion(self):
        if self.oseg.data3d is None:
            self.statusBar().showMessage('No DICOM data!')
            return

        self.statusBar().showMessage('Mask region...')
        QApplication.processEvents()

        pyed = QTSeedEditor(self.oseg.data3d, mode='mask',
                            voxelSize=self.oseg.voxelsize_mm)

        mx = self.oseg.viewermax
        mn = self.oseg.viewermin
        width = mx - mn
        # enter = (float(mx)-float(mn))
        center = np.average([mx, mn])
        logger.debug("window params max %f min %f width, %f center %f" %
                     (mx, mn, width, center))
        pyed.changeC(center)
        pyed.changeW(width)
        pyed.exec_()

        self.statusBar().showMessage('Ready')

    def autoSeg(self):
        if self.oseg.data3d is None:
            self.statusBar().showMessage('No DICOM data!')
            return

        self.oseg.interactivity(
            min_val=self.oseg.viewermin,
            max_val=self.oseg.viewermax)
        self.checkSegData('auto. seg., ')

    def manualSeg(self):
        oseg = self.oseg
        # rint 'ms d3d ', oseg.data3d.shape
        # rint 'ms seg ', oseg.segmentation.shape
        # rint 'crinfo ', oseg.crinfo
        if oseg.data3d is None:
            self.statusBar().showMessage('No DICOM data!')
            return
        sgm = oseg.segmentation.astype(np.uint8)

        pyed = QTSeedEditor(oseg.data3d,
                            seeds=sgm,
                            mode='draw',
                            voxelSize=oseg.voxelsize_mm, volume_unit='ml')
        pyed.exec_()

        oseg.segmentation = pyed.getSeeds()
        self.oseg.processing_time = time.time() - self.oseg.time_start
        self.checkSegData('manual seg., ')

    def checkSegData(self, msg):
        oseg = self.oseg
        if oseg.segmentation is None:
            self.statusBar().showMessage('No segmentation!')
            return

        nzs = oseg.segmentation.nonzero()
        nn = nzs[0].shape[0]
        if nn > 0:
            voxelvolume_mm3 = np.prod(oseg.voxelsize_mm)
            tim = self.oseg.processing_time

            if self.oseg.volume_unit == 'ml':
                import datetime
                timstr = str(datetime.timedelta(seconds=round(tim)))
                logger.debug('tim = ' + str(tim))
                aux = 'volume = %.2f [ml] , time = %s' %\
                      (nn * voxelvolume_mm3 / 1000, timstr)
            else:
                aux = 'volume = %.6e mm3' % (nn * voxelvolume_mm3, )
            self.setLabelText(self.text_seg_data, msg + aux)
            self.statusBar().showMessage('Ready')

        else:
            self.statusBar().showMessage('No segmentation!')

    def saveOut(self, event=None, filename=None):
        if self.oseg.segmentation is not None:
            self.statusBar().showMessage('Saving segmentation data...')
            QApplication.processEvents()

            # if filename is None:
            #     filename = \
            #         str(QFileDialog.getSaveFileName(self,
            #                                         'Save SEG file',
            #                                         filter='Files (*.seg)'))

            # if len(filename) > 0:

            #     outdata = {'data': self.dcm_3Ddata,
            #                'segdata': self.segmentation_data,
            #                'voxelsize_mm': self.voxel_sizemm,
            #                'offset_mm': self.dcm_offsetmm}

            #     if self.segmentation_seeds is not None:
            #         outdata['segseeds'] = self.segmentation_seeds

            #     savemat(filename, outdata, appendmat=False)

            # else:
            #     self.statusBar().showMessage('No output file specified!')

            self.oseg.save_outputs()
            self.statusBar().showMessage('Ready')

        else:
            self.statusBar().showMessage('No segmentation data!')

    def saveOutDcm(self, event=None, filename=None):
        if self.oseg.segmentation is not None:
            self.statusBar().showMessage('Saving segmentation data...')
            QApplication.processEvents()

            self.oseg.save_outputs_dcm()
            self.statusBar().showMessage('Ready')

        else:
            self.statusBar().showMessage('No segmentation data!')

    def btnVirtualResection(self):
        # mport vessel_cut

        data = {'data3d': self.oseg.data3d,
                'segmentation': self.oseg.segmentation,
                'slab': self.oseg.slab,
                'voxelsize_mm': self.oseg.voxelsize_mm
                }
        cut = virtual_resection.resection(data, None, use_old_editor=True)
        self.oseg.segmentation = cut['segmentation']
        self.oseg.slab = cut['slab']

        # rint

        voxelvolume_mm3 = np.prod(self.oseg.voxelsize_mm)
        v1 = np.sum(cut['segmentation'] == self.oseg.slab['liver'])
        v2 = np.sum(cut['segmentation'] == self.oseg.slab['resected_liver'])
        v1 = (v1) * voxelvolume_mm3
        v2 = (v2) * voxelvolume_mm3
        aux = "volume = %.4g l, %.4g/%.4g (%.3g/%.3g %% )" % (
            (v1 + v2) * 1e-6,
            (v1) * 1e-6,
            (v2) * 1e-6,
            100 * v1 / (v1 + v2),
            100 * v2 / (v1 + v2)
        )
        self.setLabelText(self.text_seg_data, aux)

        # rom PyQt4.QtCore import pyqtRemoveInputHook
        # yqtRemoveInputHook()
        # mport ipdb; ipdb.set_trace() # BREAKPOINT
        # ass

    def btnLesionLocalization(self):
        self.oseg.lesionsLocalization()

    def btnVesselSegmentation(self):
        """
        Function calls segmentation.vesselSegmentation function.
        """

        outputSegmentation = segmentation.vesselSegmentation(
            self.oseg.data3d,
            self.oseg.segmentation,
            threshold=-1,
            inputSigma=0.15,
            dilationIterations=2,
            nObj=1,
            biggestObjects=False,
            interactivity=True,
            binaryClosingIterations=2,
            binaryOpeningIterations=0)
        # rint outputSegmentation
        # rint np.unique(outputSegmentation)
        # rint self.oseg.slab
        slab = {'porta': 2}
        slab.update(self.oseg.slab)
        # rom PyQt4.QtCore import pyqtRemoveInputHook
        # yqtRemoveInputHook()
        # mport ipdb; ipdb.set_trace() # BREAKPOINT
        self.oseg.slab = slab
        self.oseg.segmentation[outputSegmentation == 1] = slab['porta']

    def view3D(self):
        # rom seg2mesh import gen_mesh_from_voxels, mesh2vtk, smooth_mesh
        # rom viewer import QVTKViewer
        oseg = self.oseg
        if oseg.segmentation is not None:
            pts, els, et = gen_mesh_from_voxels(oseg.segmentation,
                                                oseg.voxelsize_mm,
                                                etype='q', mtype='s')
            pts = smooth_mesh(pts, els, et,
                              n_iter=10)
            vtkdata = mesh2vtk(pts, els, et)
            view = QVTKViewer(vtk_data=vtkdata)
            view.exec_()

        else:
            self.statusBar().showMessage('No segmentation data!')
