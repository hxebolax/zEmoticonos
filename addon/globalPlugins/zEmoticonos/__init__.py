# -*- coding: utf-8 -*-
# Copyright (C) 2021 Héctor J. Benítez Corredera <xebolax@gmail.com>
# This file is covered by the GNU General Public License.

import globalPluginHandler
import addonHandler
import languageHandler
import core
import globalVars
import ui
import gui
import api
import watchdog
from scriptHandler import script
from keyboardHandler import KeyboardInputGesture
import wx
import os
import sys
import time
from threading import Thread

addonHandler.initTranslation()

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)

		if globalVars.appArgs.secure: return

		self.winOn = False
		self.validate = False
		self.emoList = []
		self.emoListName = []
		self._MainConfig = HiloComplemento(self, 2)
		self._MainConfig.start()

	@script(gesture=None, description= _("Muestra la ventana de zEmoticonos"), category= _("zEmoticonos"))
	def script_Run(self, event):
		if self.validate:
			if self.winOn == False:
				self._MainWindows = HiloComplemento(self, 1)
				self._MainWindows.start()
			else:
				msg = \
_("""Ya hay una instancia de zEmoticonos abierta.

No es posible tener dos instancias a la vez.""")
				ui.message(msg)
		else:
			msg = \
_("""No se pudo cargar el archivo de datos.""")
			ui.message(msg)

