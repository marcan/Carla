#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Carla settings code
# Copyright (C) 2011-2019 Filipe Coelho <falktx@falktx.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the doc/GPL.txt file.

# ------------------------------------------------------------------------------------------------------------
# Imports (Global)

from PyQt5.QtCore import pyqtSlot, QByteArray, QDir, QSettings
from PyQt5.QtGui import QColor, QCursor, QPainter, QPainterPath
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QFrame, QInputDialog, QLineEdit, QMenu, QVBoxLayout, QWidget

# ------------------------------------------------------------------------------------------------------------
# Imports (Custom)

import ui_carla_settings
import ui_carla_settings_driver

from carla_shared import *
from patchcanvas.theme import *

# ------------------------------------------------------------------------------------------------------------
# ...

BUFFER_SIZE_LIST = (16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192)
SAMPLE_RATE_LIST = (22050, 32000, 44100, 48000, 88200, 96000, 176400, 192000)

# ------------------------------------------------------------------------------------------------------------
# Driver Settings

class DriverSettingsW(QDialog):
    AUTOMATIC_OPTION = "(Auto)"

    def __init__(self, parent, host, driverIndex, driverName):
        QDialog.__init__(self, parent)
        self.host = host
        self.ui = ui_carla_settings_driver.Ui_DriverSettingsW()
        self.ui.setupUi(self)

        if False:
            # kdevelop likes this :)
            host = CarlaHostNull()
            self.host = host

        # ----------------------------------------------------------------------------------------------------
        # Internal stuff

        self.fDriverIndex = driverIndex
        self.fDriverName  = driverName
        self.fDeviceNames = host.get_engine_driver_device_names(driverIndex)

        self.fBufferSizes = BUFFER_SIZE_LIST
        self.fSampleRates = SAMPLE_RATE_LIST

        # ----------------------------------------------------------------------------------------------------
        # Set-up GUI

        for name in self.fDeviceNames:
            self.ui.cb_device.addItem(name)

        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # ----------------------------------------------------------------------------------------------------
        # Load settings

        self.loadSettings()

        # ----------------------------------------------------------------------------------------------------
        # Set-up connections

        self.accepted.connect(self.slot_saveSettings)
        self.ui.cb_device.currentIndexChanged.connect(self.slot_updateDeviceInfo)

        # ----------------------------------------------------------------------------------------------------

    def loadSettings(self):
        settings = QSettings("falkTX", "Carla2")

        audioDevice       = settings.value("%s%s/Device"       % (CARLA_KEY_ENGINE_DRIVER_PREFIX, self.fDriverName), "",                                type=str)
        audioBufferSize   = settings.value("%s%s/BufferSize"   % (CARLA_KEY_ENGINE_DRIVER_PREFIX, self.fDriverName), CARLA_DEFAULT_AUDIO_BUFFER_SIZE,   type=int)
        audioSampleRate   = settings.value("%s%s/SampleRate"   % (CARLA_KEY_ENGINE_DRIVER_PREFIX, self.fDriverName), CARLA_DEFAULT_AUDIO_SAMPLE_RATE,   type=int)
        audioTripleBuffer = settings.value("%s%s/TripleBuffer" % (CARLA_KEY_ENGINE_DRIVER_PREFIX, self.fDriverName), CARLA_DEFAULT_AUDIO_TRIPLE_BUFFER, type=bool)

        if audioDevice and audioDevice in self.fDeviceNames:
            self.ui.cb_device.setCurrentIndex(self.fDeviceNames.index(audioDevice))
        else:
            self.ui.cb_device.setCurrentIndex(-1)

        # fill combo-boxes first
        self.slot_updateDeviceInfo()

        if audioBufferSize and audioBufferSize in self.fBufferSizes:
            self.ui.cb_buffersize.setCurrentIndex(self.fBufferSizes.index(audioBufferSize))
        elif self.fBufferSizes == BUFFER_SIZE_LIST:
            self.ui.cb_buffersize.setCurrentIndex(BUFFER_SIZE_LIST.index(CARLA_DEFAULT_AUDIO_BUFFER_SIZE))
        else:
            self.ui.cb_buffersize.setCurrentIndex(len(self.fBufferSizes)/2)

        if audioSampleRate and audioSampleRate in self.fSampleRates:
            self.ui.cb_samplerate.setCurrentIndex(self.fSampleRates.index(audioSampleRate))
        elif self.fSampleRates == SAMPLE_RATE_LIST:
            self.ui.cb_samplerate.setCurrentIndex(SAMPLE_RATE_LIST.index(CARLA_DEFAULT_AUDIO_SAMPLE_RATE))
        else:
            self.ui.cb_samplerate.setCurrentIndex(len(self.fSampleRates)/2)

        self.ui.cb_triple_buffer.setChecked(audioTripleBuffer and self.ui.cb_triple_buffer.isEnabled())

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_saveSettings(self):
        settings = QSettings("falkTX", "Carla2")

        bufferSize = self.ui.cb_buffersize.currentText()
        sampleRate = self.ui.cb_samplerate.currentText()

        if bufferSize == self.AUTOMATIC_OPTION:
            bufferSize = "0"
        if sampleRate == self.AUTOMATIC_OPTION:
            sampleRate = "0"

        settings.setValue("%s%s/Device"       % (CARLA_KEY_ENGINE_DRIVER_PREFIX, self.fDriverName), self.ui.cb_device.currentText())
        settings.setValue("%s%s/BufferSize"   % (CARLA_KEY_ENGINE_DRIVER_PREFIX, self.fDriverName), bufferSize)
        settings.setValue("%s%s/SampleRate"   % (CARLA_KEY_ENGINE_DRIVER_PREFIX, self.fDriverName), sampleRate)
        settings.setValue("%s%s/TripleBuffer" % (CARLA_KEY_ENGINE_DRIVER_PREFIX, self.fDriverName), self.ui.cb_triple_buffer.isChecked())

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_updateDeviceInfo(self):
        deviceName = self.ui.cb_device.currentText()

        oldBufferSize = self.ui.cb_buffersize.currentText()
        oldSampleRate = self.ui.cb_samplerate.currentText()

        self.ui.cb_buffersize.clear()
        self.ui.cb_samplerate.clear()

        driverDeviceInfo  = self.host.get_engine_driver_device_info(self.fDriverIndex, deviceName)
        driverDeviceHints = driverDeviceInfo['hints']
        self.fBufferSizes = driverDeviceInfo['bufferSizes']
        self.fSampleRates = driverDeviceInfo['sampleRates']

        if driverDeviceHints & ENGINE_DRIVER_DEVICE_CAN_TRIPLE_BUFFER:
            self.ui.cb_triple_buffer.setEnabled(True)
        else:
            self.ui.cb_triple_buffer.setEnabled(False)

        if len(self.fBufferSizes) > 0:
            for bsize in self.fBufferSizes:
                sbsize = str(bsize)
                self.ui.cb_buffersize.addItem(sbsize)

                if oldBufferSize == sbsize:
                    self.ui.cb_buffersize.setCurrentIndex(self.ui.cb_buffersize.count()-1)

        else:
            self.ui.cb_buffersize.addItem(self.AUTOMATIC_OPTION)
            self.ui.cb_buffersize.setCurrentIndex(0)

        if len(self.fSampleRates) > 0:
            for srate in self.fSampleRates:
                ssrate = str(int(srate))
                self.ui.cb_samplerate.addItem(ssrate)

                if oldSampleRate == ssrate:
                    self.ui.cb_samplerate.setCurrentIndex(self.ui.cb_samplerate.count()-1)

        else:
            self.ui.cb_samplerate.addItem(self.AUTOMATIC_OPTION)
            self.ui.cb_samplerate.setCurrentIndex(0)

    # --------------------------------------------------------------------------------------------------------

    def done(self, r):
        QDialog.done(self, r)
        self.close()

# ------------------------------------------------------------------------------------------------------------
# Settings Dialog

class CarlaSettingsW(QDialog):
    # Tab indexes
    TAB_INDEX_MAIN         = 0
    TAB_INDEX_CANVAS       = 1
    TAB_INDEX_ENGINE       = 2
    TAB_INDEX_OSC          = 3
    TAB_INDEX_PATHS        = 4
    TAB_INDEX_WINE         = 5
    TAB_INDEX_EXPERIMENTAL = 6
    TAB_INDEX_NONE         = 7

    # Path indexes
    PATH_INDEX_LADSPA = 0
    PATH_INDEX_DSSI   = 1
    PATH_INDEX_LV2    = 2
    PATH_INDEX_VST2   = 3
    PATH_INDEX_VST3   = 4
    PATH_INDEX_SF2    = 5
    PATH_INDEX_SFZ    = 6

    # Single and Multiple client mode is only for JACK,
    # but we still want to match QComboBox index to backend defines,
    # so add +2 pos padding if driverName != "JACK".
    PROCESS_MODE_NON_JACK_PADDING = 2

    # --------------------------------------------------------------------------------------------------------

    def __init__(self, parent, host, hasCanvas, hasCanvasGL):
        QDialog.__init__(self, parent)
        self.host = host
        self.ui = ui_carla_settings.Ui_CarlaSettingsW()
        self.ui.setupUi(self)

        if False:
            # kdevelop likes this :)
            host = CarlaHostNull()
            self.host = host

        # ----------------------------------------------------------------------------------------------------
        # Set-up GUI

        self.ui.lw_page.setFixedWidth(48 + 6*3 + self.ui.lw_page.fontMetrics().width("   Experimental   "))

        for i in range(host.get_engine_driver_count()):
            self.ui.cb_engine_audio_driver.addItem(host.get_engine_driver_name(i))

        for i in range(Theme.THEME_MAX):
            self.ui.cb_canvas_theme.addItem(getThemeName(i))

        if MACOS:
            self.ui.group_main_theme.setEnabled(False)
            self.ui.group_main_theme.setVisible(False)

        if WINDOWS or host.isControl:
            self.ui.ch_main_show_logs.setEnabled(False)
            self.ui.ch_main_show_logs.setVisible(False)

        if host.isControl:
            self.ui.lw_page.hideRow(self.TAB_INDEX_ENGINE)
            self.ui.lw_page.hideRow(self.TAB_INDEX_PATHS)
            self.ui.ch_exp_export_lv2.hide()
            self.ui.group_experimental_engine.hide()

        elif not hasCanvas:
            self.ui.lw_page.hideRow(self.TAB_INDEX_CANVAS)

        elif not hasCanvasGL:
            self.ui.cb_canvas_use_opengl.setEnabled(False)
            self.ui.cb_canvas_render_hq_aa.setEnabled(False)

        if host.isPlugin:
            self.ui.cb_engine_audio_driver.setEnabled(False)

        if host.audioDriverForced is not None:
            self.ui.cb_engine_audio_driver.setEnabled(False)
            self.ui.tb_engine_driver_config.setEnabled(False)

        if host.processModeForced:
            self.ui.cb_engine_process_mode_jack.setEnabled(False)
            self.ui.cb_engine_process_mode_other.setEnabled(False)

            if self.host.processMode == ENGINE_PROCESS_MODE_CONTINUOUS_RACK:
                self.ui.ch_engine_force_stereo.setEnabled(False)

        if host.isControl or host.isPlugin:
            self.ui.ch_main_confirm_exit.hide()
            self.ui.ch_exp_load_lib_global.hide()
            self.ui.lw_page.hideRow(self.TAB_INDEX_OSC)
            self.ui.lw_page.hideRow(self.TAB_INDEX_WINE)

        if not LINUX:
            self.ui.ch_exp_wine_bridges.setVisible(False)
            self.ui.ch_exp_jack_apps.setVisible(False)
            self.ui.ch_exp_prevent_bad_behaviour.setVisible(False)
            self.ui.lw_page.hideRow(self.TAB_INDEX_WINE)

        if not MACOS:
            self.ui.label_engine_ui_bridges_mac_note.setVisible(False)

        # FIXME, not implemented yet
        self.ui.ch_engine_uis_always_on_top.hide()

        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # ----------------------------------------------------------------------------------------------------
        # Load settings

        self.loadSettings()

        # ----------------------------------------------------------------------------------------------------
        # Set-up connections

        self.accepted.connect(self.slot_saveSettings)
        self.ui.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.slot_resetSettings)

        self.ui.b_main_proj_folder_open.clicked.connect(self.slot_getAndSetProjectPath)

        self.ui.cb_engine_audio_driver.currentIndexChanged.connect(self.slot_engineAudioDriverChanged)
        self.ui.tb_engine_driver_config.clicked.connect(self.slot_showAudioDriverSettings)

        self.ui.b_paths_add.clicked.connect(self.slot_addPluginPath)
        self.ui.b_paths_remove.clicked.connect(self.slot_removePluginPath)
        self.ui.b_paths_change.clicked.connect(self.slot_changePluginPath)
        self.ui.cb_paths.currentIndexChanged.connect(self.slot_pluginPathTabChanged)
        self.ui.lw_ladspa.currentRowChanged.connect(self.slot_pluginPathRowChanged)
        self.ui.lw_dssi.currentRowChanged.connect(self.slot_pluginPathRowChanged)
        self.ui.lw_lv2.currentRowChanged.connect(self.slot_pluginPathRowChanged)
        self.ui.lw_vst.currentRowChanged.connect(self.slot_pluginPathRowChanged)
        self.ui.lw_vst3.currentRowChanged.connect(self.slot_pluginPathRowChanged)
        self.ui.lw_sf2.currentRowChanged.connect(self.slot_pluginPathRowChanged)
        self.ui.lw_sfz.currentRowChanged.connect(self.slot_pluginPathRowChanged)

        self.ui.ch_main_experimental.toggled.connect(self.slot_enableExperimental)
        self.ui.ch_exp_wine_bridges.toggled.connect(self.slot_enableWineBridges)
        self.ui.cb_exp_plugin_bridges.toggled.connect(self.slot_pluginBridgesToggled)
        self.ui.cb_canvas_eyecandy.toggled.connect(self.slot_canvasEyeCandyToggled)
        self.ui.cb_canvas_fancy_eyecandy.toggled.connect(self.slot_canvasFancyEyeCandyToggled)
        self.ui.cb_canvas_use_opengl.toggled.connect(self.slot_canvasOpenGLToggled)

        # ----------------------------------------------------------------------------------------------------
        # Post-connect setup

        self.ui.lw_ladspa.setCurrentRow(0)
        self.ui.lw_dssi.setCurrentRow(0)
        self.ui.lw_lv2.setCurrentRow(0)
        self.ui.lw_vst.setCurrentRow(0)
        self.ui.lw_vst3.setCurrentRow(0)
        self.ui.lw_sf2.setCurrentRow(0)
        self.ui.lw_sfz.setCurrentRow(0)

        self.ui.lw_page.setCurrentCell(0, 0)

        self.adjustSize()

    # --------------------------------------------------------------------------------------------------------

    def loadSettings(self):
        settings = QSettings()

        # ----------------------------------------------------------------------------------------------------
        # Main

        self.ui.ch_main_show_logs.setChecked(self.host.showLogs)
        self.ui.ch_engine_uis_always_on_top.setChecked(self.host.uisAlwaysOnTop)

        self.ui.le_main_proj_folder.setText(settings.value(CARLA_KEY_MAIN_PROJECT_FOLDER, CARLA_DEFAULT_MAIN_PROJECT_FOLDER, type=str))
        self.ui.ch_main_theme_pro.setChecked(settings.value(CARLA_KEY_MAIN_USE_PRO_THEME, CARLA_DEFAULT_MAIN_USE_PRO_THEME, type=bool) and self.ui.group_main_theme.isEnabled())
        self.ui.cb_main_theme_color.setCurrentIndex(self.ui.cb_main_theme_color.findText(settings.value(CARLA_KEY_MAIN_PRO_THEME_COLOR, CARLA_DEFAULT_MAIN_PRO_THEME_COLOR, type=str)))
        self.ui.sb_main_refresh_interval.setValue(settings.value(CARLA_KEY_MAIN_REFRESH_INTERVAL, CARLA_DEFAULT_MAIN_REFRESH_INTERVAL, type=int))
        self.ui.ch_main_confirm_exit.setChecked(settings.value(CARLA_KEY_MAIN_CONFIRM_EXIT, CARLA_DEFAULT_MAIN_CONFIRM_EXIT, type=bool))

        # ----------------------------------------------------------------------------------------------------
        # Canvas

        self.ui.cb_canvas_theme.setCurrentIndex(self.ui.cb_canvas_theme.findText(settings.value(CARLA_KEY_CANVAS_THEME, CARLA_DEFAULT_CANVAS_THEME, type=str)))
        self.ui.cb_canvas_size.setCurrentIndex(self.ui.cb_canvas_size.findText(settings.value(CARLA_KEY_CANVAS_SIZE, CARLA_DEFAULT_CANVAS_SIZE, type=str)))
        self.ui.cb_canvas_bezier_lines.setChecked(settings.value(CARLA_KEY_CANVAS_USE_BEZIER_LINES, CARLA_DEFAULT_CANVAS_USE_BEZIER_LINES, type=bool))
        self.ui.cb_canvas_hide_groups.setChecked(settings.value(CARLA_KEY_CANVAS_AUTO_HIDE_GROUPS, CARLA_DEFAULT_CANVAS_AUTO_HIDE_GROUPS, type=bool))
        self.ui.cb_canvas_auto_select.setChecked(settings.value(CARLA_KEY_CANVAS_AUTO_SELECT_ITEMS, CARLA_DEFAULT_CANVAS_AUTO_SELECT_ITEMS, type=bool))
        self.ui.cb_canvas_eyecandy.setChecked(settings.value(CARLA_KEY_CANVAS_EYE_CANDY, CARLA_DEFAULT_CANVAS_EYE_CANDY, type=bool))
        self.ui.cb_canvas_fancy_eyecandy.setChecked(settings.value(CARLA_KEY_CANVAS_FANCY_EYE_CANDY, CARLA_DEFAULT_CANVAS_FANCY_EYE_CANDY, type=bool))
        self.ui.cb_canvas_use_opengl.setChecked(settings.value(CARLA_KEY_CANVAS_USE_OPENGL, CARLA_DEFAULT_CANVAS_USE_OPENGL, type=bool) and self.ui.cb_canvas_use_opengl.isEnabled())
        self.ui.cb_canvas_render_aa.setCheckState(settings.value(CARLA_KEY_CANVAS_ANTIALIASING, CARLA_DEFAULT_CANVAS_ANTIALIASING, type=int))
        self.ui.cb_canvas_render_hq_aa.setChecked(settings.value(CARLA_KEY_CANVAS_HQ_ANTIALIASING, CARLA_DEFAULT_CANVAS_HQ_ANTIALIASING, type=bool) and self.ui.cb_canvas_render_hq_aa.isEnabled())

        # ----------------------------------------------------------------------------------------------------

        settings = QSettings("falkTX", "Carla2")

        # ----------------------------------------------------------------------------------------------------
        # Main

        self.ui.ch_main_experimental.setChecked(self.host.experimental)

        if not self.host.experimental:
            self.ui.lw_page.hideRow(self.TAB_INDEX_EXPERIMENTAL)
            self.ui.lw_page.hideRow(self.TAB_INDEX_WINE)

        elif not self.host.showWineBridges:
            self.ui.lw_page.hideRow(self.TAB_INDEX_WINE)

        # ----------------------------------------------------------------------------------------------------
        # Engine

        if self.host.isPlugin:
            audioDriver = "Plugin"
            self.ui.cb_engine_audio_driver.setCurrentIndex(0)
        elif self.host.audioDriverForced:
            audioDriver = self.host.audioDriverForced
            self.ui.cb_engine_audio_driver.setCurrentIndex(0)
        else:
            audioDriver = settings.value(CARLA_KEY_ENGINE_AUDIO_DRIVER, CARLA_DEFAULT_AUDIO_DRIVER, type=str)

            for i in range(self.ui.cb_engine_audio_driver.count()):
                if self.ui.cb_engine_audio_driver.itemText(i) == audioDriver:
                    self.ui.cb_engine_audio_driver.setCurrentIndex(i)
                    break
            else:
                self.ui.cb_engine_audio_driver.setCurrentIndex(-1)

        if audioDriver == "JACK":
            self.ui.sw_engine_process_mode.setCurrentIndex(0)
        else:
            self.ui.sw_engine_process_mode.setCurrentIndex(1)

        self.ui.tb_engine_driver_config.setEnabled(self.host.audioDriverForced is None and not self.host.isPlugin)

        self.ui.cb_engine_process_mode_jack.setCurrentIndex(self.host.nextProcessMode)

        if self.host.nextProcessMode >= self.PROCESS_MODE_NON_JACK_PADDING:
            self.ui.cb_engine_process_mode_other.setCurrentIndex(self.host.nextProcessMode-self.PROCESS_MODE_NON_JACK_PADDING)
        else:
            self.ui.cb_engine_process_mode_other.setCurrentIndex(0)

        self.ui.sb_engine_max_params.setValue(self.host.maxParameters)
        self.ui.ch_engine_manage_uis.setChecked(self.host.manageUIs)
        self.ui.ch_engine_prefer_ui_bridges.setChecked(self.host.preferUIBridges)
        self.ui.sb_engine_ui_bridges_timeout.setValue(self.host.uiBridgesTimeout)
        self.ui.ch_engine_force_stereo.setChecked(self.host.forceStereo or not self.ui.ch_engine_force_stereo.isEnabled())
        self.ui.ch_engine_prefer_plugin_bridges.setChecked(self.host.preferPluginBridges)
        self.ui.ch_exp_export_lv2.setChecked(self.host.exportLV2)
        self.ui.cb_exp_plugin_bridges.setChecked(self.host.showPluginBridges)
        self.ui.ch_exp_wine_bridges.setChecked(self.host.showWineBridges)

        # ----------------------------------------------------------------------------------------------------
        # OSC

        self.ui.ch_osc_enable.setChecked(settings.value(CARLA_KEY_OSC_ENABLED,
                                                        CARLA_DEFAULT_OSC_ENABLED,
                                                        type=bool))

        self.ui.group_osc_tcp_port.setChecked(settings.value(CARLA_KEY_OSC_TCP_PORT_ENABLED,
                                                             CARLA_DEFAULT_OSC_TCP_PORT_ENABLED,
                                                             type=bool))

        self.ui.group_osc_udp_port.setChecked(settings.value(CARLA_KEY_OSC_UDP_PORT_ENABLED,
                                                             CARLA_DEFAULT_OSC_UDP_PORT_ENABLED,
                                                             type=bool))

        self.ui.sb_osc_tcp_port_number.setValue(settings.value(CARLA_KEY_OSC_TCP_PORT_NUMBER,
                                                               CARLA_DEFAULT_OSC_TCP_PORT_NUMBER,
                                                               type=int))

        self.ui.sb_osc_udp_port_number.setValue(settings.value(CARLA_KEY_OSC_UDP_PORT_NUMBER,
                                                               CARLA_DEFAULT_OSC_UDP_PORT_NUMBER,
                                                               type=int))

        if settings.value(CARLA_KEY_OSC_TCP_PORT_RANDOM, CARLA_DEFAULT_OSC_TCP_PORT_RANDOM, type=bool):
            self.ui.rb_osc_tcp_port_specific.setChecked(False)
            self.ui.rb_osc_tcp_port_random.setChecked(True)
        else:
            self.ui.rb_osc_tcp_port_random.setChecked(False)
            self.ui.rb_osc_tcp_port_specific.setChecked(True)

        if settings.value(CARLA_KEY_OSC_UDP_PORT_RANDOM, CARLA_DEFAULT_OSC_UDP_PORT_RANDOM, type=bool):
            self.ui.rb_osc_udp_port_specific.setChecked(False)
            self.ui.rb_osc_udp_port_random.setChecked(True)
        else:
            self.ui.rb_osc_udp_port_random.setChecked(False)
            self.ui.rb_osc_udp_port_specific.setChecked(True)

        # ----------------------------------------------------------------------------------------------------
        # Paths

        ladspas = toList(settings.value(CARLA_KEY_PATHS_LADSPA, CARLA_DEFAULT_LADSPA_PATH))
        dssis   = toList(settings.value(CARLA_KEY_PATHS_DSSI,   CARLA_DEFAULT_DSSI_PATH))
        lv2s    = toList(settings.value(CARLA_KEY_PATHS_LV2,    CARLA_DEFAULT_LV2_PATH))
        vst2s   = toList(settings.value(CARLA_KEY_PATHS_VST2,   CARLA_DEFAULT_VST2_PATH))
        vst3s   = toList(settings.value(CARLA_KEY_PATHS_VST3,   CARLA_DEFAULT_VST3_PATH))
        sf2s    = toList(settings.value(CARLA_KEY_PATHS_SF2,    CARLA_DEFAULT_SF2_PATH))
        sfzs    = toList(settings.value(CARLA_KEY_PATHS_SFZ,    CARLA_DEFAULT_SFZ_PATH))

        ladspas.sort()
        dssis.sort()
        lv2s.sort()
        vst2s.sort()
        vst3s.sort()
        sf2s.sort()
        sfzs.sort()

        for ladspa in ladspas:
            if not ladspa: continue
            self.ui.lw_ladspa.addItem(ladspa)

        for dssi in dssis:
            if not dssi: continue
            self.ui.lw_dssi.addItem(dssi)

        for lv2 in lv2s:
            if not lv2: continue
            self.ui.lw_lv2.addItem(lv2)

        for vst2 in vst2s:
            if not vst2: continue
            self.ui.lw_vst.addItem(vst2)

        for vst3 in vst3s:
            if not vst3: continue
            self.ui.lw_vst3.addItem(vst3)

        for sf2 in sf2s:
            if not sf2: continue
            self.ui.lw_sf2.addItem(sf2)

        for sfz in sfzs:
            if not sfz: continue
            self.ui.lw_sfz.addItem(sfz)

        # ----------------------------------------------------------------------------------------------------
        # Wine

        self.ui.le_wine_exec.setText(settings.value(CARLA_KEY_WINE_EXECUTABLE,
                                                    CARLA_DEFAULT_WINE_EXECUTABLE,
                                                    type=str))

        self.ui.cb_wine_prefix_detect.setChecked(settings.value(CARLA_KEY_WINE_AUTO_PREFIX,
                                                                CARLA_DEFAULT_WINE_AUTO_PREFIX,
                                                                 type=bool))

        self.ui.le_wine_prefix_fallback.setText(settings.value(CARLA_KEY_WINE_FALLBACK_PREFIX,
                                                               CARLA_DEFAULT_WINE_FALLBACK_PREFIX,
                                                               type=str))

        self.ui.group_wine_realtime.setChecked(settings.value(CARLA_KEY_WINE_RT_PRIO_ENABLED,
                                                              CARLA_DEFAULT_WINE_RT_PRIO_ENABLED,
                                                              type=bool))

        self.ui.sb_wine_base_prio.setValue(settings.value(CARLA_KEY_WINE_BASE_RT_PRIO,
                                                          CARLA_DEFAULT_WINE_BASE_RT_PRIO,
                                                          type=int))

        self.ui.sb_wine_server_prio.setValue(settings.value(CARLA_KEY_WINE_SERVER_RT_PRIO,
                                                            CARLA_DEFAULT_WINE_SERVER_RT_PRIO,
                                                            type=int))

        # ----------------------------------------------------------------------------------------------------
        # Experimental

        self.ui.ch_exp_jack_apps.setChecked(settings.value(CARLA_KEY_EXPERIMENTAL_JACK_APPS,
                                                           CARLA_DEFAULT_EXPERIMENTAL_JACK_APPS,
                                                           type=bool))

        self.ui.ch_exp_export_lv2.setChecked(settings.value(CARLA_KEY_EXPERIMENTAL_EXPORT_LV2,
                                                            CARLA_DEFAULT_EXPERIMENTAL_LV2_EXPORT,
                                                            type=bool))

        self.ui.ch_exp_load_lib_global.setChecked(settings.value(CARLA_KEY_EXPERIMENTAL_LOAD_LIB_GLOBAL,
                                                                 CARLA_DEFAULT_EXPERIMENTAL_LOAD_LIB_GLOBAL,
                                                                 type=bool))

        self.ui.ch_exp_prevent_bad_behaviour.setChecked(settings.value(CARLA_KEY_EXPERIMENTAL_PREVENT_BAD_BEHAVIOUR,
                                                                       CARLA_DEFAULT_EXPERIMENTAL_PREVENT_BAD_BEHAVIOUR,
                                                                       type=bool))

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_saveSettings(self):
        settings = QSettings()

        self.host.experimental = self.ui.ch_main_experimental.isChecked()

        if not self.host.experimental:
            self.resetExperimentalSettings()

        # ----------------------------------------------------------------------------------------------------
        # Main

        settings.setValue(CARLA_KEY_MAIN_PROJECT_FOLDER,   self.ui.le_main_proj_folder.text())
        settings.setValue(CARLA_KEY_MAIN_CONFIRM_EXIT,     self.ui.ch_main_confirm_exit.isChecked())
        settings.setValue(CARLA_KEY_MAIN_USE_PRO_THEME,    self.ui.ch_main_theme_pro.isChecked())
        settings.setValue(CARLA_KEY_MAIN_PRO_THEME_COLOR,  self.ui.cb_main_theme_color.currentText())
        settings.setValue(CARLA_KEY_MAIN_REFRESH_INTERVAL, self.ui.sb_main_refresh_interval.value())

        # ----------------------------------------------------------------------------------------------------
        # Canvas

        settings.setValue(CARLA_KEY_CANVAS_THEME,             self.ui.cb_canvas_theme.currentText())
        settings.setValue(CARLA_KEY_CANVAS_SIZE,              self.ui.cb_canvas_size.currentText())
        settings.setValue(CARLA_KEY_CANVAS_USE_BEZIER_LINES,  self.ui.cb_canvas_bezier_lines.isChecked())
        settings.setValue(CARLA_KEY_CANVAS_AUTO_HIDE_GROUPS,  self.ui.cb_canvas_hide_groups.isChecked())
        settings.setValue(CARLA_KEY_CANVAS_AUTO_SELECT_ITEMS, self.ui.cb_canvas_auto_select.isChecked())
        settings.setValue(CARLA_KEY_CANVAS_EYE_CANDY,         self.ui.cb_canvas_eyecandy.isChecked())
        settings.setValue(CARLA_KEY_CANVAS_FANCY_EYE_CANDY,   self.ui.cb_canvas_fancy_eyecandy.isChecked())
        settings.setValue(CARLA_KEY_CANVAS_USE_OPENGL,        self.ui.cb_canvas_use_opengl.isChecked())
        settings.setValue(CARLA_KEY_CANVAS_HQ_ANTIALIASING,   self.ui.cb_canvas_render_hq_aa.isChecked())
        settings.setValue(CARLA_KEY_CANVAS_ANTIALIASING,      self.ui.cb_canvas_render_aa.checkState()) # 0, 1, 2 match their enum variants

        # ----------------------------------------------------------------------------------------------------

        settings = QSettings("falkTX", "Carla2")

        # ----------------------------------------------------------------------------------------------------
        # Main

        settings.setValue(CARLA_KEY_MAIN_EXPERIMENTAL, self.host.experimental)

        # ----------------------------------------------------------------------------------------------------
        # Engine

        audioDriver = self.ui.cb_engine_audio_driver.currentText()

        if audioDriver and self.host.audioDriverForced is None and not self.host.isPlugin:
            settings.setValue(CARLA_KEY_ENGINE_AUDIO_DRIVER, audioDriver)

        if not self.host.processModeForced:
            # engine sends callback if processMode really changes
            if audioDriver == "JACK":
                self.host.nextProcessMode = self.ui.cb_engine_process_mode_jack.currentIndex()
            else:
                self.host.nextProcessMode = self.ui.cb_engine_process_mode_other.currentIndex() + self.PROCESS_MODE_NON_JACK_PADDING

            settings.setValue(CARLA_KEY_ENGINE_PROCESS_MODE, self.host.nextProcessMode)

        self.host.exportLV2           = self.ui.ch_exp_export_lv2.isChecked()
        self.host.forceStereo         = self.ui.ch_engine_force_stereo.isChecked()
        self.host.maxParameters       = self.ui.sb_engine_max_params.value()
        self.host.manageUIs           = self.ui.ch_engine_manage_uis.isChecked()
        self.host.preferPluginBridges = self.ui.ch_engine_prefer_plugin_bridges.isChecked()
        self.host.preferUIBridges     = self.ui.ch_engine_prefer_ui_bridges.isChecked()
        self.host.showLogs            = self.ui.ch_main_show_logs.isChecked()
        self.host.showPluginBridges   = self.ui.cb_exp_plugin_bridges.isChecked()
        self.host.showWineBridges     = self.ui.ch_exp_wine_bridges.isChecked()
        self.host.uiBridgesTimeout    = self.ui.sb_engine_ui_bridges_timeout.value()
        self.host.uisAlwaysOnTop      = self.ui.ch_engine_uis_always_on_top.isChecked()

        if self.ui.ch_engine_force_stereo.isEnabled():
            settings.setValue(CARLA_KEY_ENGINE_FORCE_STEREO,      self.host.forceStereo)

        settings.setValue(CARLA_KEY_MAIN_SHOW_LOGS,               self.host.showLogs)
        settings.setValue(CARLA_KEY_ENGINE_MAX_PARAMETERS,        self.host.maxParameters)
        settings.setValue(CARLA_KEY_ENGINE_MANAGE_UIS,            self.host.manageUIs)
        settings.setValue(CARLA_KEY_ENGINE_PREFER_PLUGIN_BRIDGES, self.host.preferPluginBridges)
        settings.setValue(CARLA_KEY_ENGINE_PREFER_UI_BRIDGES,     self.host.preferUIBridges)
        settings.setValue(CARLA_KEY_ENGINE_UI_BRIDGES_TIMEOUT,    self.host.uiBridgesTimeout)
        settings.setValue(CARLA_KEY_ENGINE_UIS_ALWAYS_ON_TOP,     self.host.uisAlwaysOnTop)
        settings.setValue(CARLA_KEY_EXPERIMENTAL_EXPORT_LV2,      self.host.exportLV2)
        settings.setValue(CARLA_KEY_EXPERIMENTAL_PLUGIN_BRIDGES,  self.host.showPluginBridges)
        settings.setValue(CARLA_KEY_EXPERIMENTAL_WINE_BRIDGES,    self.host.showWineBridges)

        # ----------------------------------------------------------------------------------------------------
        # OSC

        settings.setValue(CARLA_KEY_OSC_ENABLED,          self.ui.ch_osc_enable.isChecked())
        settings.setValue(CARLA_KEY_OSC_TCP_PORT_ENABLED, self.ui.group_osc_tcp_port.isChecked())
        settings.setValue(CARLA_KEY_OSC_UDP_PORT_ENABLED, self.ui.group_osc_udp_port.isChecked())
        settings.setValue(CARLA_KEY_OSC_TCP_PORT_RANDOM,  self.ui.rb_osc_tcp_port_random.isChecked())
        settings.setValue(CARLA_KEY_OSC_UDP_PORT_RANDOM,  self.ui.rb_osc_udp_port_random.isChecked())
        settings.setValue(CARLA_KEY_OSC_TCP_PORT_NUMBER,  self.ui.sb_osc_tcp_port_number.value())
        settings.setValue(CARLA_KEY_OSC_UDP_PORT_NUMBER,  self.ui.sb_osc_udp_port_number.value())

        # ----------------------------------------------------------------------------------------------------
        # Paths

        ladspas = []
        dssis   = []
        lv2s    = []
        vst2s   = []
        vst3s   = []
        sf2s    = []
        sfzs    = []

        for i in range(self.ui.lw_ladspa.count()):
            ladspas.append(self.ui.lw_ladspa.item(i).text())

        for i in range(self.ui.lw_dssi.count()):
            dssis.append(self.ui.lw_dssi.item(i).text())

        for i in range(self.ui.lw_lv2.count()):
            lv2s.append(self.ui.lw_lv2.item(i).text())

        for i in range(self.ui.lw_vst.count()):
            vst2s.append(self.ui.lw_vst.item(i).text())

        for i in range(self.ui.lw_vst3.count()):
            vst3s.append(self.ui.lw_vst3.item(i).text())

        for i in range(self.ui.lw_sf2.count()):
            sf2s.append(self.ui.lw_sf2.item(i).text())

        for i in range(self.ui.lw_sfz.count()):
            sfzs.append(self.ui.lw_sfz.item(i).text())

        self.host.set_engine_option(ENGINE_OPTION_PLUGIN_PATH, PLUGIN_LADSPA, splitter.join(ladspas))
        self.host.set_engine_option(ENGINE_OPTION_PLUGIN_PATH, PLUGIN_DSSI,   splitter.join(dssis))
        self.host.set_engine_option(ENGINE_OPTION_PLUGIN_PATH, PLUGIN_LV2,    splitter.join(lv2s))
        self.host.set_engine_option(ENGINE_OPTION_PLUGIN_PATH, PLUGIN_VST2,   splitter.join(vst2s))
        self.host.set_engine_option(ENGINE_OPTION_PLUGIN_PATH, PLUGIN_VST3,   splitter.join(vst3s))
        self.host.set_engine_option(ENGINE_OPTION_PLUGIN_PATH, PLUGIN_SF2,    splitter.join(sf2s))
        self.host.set_engine_option(ENGINE_OPTION_PLUGIN_PATH, PLUGIN_SFZ,    splitter.join(sfzs))

        settings.setValue(CARLA_KEY_PATHS_LADSPA, ladspas)
        settings.setValue(CARLA_KEY_PATHS_DSSI,   dssis)
        settings.setValue(CARLA_KEY_PATHS_LV2,    lv2s)
        settings.setValue(CARLA_KEY_PATHS_VST2,   vst2s)
        settings.setValue(CARLA_KEY_PATHS_VST3,   vst3s)
        settings.setValue(CARLA_KEY_PATHS_SF2,    sf2s)
        settings.setValue(CARLA_KEY_PATHS_SFZ,    sfzs)

        # ----------------------------------------------------------------------------------------------------
        # Wine

        settings.setValue(CARLA_KEY_WINE_EXECUTABLE, self.ui.le_wine_exec.text())
        settings.setValue(CARLA_KEY_WINE_AUTO_PREFIX, self.ui.cb_wine_prefix_detect.isChecked())
        settings.setValue(CARLA_KEY_WINE_FALLBACK_PREFIX, self.ui.le_wine_prefix_fallback.text())
        settings.setValue(CARLA_KEY_WINE_RT_PRIO_ENABLED, self.ui.group_wine_realtime.isChecked())
        settings.setValue(CARLA_KEY_WINE_BASE_RT_PRIO, self.ui.sb_wine_base_prio.value())
        settings.setValue(CARLA_KEY_WINE_SERVER_RT_PRIO, self.ui.sb_wine_server_prio.value())

        # ----------------------------------------------------------------------------------------------------
        # Experimental

        settings.setValue(CARLA_KEY_EXPERIMENTAL_JACK_APPS, self.ui.ch_exp_jack_apps.isChecked())
        settings.setValue(CARLA_KEY_EXPERIMENTAL_LOAD_LIB_GLOBAL, self.ui.ch_exp_load_lib_global.isChecked())
        settings.setValue(CARLA_KEY_EXPERIMENTAL_PREVENT_BAD_BEHAVIOUR, self.ui.ch_exp_prevent_bad_behaviour.isChecked())

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_resetSettings(self):
        currentRow = self.ui.lw_page.currentRow()

        # ----------------------------------------------------------------------------------------------------
        # Main

        if currentRow == self.TAB_INDEX_MAIN:
            self.ui.le_main_proj_folder.setText(CARLA_DEFAULT_MAIN_PROJECT_FOLDER)
            self.ui.ch_main_theme_pro.setChecked(CARLA_DEFAULT_MAIN_USE_PRO_THEME and self.ui.group_main_theme.isEnabled())
            self.ui.cb_main_theme_color.setCurrentIndex(self.ui.cb_main_theme_color.findText(CARLA_DEFAULT_MAIN_PRO_THEME_COLOR))
            self.ui.sb_main_refresh_interval.setValue(CARLA_DEFAULT_MAIN_REFRESH_INTERVAL)
            self.ui.ch_main_confirm_exit.setChecked(CARLA_DEFAULT_MAIN_CONFIRM_EXIT)
            self.ui.ch_main_show_logs.setChecked(CARLA_DEFAULT_MAIN_SHOW_LOGS)

        # ----------------------------------------------------------------------------------------------------
        # Canvas

        elif currentRow == self.TAB_INDEX_CANVAS:
            self.ui.cb_canvas_theme.setCurrentIndex(self.ui.cb_canvas_theme.findText(CARLA_DEFAULT_CANVAS_THEME))
            self.ui.cb_canvas_size.setCurrentIndex(self.ui.cb_canvas_size.findText(CARLA_DEFAULT_CANVAS_SIZE))
            self.ui.cb_canvas_bezier_lines.setChecked(CARLA_DEFAULT_CANVAS_USE_BEZIER_LINES)
            self.ui.cb_canvas_hide_groups.setChecked(CARLA_DEFAULT_CANVAS_AUTO_HIDE_GROUPS)
            self.ui.cb_canvas_auto_select.setChecked(CARLA_DEFAULT_CANVAS_AUTO_SELECT_ITEMS)
            self.ui.cb_canvas_eyecandy.setChecked(CARLA_DEFAULT_CANVAS_EYE_CANDY)
            self.ui.cb_canvas_render_aa.setCheckState(Qt.PartiallyChecked) # CARLA_DEFAULT_CANVAS_ANTIALIASING

        # ----------------------------------------------------------------------------------------------------
        # Engine

        elif currentRow == self.TAB_INDEX_ENGINE:
            if not self.host.isPlugin:
                self.ui.cb_engine_audio_driver.setCurrentIndex(0)

            if not self.host.processModeForced:
                if self.ui.cb_engine_audio_driver.currentText() == "JACK":
                    self.ui.cb_engine_process_mode_jack.setCurrentIndex(CARLA_DEFAULT_PROCESS_MODE)
                    self.ui.sw_engine_process_mode.setCurrentIndex(0) # show all modes
                else:
                    self.ui.cb_engine_process_mode_other.setCurrentIndex(CARLA_DEFAULT_PROCESS_MODE-self.PROCESS_MODE_NON_JACK_PADDING)
                    self.ui.sw_engine_process_mode.setCurrentIndex(1) # hide single+multi client modes

            self.ui.sb_engine_max_params.setValue(CARLA_DEFAULT_MAX_PARAMETERS)
            self.ui.ch_engine_uis_always_on_top.setChecked(CARLA_DEFAULT_UIS_ALWAYS_ON_TOP)
            self.ui.ch_engine_prefer_ui_bridges.setChecked(CARLA_DEFAULT_PREFER_UI_BRIDGES)
            self.ui.sb_engine_ui_bridges_timeout.setValue(CARLA_DEFAULT_UI_BRIDGES_TIMEOUT)
            self.ui.ch_engine_manage_uis.setChecked(CARLA_DEFAULT_MANAGE_UIS)

        # ----------------------------------------------------------------------------------------------------
        # OSC

        elif currentRow == self.TAB_INDEX_OSC:
            self.ui.ch_osc_enable.setChecked(CARLA_DEFAULT_OSC_ENABLED)
            self.ui.group_osc_tcp_port.setChecked(CARLA_DEFAULT_OSC_TCP_PORT_ENABLED)
            self.ui.group_osc_udp_port.setChecked(CARLA_DEFAULT_OSC_UDP_PORT_ENABLED)
            self.ui.sb_osc_tcp_port_number.setValue(CARLA_DEFAULT_OSC_TCP_PORT_NUMBER)
            self.ui.sb_osc_udp_port_number.setValue(CARLA_DEFAULT_OSC_UDP_PORT_NUMBER)

            if CARLA_DEFAULT_OSC_TCP_PORT_RANDOM:
                self.ui.rb_osc_tcp_port_specific.setChecked(False)
                self.ui.rb_osc_tcp_port_random.setChecked(True)
            else:
                self.ui.rb_osc_tcp_port_random.setChecked(False)
                self.ui.rb_osc_tcp_port_specific.setChecked(True)

            if CARLA_DEFAULT_OSC_UDP_PORT_RANDOM:
                self.ui.rb_osc_udp_port_specific.setChecked(False)
                self.ui.rb_osc_udp_port_random.setChecked(True)
            else:
                self.ui.rb_osc_udp_port_random.setChecked(False)
                self.ui.rb_osc_udp_port_specific.setChecked(True)

        # ----------------------------------------------------------------------------------------------------
        # Paths

        elif currentRow == self.TAB_INDEX_PATHS:
            curIndex = self.ui.tw_paths.currentIndex()

            if curIndex == self.PATH_INDEX_LADSPA:
                paths = CARLA_DEFAULT_LADSPA_PATH
                paths.sort()
                self.ui.lw_ladspa.clear()

                for path in paths:
                    if not path: continue
                    self.ui.lw_ladspa.addItem(path)

            elif curIndex == self.PATH_INDEX_DSSI:
                paths = CARLA_DEFAULT_DSSI_PATH
                paths.sort()
                self.ui.lw_dssi.clear()

                for path in paths:
                    if not path: continue
                    self.ui.lw_dssi.addItem(path)

            elif curIndex == self.PATH_INDEX_LV2:
                paths = CARLA_DEFAULT_LV2_PATH
                paths.sort()
                self.ui.lw_lv2.clear()

                for path in paths:
                    if not path: continue
                    self.ui.lw_lv2.addItem(path)

            elif curIndex == self.PATH_INDEX_VST2:
                paths = CARLA_DEFAULT_VST2_PATH
                paths.sort()
                self.ui.lw_vst.clear()

                for path in paths:
                    if not path: continue
                    self.ui.lw_vst.addItem(path)

            elif curIndex == self.PATH_INDEX_VST3:
                paths = CARLA_DEFAULT_VST3_PATH
                paths.sort()
                self.ui.lw_vst3.clear()

                for path in paths:
                    if not path: continue
                    self.ui.lw_vst3.addItem(path)

            elif curIndex == self.PATH_INDEX_SF2:
                paths = CARLA_DEFAULT_SF2_PATH
                paths.sort()
                self.ui.lw_sf2.clear()

                for path in paths:
                    if not path: continue
                    self.ui.lw_sf2.addItem(path)

            elif curIndex == self.PATH_INDEX_SFZ:
                paths = CARLA_DEFAULT_SFZ_PATH
                paths.sort()
                self.ui.lw_sfz.clear()

                for path in paths:
                    if not path: continue
                    self.ui.lw_sfz.addItem(path)

        # ----------------------------------------------------------------------------------------------------
        # Wine

        elif currentRow == self.TAB_INDEX_WINE:
            self.ui.le_wine_exec.setText(CARLA_DEFAULT_WINE_EXECUTABLE)
            self.ui.cb_wine_prefix_detect.setChecked(CARLA_DEFAULT_WINE_AUTO_PREFIX)
            self.ui.le_wine_prefix_fallback.setText(CARLA_DEFAULT_WINE_FALLBACK_PREFIX)
            self.ui.group_wine_realtime.setChecked(CARLA_DEFAULT_WINE_RT_PRIO_ENABLED)
            self.ui.sb_wine_base_prio.setValue(CARLA_DEFAULT_WINE_BASE_RT_PRIO)
            self.ui.sb_wine_server_prio.setValue(CARLA_DEFAULT_WINE_SERVER_RT_PRIO)

        # ----------------------------------------------------------------------------------------------------
        # Experimental

        elif currentRow == self.TAB_INDEX_EXPERIMENTAL:
            self.resetExperimentalSettings()

    def resetExperimentalSettings(self):
        # Forever experimental
        self.ui.cb_exp_plugin_bridges.setChecked(CARLA_DEFAULT_EXPERIMENTAL_PLUGIN_BRIDGES)
        self.ui.ch_exp_wine_bridges.setChecked(CARLA_DEFAULT_EXPERIMENTAL_WINE_BRIDGES)
        self.ui.ch_exp_jack_apps.setChecked(CARLA_DEFAULT_EXPERIMENTAL_JACK_APPS)
        self.ui.ch_exp_export_lv2.setChecked(CARLA_DEFAULT_EXPERIMENTAL_LV2_EXPORT)
        self.ui.ch_exp_load_lib_global.setChecked(CARLA_DEFAULT_EXPERIMENTAL_LOAD_LIB_GLOBAL)
        self.ui.ch_exp_prevent_bad_behaviour.setChecked(CARLA_DEFAULT_EXPERIMENTAL_PREVENT_BAD_BEHAVIOUR)

        # Temporary, until stable
        self.ui.cb_canvas_fancy_eyecandy.setChecked(CARLA_DEFAULT_CANVAS_FANCY_EYE_CANDY)
        self.ui.cb_canvas_use_opengl.setChecked(CARLA_DEFAULT_CANVAS_USE_OPENGL and self.ui.cb_canvas_use_opengl.isEnabled())
        self.ui.cb_canvas_render_hq_aa.setChecked(CARLA_DEFAULT_CANVAS_HQ_ANTIALIASING and self.ui.cb_canvas_render_hq_aa.isEnabled())
        self.ui.ch_engine_force_stereo.setChecked(CARLA_DEFAULT_FORCE_STEREO)
        self.ui.ch_engine_prefer_plugin_bridges.setChecked(CARLA_DEFAULT_PREFER_PLUGIN_BRIDGES)

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot(bool)
    def slot_enableExperimental(self, toggled):
        if toggled:
            self.ui.lw_page.showRow(self.TAB_INDEX_EXPERIMENTAL)
            if self.ui.ch_exp_wine_bridges.isChecked() and not self.host.isControl:
                self.ui.lw_page.showRow(self.TAB_INDEX_WINE)
        else:
            self.ui.lw_page.hideRow(self.TAB_INDEX_EXPERIMENTAL)
            self.ui.lw_page.hideRow(self.TAB_INDEX_WINE)

    @pyqtSlot(bool)
    def slot_enableWineBridges(self, toggled):
        if toggled and not self.host.isControl:
            self.ui.lw_page.showRow(self.TAB_INDEX_WINE)
        else:
            self.ui.lw_page.hideRow(self.TAB_INDEX_WINE)

    @pyqtSlot(bool)
    def slot_pluginBridgesToggled(self, toggled):
        if not toggled:
            self.ui.ch_exp_wine_bridges.setChecked(False)
            self.ui.ch_engine_prefer_plugin_bridges.setChecked(False)
            self.ui.lw_page.hideRow(self.TAB_INDEX_WINE)

    @pyqtSlot(bool)
    def slot_canvasEyeCandyToggled(self, toggled):
        if not toggled:
            self.ui.cb_canvas_fancy_eyecandy.setChecked(False)

    @pyqtSlot(bool)
    def slot_canvasFancyEyeCandyToggled(self, toggled):
        if toggled:
            self.ui.cb_canvas_eyecandy.setChecked(True)

    @pyqtSlot(bool)
    def slot_canvasOpenGLToggled(self, toggled):
        if not toggled:
            self.ui.cb_canvas_render_hq_aa.setChecked(False)

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_getAndSetProjectPath(self):
        # FIXME
        getAndSetPath(self, self.ui.le_main_proj_folder)

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_engineAudioDriverChanged(self):
        if self.ui.cb_engine_audio_driver.currentText() == "JACK":
            self.ui.sw_engine_process_mode.setCurrentIndex(0)
        else:
            self.ui.sw_engine_process_mode.setCurrentIndex(1)

    @pyqtSlot()
    def slot_showAudioDriverSettings(self):
        driverIndex = self.ui.cb_engine_audio_driver.currentIndex()
        driverName  = self.ui.cb_engine_audio_driver.currentText()
        DriverSettingsW(self, self.host, driverIndex, driverName).exec_()

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot()
    def slot_addPluginPath(self):
        newPath = QFileDialog.getExistingDirectory(self, self.tr("Add Path"), "", QFileDialog.ShowDirsOnly)

        if not newPath:
            return

        curIndex = self.ui.tw_paths.currentIndex()

        if curIndex == self.PATH_INDEX_LADSPA:
            self.ui.lw_ladspa.addItem(newPath)
        elif curIndex == self.PATH_INDEX_DSSI:
            self.ui.lw_dssi.addItem(newPath)
        elif curIndex == self.PATH_INDEX_LV2:
            self.ui.lw_lv2.addItem(newPath)
        elif curIndex == self.PATH_INDEX_VST2:
            self.ui.lw_vst.addItem(newPath)
        elif curIndex == self.PATH_INDEX_VST3:
            self.ui.lw_vst3.addItem(newPath)
        elif curIndex == self.PATH_INDEX_SF2:
            self.ui.lw_sf2.addItem(newPath)
        elif curIndex == self.PATH_INDEX_SFZ:
            self.ui.lw_sfz.addItem(newPath)

    @pyqtSlot()
    def slot_removePluginPath(self):
        curIndex = self.ui.tw_paths.currentIndex()

        if curIndex == self.PATH_INDEX_LADSPA:
            self.ui.lw_ladspa.takeItem(self.ui.lw_ladspa.currentRow())
        elif curIndex == self.PATH_INDEX_DSSI:
            self.ui.lw_dssi.takeItem(self.ui.lw_dssi.currentRow())
        elif curIndex == self.PATH_INDEX_LV2:
            self.ui.lw_lv2.takeItem(self.ui.lw_lv2.currentRow())
        elif curIndex == self.PATH_INDEX_VST2:
            self.ui.lw_vst.takeItem(self.ui.lw_vst.currentRow())
        elif curIndex == self.PATH_INDEX_VST3:
            self.ui.lw_vst3.takeItem(self.ui.lw_vst3.currentRow())
        elif curIndex == self.PATH_INDEX_SF2:
            self.ui.lw_sf2.takeItem(self.ui.lw_sf2.currentRow())
        elif curIndex == self.PATH_INDEX_SFZ:
            self.ui.lw_sfz.takeItem(self.ui.lw_sfz.currentRow())

    @pyqtSlot()
    def slot_changePluginPath(self):
        curIndex = self.ui.tw_paths.currentIndex()

        if curIndex == self.PATH_INDEX_LADSPA:
            currentPath = self.ui.lw_ladspa.currentItem().text()
        elif curIndex == self.PATH_INDEX_DSSI:
            currentPath = self.ui.lw_dssi.currentItem().text()
        elif curIndex == self.PATH_INDEX_LV2:
            currentPath = self.ui.lw_lv2.currentItem().text()
        elif curIndex == self.PATH_INDEX_VST2:
            currentPath = self.ui.lw_vst.currentItem().text()
        elif curIndex == self.PATH_INDEX_VST3:
            currentPath = self.ui.lw_vst3.currentItem().text()
        elif curIndex == self.PATH_INDEX_SF2:
            currentPath = self.ui.lw_sf2.currentItem().text()
        elif curIndex == self.PATH_INDEX_SFZ:
            currentPath = self.ui.lw_sfz.currentItem().text()
        else:
            currentPath = ""

        newPath = QFileDialog.getExistingDirectory(self, self.tr("Add Path"), currentPath, QFileDialog.ShowDirsOnly)

        if not newPath:
            return

        if curIndex == self.PATH_INDEX_LADSPA:
            self.ui.lw_ladspa.currentItem().setText(newPath)
        elif curIndex == self.PATH_INDEX_DSSI:
            self.ui.lw_dssi.currentItem().setText(newPath)
        elif curIndex == self.PATH_INDEX_LV2:
            self.ui.lw_lv2.currentItem().setText(newPath)
        elif curIndex == self.PATH_INDEX_VST2:
            self.ui.lw_vst.currentItem().setText(newPath)
        elif curIndex == self.PATH_INDEX_VST3:
            self.ui.lw_vst3.currentItem().setText(newPath)
        elif curIndex == self.PATH_INDEX_SF2:
            self.ui.lw_sf2.currentItem().setText(newPath)
        elif curIndex == self.PATH_INDEX_SFZ:
            self.ui.lw_sfz.currentItem().setText(newPath)

    # --------------------------------------------------------------------------------------------------------

    @pyqtSlot(int)
    def slot_pluginPathTabChanged(self, index):
        if index == self.PATH_INDEX_LADSPA:
            row = self.ui.lw_ladspa.currentRow()
        elif index == self.PATH_INDEX_DSSI:
            row = self.ui.lw_dssi.currentRow()
        elif index == self.PATH_INDEX_LV2:
            row = self.ui.lw_lv2.currentRow()
        elif index == self.PATH_INDEX_VST2:
            row = self.ui.lw_vst.currentRow()
        elif index == self.PATH_INDEX_VST3:
            row = self.ui.lw_vst3.currentRow()
        elif index == self.PATH_INDEX_SF2:
            row = self.ui.lw_sf2.currentRow()
        elif index == self.PATH_INDEX_SFZ:
            row = self.ui.lw_sfz.currentRow()
        else:
            row = -1

        check = bool(row >= 0)
        self.ui.b_paths_remove.setEnabled(check)
        self.ui.b_paths_change.setEnabled(check)

    @pyqtSlot(int)
    def slot_pluginPathRowChanged(self, row):
        check = bool(row >= 0)
        self.ui.b_paths_remove.setEnabled(check)
        self.ui.b_paths_change.setEnabled(check)

    # --------------------------------------------------------------------------------------------------------

    def done(self, r):
        QDialog.done(self, r)
        self.close()

# ------------------------------------------------------------------------------------------------------------
# Main

if __name__ == '__main__':
    from carla_app import CarlaApplication
    from carla_host import initHost, loadHostSettings

    initName, libPrefix = handleInitialCommandLineArguments(__file__ if "__file__" in dir() else None)

    app  = CarlaApplication("Carla2-Settings", libPrefix)
    host = initHost("Carla2-Settings", libPrefix, False, False, False)
    loadHostSettings(host)

    gui = CarlaSettingsW(None, host, True, True)
    gui.show()

    app.exit_exec()

# ------------------------------------------------------------------------------------------------------------