class zEmoticonos(wx.Dialog):
	def _calculatePosition(self, width, height):
		w = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
		h = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
		# Centre of the screen
		x = w / 2
		y = h / 2
		# Minus application offset
		x -= (width / 2)
		y -= (height / 2)
		return (x, y)

	def __init__(self, parent, selfPrincipal):

		WIDTH = 800
		HEIGHT = 600
		pos = self._calculatePosition(WIDTH, HEIGHT)

		super(zEmoticonos, self).__init__(parent, -1, title=_("zEmoticonos - {}emoticonos y símbolos").format(len(selfPrincipal.emoList)),pos = pos, size = (WIDTH, HEIGHT))

		self.selfPrincipal = selfPrincipal
		self.selfPrincipal.winOn = True
		self._filtro = None

		self.Panel = wx.Panel(self, 1)

		labelBusqueda = wx.StaticText(self.Panel, wx.ID_ANY, _("&Buscar:"))
		self.textoBusqueda = wx.TextCtrl(self.Panel, 2,style = wx.TE_PROCESS_ENTER)
		self.textoBusqueda.Bind(wx.EVT_CONTEXT_MENU, self.skip)
		self.textoBusqueda.Bind(wx.EVT_TEXT_ENTER, self.onBusqueda)
		self.textoBusqueda.Bind(wx.EVT_KEY_UP, self.onPrincipalTeclas)

		labelemoticonos = wx.StaticText(self.Panel, wx.ID_ANY, _("&Lista emoticonos y símbolos:"))
		self.listbox = wx.ListBox(self.Panel, 3)
		self.listbox.Append(self.selfPrincipal.emoListName)
		self.listbox.SetSelection(0)
		self.listbox.Bind(wx.EVT_KEY_UP, self.onLisbox)

		labelescritura = wx.StaticText(self.Panel, wx.ID_ANY, _("&Editor de texto:"))
		self.textoPegar = wx.TextCtrl(self.Panel, 4)
		self.textoPegar.Bind(wx.EVT_CONTEXT_MENU, self.skip)
		self.textoPegar.Bind(wx.EVT_KEY_UP, self.onPrincipalTeclas)

		self.CancelarBTN = wx.Button(self.Panel, wx.ID_CANCEL, label=_("&Cerrar"))
		self.Bind(wx.EVT_BUTTON, self.onSalir, id=wx.ID_CANCEL)

		self.Bind(wx.EVT_CLOSE, self.onSalir)

		sizeV = wx.BoxSizer(wx.VERTICAL)

		sizeV.Add(labelBusqueda, 0, wx.EXPAND)
		sizeV.Add(self.textoBusqueda, 0, wx.EXPAND)

		sizeV.Add(labelemoticonos, 0, wx.EXPAND)
		sizeV.Add(self.listbox, 1, wx.EXPAND)

		sizeV.Add(labelescritura, 0, wx.EXPAND)
		sizeV.Add(self.textoPegar, 0, wx.EXPAND)

		sizeV.Add(self.CancelarBTN, 0, wx.CENTRE)

		self.Panel.SetSizer(sizeV)

		self.CenterOnScreen()

	def contador(self, texto):
		numEmo = len(''.join(c for c in texto if c in self.selfPrincipal.emoList)) * 2
		numChar = len(''.join(c for c in texto if c not in self.selfPrincipal.emoList))
		return numEmo + numChar

	def skip(self, event):
		return

	def onBusqueda(self, event):
		if self.textoBusqueda.GetValue() == "":
			self.listbox.Clear()
			self.listbox.Append(self.selfPrincipal.emoListName)
			self.listbox.SetSelection(0)
			self.listbox.SetFocus()
		else:
			pattern = self.textoBusqueda.GetValue()
			filtro = [item for item in self.selfPrincipal.emoListName if pattern.lower() in item.lower()]
			self.listbox.Clear()
			if len(filtro) == 0:
				self.listbox.Append(_("No se encontraron resultados"))
				self.listbox.SetSelection(0)
				self.listbox.SetFocus()
			else:
				self.listbox.Append(filtro)
				self.listbox.SetSelection(0)
				self.listbox.SetFocus()

	def onLisbox(self, event):
		if self.listbox.GetSelection() == -1:
			pass
		else:
			if self.listbox.GetString(self.listbox.GetSelection()) == _("No se encontraron resultados"):
				pass
			else:
				if event.GetKeyCode() == 32: # 13 Intro 32 Espacio
					nombre = self.listbox.GetString(self.listbox.GetSelection())
					indice = [i for i,x in enumerate(self.selfPrincipal.emoListName) if x ==nombre]
					final = self.textoPegar.GetLastPosition()
					pos = self.textoPegar.GetInsertionPoint()
					if final == pos:
						self.textoPegar.SetSelection(0,0)
					if len(indice) == 1:
						selected1, selected2 = self.textoPegar.GetSelection()
						self.textoPegar.AppendText(self.selfPrincipal.emoList[indice[0]])
						if selected1 != 0:
							self.textoPegar.SetInsertionPoint(selected1)
					else:
						ui.message(_("Se encontró más de un emoticono."))
				elif event.GetKeyCode() == 340:
					self.onPrincipalTeclas(event)
				elif event.GetKeyCode() == 341: # F2 copia al portapapeles
					nombre = self.listbox.GetString(self.listbox.GetSelection())
					indice = [i for i,x in enumerate(self.selfPrincipal.emoListName) if x ==nombre]
					self.dataObj = wx.TextDataObject()
					self.dataObj.SetText(self.selfPrincipal.emoList[indice[0]])
					if wx.TheClipboard.Open():
						wx.TheClipboard.SetData(self.dataObj)
						wx.TheClipboard.Flush()
						ui.message(_("Se ha copiado al portapapeles"))
					else:
						ui.message(_("No se a podido copiar al portapapeles"))
				elif event.GetKeyCode() == 342: # F3 pega en la app
					nombre = self.listbox.GetString(self.listbox.GetSelection())
					indice = [i for i,x in enumerate(self.selfPrincipal.emoListName) if x ==nombre]
					self.Hide()
					event.Skip()
					paste = self.selfPrincipal.emoList[indice[0]]
					# Source code taken from: frequentText add-on for NVDA. Written by Rui Fontes and Ângelo Abrantes
					try:
						clipboardBackup = api.getClipData()
					except:
						pass
					api.copyToClip(paste)
					time.sleep(0.1)
					api.processPendingEvents(False)
					focus = api.getFocusObject()
					if focus.windowClassName == "ConsoleWindowClass":
						# Windows console window - Control+V doesn't work here, so using an alternative method here
						WM_COMMAND = 0x0111
						watchdog.cancellableSendMessage(focus.windowHandle, WM_COMMAND, 0xfff1, 0)
					else:
						try:
							KeyboardInputGesture.fromName("Control+v").send()
						except:
							# Solución para teclados con caracteres cirilicos.
							KeyboardInputGesture.fromName("shift+insert").send()

					try:
						core.callLater(300, lambda: api.copyToClip(clipboardBackup))
					except:
						pass
					self.onSalir(None)

	def onPrincipalTeclas(self, event):
		cantidad = self.contador(self.textoPegar.GetValue())
		if event.GetKeyCode() == 340: # F1 info total caracteres
			if cantidad == 0:
				ui.message(_("Sin caracteres"))
			else:
					ui.message(_("{} caracteres").format(cantidad))
		elif event.GetKeyCode() == 341: # F2 copia al portapapeles
			if cantidad == 0:
				ui.message(_("No hay nada para copiar al portapapeles"))
			else:
				self.dataObj = wx.TextDataObject()
				self.dataObj.SetText(self.textoPegar.GetValue())
				if wx.TheClipboard.Open():
					wx.TheClipboard.SetData(self.dataObj)
					wx.TheClipboard.Flush()
					ui.message(_("Se ha copiado al portapapeles"))
				else:
					ui.message(_("No se a podido copiar al portapapeles"))
		elif event.GetKeyCode() == 342: # F3 pega en la app
			if cantidad == 0:
				ui.message(_("No hay nada para copiar al foco"))
			else:
				self.Hide()
				event.Skip()
				tempPaste = self.textoPegar.GetValue()
				paste = u"{}".format(tempPaste)
				# Source code taken from: frequentText add-on for NVDA. Written by Rui Fontes and Ângelo Abrantes
				try:
					clipboardBackup = api.getClipData()
				except:
					pass
				api.copyToClip(paste)
				time.sleep(0.1)
				api.processPendingEvents(False)
				focus = api.getFocusObject()
				if focus.windowClassName == "ConsoleWindowClass":
					# Windows console window - Control+V doesn't work here, so using an alternative method here
					WM_COMMAND = 0x0111
					watchdog.cancellableSendMessage(focus.windowHandle, WM_COMMAND, 0xfff1, 0)
				else:
					try:
						KeyboardInputGesture.fromName("Control+v").send()
					except:
						# Solución para teclados con caracteres cirilicos.
						KeyboardInputGesture.fromName("shift+insert").send()

				try:
					core.callLater(300, lambda: api.copyToClip(clipboardBackup))
				except:
					pass
				self.onSalir(None)

	def onSalir(self, event):
		self.selfPrincipal.winOn = False
		self.Destroy()
		gui.mainFrame.postPopup()

class HiloComplemento(Thread):
	def __init__(self, frame, opcion):
		super(HiloComplemento, self).__init__()

		self.frame = frame
		self.opcion = opcion
		self.daemon = True

	def run(self):
		def ze_app():
			self.windowsApp = zEmoticonos(gui.mainFrame, self.frame)
			gui.mainFrame.prePopup()
			self.windowsApp.Show()

		def ze_config():
			directorioIdiomas = os.path.join(globalVars.appDir, "locale")
			try:
				idioma = languageHandler.curLang
			except:
				idioma = languageHandler.getLanguage()
			if os.path.isdir(os.path.join(directorioIdiomas, idioma)):
				pass
			elif os.path.isdir(os.path.join(directorioIdiomas, idioma[:2])):
				try:
					idioma = languageHandler.curLang[:2]
				except:
					idioma = languageHandler.getLanguage()[:2]
				else:
				idioma = "es"
			fichero = os.path.join(directorioIdiomas, idioma, "cldr.dic")
			if os.path.exists(fichero):
				try:
					with open(fichero, encoding='utf8') as data:
						content = data.readlines()
						content = content[1:]
						for line in content:
							spl = line.strip().split("	")
							self.frame.emoList.append(spl[0])
							self.frame.emoListName.append(spl[1])
					self.frame.validate = True
				except:
					self.frame.validate = False
			else:
				self.frame.validate = False

		if self.opcion == 1:
			wx.CallAfter(ze_app)
		if self.opcion == 2:
			wx.CallAfter(ze_config)
