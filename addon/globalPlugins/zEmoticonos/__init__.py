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
import json
import wx
import os
import sys
import time
from threading import Thread
from . import ajustes

addonHandler.initTranslation()


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)

		self.winOn = False
		self.validate = False
		self.emoList = []
		self.emoListName = []
		self.emoListFAV = []
		self.emoListNameFAV = []
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

if globalVars.appArgs.secure:
	GlobalPlugin = globalPluginHandler.GlobalPlugin # noqa: F811 

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

		if ajustes.categoria == 0:
			super(zEmoticonos, self).__init__(parent, -1, title=_("zEmoticonos - General - {} emoticonos y símbolos").format(len(selfPrincipal.emoList)),pos = pos, size = (WIDTH, HEIGHT))
		else:
			super(zEmoticonos, self).__init__(parent, -1, title=_("zEmoticonos - Favoritos - {} emoticonos y símbolos").format(len(selfPrincipal.emoListFAV)),pos = pos, size = (WIDTH, HEIGHT))

		self.selfPrincipal = selfPrincipal
		self.selfPrincipal.winOn = True
		self._filtro = None

		self.Panel = wx.Panel(self, 1)

		label_1 = wx.StaticText(self.Panel, wx.ID_ANY, _("C&ategoría:"))
		self.choice = wx.Choice(self.Panel, wx.ID_ANY, choices=[_("General"), _("Favoritos")])
		self.choice.SetSelection(ajustes.categoria)
		self.choice.Bind(wx.EVT_CHOICE, self.onChoice)

		labelBusqueda = wx.StaticText(self.Panel, wx.ID_ANY, _("&Buscar:"))
		self.textoBusqueda = wx.TextCtrl(self.Panel, 2,style = wx.TE_PROCESS_ENTER)
		self.textoBusqueda.Bind(wx.EVT_CONTEXT_MENU, self.skip)
		self.textoBusqueda.Bind(wx.EVT_TEXT_ENTER, self.onBusqueda)
		self.textoBusqueda.Bind(wx.EVT_KEY_UP, self.onPrincipalTeclas)

		labelemoticonos = wx.StaticText(self.Panel, wx.ID_ANY, _("&Lista emoticonos y símbolos:"))
		self.listbox = wx.ListBox(self.Panel, 3)
		if ajustes.categoria == 0:
			self.listbox.Append(self.selfPrincipal.emoListName)
			self.listbox.SetSelection(0)
		else:
			self.onCargarFavoritos()
		self.listbox.Bind(wx.EVT_KEY_UP, self.onLisbox)

		labelescritura = wx.StaticText(self.Panel, wx.ID_ANY, _("&Editor de texto:"))
		self.textoPegar = wx.TextCtrl(self.Panel, 4)
		self.textoPegar.Bind(wx.EVT_CONTEXT_MENU, self.skip)
		self.textoPegar.Bind(wx.EVT_KEY_UP, self.onPrincipalTeclas)

		self.CancelarBTN = wx.Button(self.Panel, wx.ID_CANCEL, label=_("&Cerrar"))
		self.Bind(wx.EVT_BUTTON, self.onSalir, id=wx.ID_CANCEL)

		self.Bind(wx.EVT_CLOSE, self.onSalir)

		sizeV = wx.BoxSizer(wx.VERTICAL)

		sizeV.Add(label_1, 0, wx.EXPAND)
		sizeV.Add(self.choice, 0, wx.EXPAND)

		sizeV.Add(labelBusqueda, 0, wx.EXPAND)
		sizeV.Add(self.textoBusqueda, 0, wx.EXPAND)

		sizeV.Add(labelemoticonos, 0, wx.EXPAND)
		sizeV.Add(self.listbox, 1, wx.EXPAND)

		sizeV.Add(labelescritura, 0, wx.EXPAND)
		sizeV.Add(self.textoPegar, 0, wx.EXPAND)

		sizeV.Add(self.CancelarBTN, 0, wx.CENTRE)

		self.Panel.SetSizer(sizeV)

		self.CenterOnScreen()
		self.textoBusqueda.SetFocus()

	def contador(self, texto):
		if ajustes.categoria == 0:
			numEmo = len(''.join(c for c in texto if c in self.selfPrincipal.emoList)) * 2
			numChar = len(''.join(c for c in texto if c not in self.selfPrincipal.emoList))
			return numEmo + numChar
		else:
			numEmo = len(''.join(c for c in texto if c in self.selfPrincipal.emoListFAV)) * 2
			numChar = len(''.join(c for c in texto if c not in self.selfPrincipal.emoListFAV))
			return numEmo + numChar

	def onCargarFavoritos(self):
		fileFavoritos = os.path.join(globalVars.appArgs.configPath, "zEmoticonos", "favoritos.json")
		with open(fileFavoritos, "r") as fp:
			datosFavoritos = json.load(fp)
		self.listbox.Clear()
		del self.selfPrincipal.emoListFAV[:]
		del self.selfPrincipal.emoListNameFAV[:]
		if len(datosFavoritos) == 0:
			self.listbox.Append(_("Sin favoritos"))
		else:
			for i in range(0, len(datosFavoritos)):
				self.selfPrincipal.emoListFAV.append(datosFavoritos[i][0])
				self.selfPrincipal.emoListNameFAV.append(datosFavoritos[i][1])
			self.listbox.Append(self.selfPrincipal.emoListNameFAV)
		self.SetTitle(_("zEmoticonos - Favoritos - {} emoticonos y símbolos").format(len(self.selfPrincipal.emoListFAV)))
		self.listbox.SetSelection(0)

	def onChoice(self, event):
		id = event.GetSelection()
		ajustes.categoria = id
		if id == 0:
			self.SetTitle(_("zEmoticonos - General - {} emoticonos y símbolos").format(len(self.selfPrincipal.emoList)))
			self.listbox.Clear()
			self.listbox.Append(self.selfPrincipal.emoListName)
			self.listbox.SetSelection(0)
		else:
			self.onCargarFavoritos()

	def skip(self, event):
		return

	def onBusqueda(self, event):
		if self.textoBusqueda.GetValue() == "":
			self.listbox.Clear()
			if ajustes.categoria == 0:
				self.listbox.Append(self.selfPrincipal.emoListName)
			else:
				if len(self.selfPrincipal.emoListNameFAV) == 0:
					self.listbox.Append(_("Sin favoritos"))
				else:
					self.listbox.Append(self.selfPrincipal.emoListNameFAV)
			self.listbox.SetSelection(0)
			self.listbox.SetFocus()
		else:
			pattern = self.textoBusqueda.GetValue()
			if ajustes.categoria == 0:
				filtro = [item for item in self.selfPrincipal.emoListName if pattern.lower() in item.lower()]
			else:
				filtro = [item for item in self.selfPrincipal.emoListNameFAV if pattern.lower() in item.lower()]
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
				if self.listbox.GetString(self.listbox.GetSelection()) == _("Sin favoritos"):
					pass
				else:
					if event.GetKeyCode() == 32: # 13 Intro 32 Espacio
						nombre = self.listbox.GetString(self.listbox.GetSelection())
						if ajustes.categoria == 0:
							indice = [i for i,x in enumerate(self.selfPrincipal.emoListName) if x ==nombre]
						else:
							indice = [i for i,x in enumerate(self.selfPrincipal.emoListNameFAV) if x ==nombre]
						final = self.textoPegar.GetLastPosition()
						pos = self.textoPegar.GetInsertionPoint()
						if final == pos:
							self.textoPegar.SetSelection(0,0)
						if len(indice) == 1:
							selected1, selected2 = self.textoPegar.GetSelection()
							if ajustes.categoria == 0:
								self.textoPegar.AppendText(self.selfPrincipal.emoList[indice[0]])
							else:
								self.textoPegar.AppendText(self.selfPrincipal.emoListFAV[indice[0]])
							if selected1 != 0:
								self.textoPegar.SetInsertionPoint(selected1)
						else:
							ui.message(_("Se encontró más de un emoticono."))
					elif event.GetKeyCode() == 340:
						self.onPrincipalTeclas(event)
					elif event.GetKeyCode() == 341: # F2 copia al portapapeles
						nombre = self.listbox.GetString(self.listbox.GetSelection())
						if ajustes.categoria == 0:
							indice = [i for i,x in enumerate(self.selfPrincipal.emoListName) if x ==nombre]
						else:
							indice = [i for i,x in enumerate(self.selfPrincipal.emoListNameFAV) if x ==nombre]

						self.dataObj = wx.TextDataObject()
						if ajustes.categoria == 0:
							self.dataObj.SetText(self.selfPrincipal.emoList[indice[0]])
						else:
							self.dataObj.SetText(self.selfPrincipal.emoListFAV[indice[0]])
						if wx.TheClipboard.Open():
							wx.TheClipboard.SetData(self.dataObj)
							wx.TheClipboard.Flush()
							ui.message(_("Se ha copiado al portapapeles"))
						else:
							ui.message(_("No se a podido copiar al portapapeles"))
					elif event.GetKeyCode() == 342: # F3 pega en la app
						try:
							clipboardBackup = api.getClipData()
						except:
							pass

						nombre = self.listbox.GetString(self.listbox.GetSelection())
						if ajustes.categoria == 0:
							indice = [i for i,x in enumerate(self.selfPrincipal.emoListName) if x ==nombre]
						else:
							indice = [i for i,x in enumerate(self.selfPrincipal.emoListNameFAV) if x ==nombre]

						self.Hide()
						event.Skip()
						if ajustes.categoria == 0:
							paste = self.selfPrincipal.emoList[indice[0]]
						else:
							paste = self.selfPrincipal.emoListFAV[indice[0]]

						# Source code taken from: frequentText add-on for NVDA. Written by Rui Fontes and Ângelo Abrantes
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

#						try:
#							core.callLater(300, lambda: api.copyToClip(clipboardBackup))
#						except:
#							pass
						self.onSalir(None)
					elif event.GetKeyCode() == 343:
						nombre = self.listbox.GetString(self.listbox.GetSelection())
						fileFavoritos = os.path.join(globalVars.appArgs.configPath, "zEmoticonos", "favoritos.json")
						if ajustes.categoria == 0:
							indice = [i for i,x in enumerate(self.selfPrincipal.emoListName) if x ==nombre]
							if ajustes.estaenlistado(self.selfPrincipal.emoListNameFAV, self.selfPrincipal.emoListName[indice[0]]):
								ui.message(_("No se puede copiar {} por que ya esta en favoritos").format(self.selfPrincipal.emoListName[indice[0]]))
							else:
								with open(fileFavoritos, "r") as fp:
									datosFavoritos = json.load(fp)
								datosFavoritos.append([self.selfPrincipal.emoList[indice[0]], self.selfPrincipal.emoListName[indice[0]]])
								with open(fileFavoritos, "w") as fp:
									json.dump(datosFavoritos, fp)
								ui.message(_("{} Añadido a favoritos").format(self.selfPrincipal.emoListName[indice[0]]))
						else:
							indice = [i for i,x in enumerate(self.selfPrincipal.emoListNameFAV) if x ==nombre]
							with open(fileFavoritos, "r") as fp:
								datosFavoritos = json.load(fp)
							del datosFavoritos[indice[0]]
							with open(fileFavoritos, "w") as fp:
								json.dump(datosFavoritos, fp)
							ui.message(_("{} Eliminado de favoritos").format(self.selfPrincipal.emoListNameFAV[indice[0]]))
							self.onCargarFavoritos()

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

#				try:
#					core.callLater(300, lambda: api.copyToClip(clipboardBackup))
#				except:
#					pass
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
			dirDatos =os.path.join(globalVars.appArgs.configPath, "zEmoticonos")
			if os.path.exists(dirDatos) == False:
				os.mkdir(dirDatos)
			fileFavoritos = os.path.join(globalVars.appArgs.configPath, "zEmoticonos", "favoritos.json")
			if os.path.isfile(fileFavoritos):
				with open(fileFavoritos, "r") as fp:
					datosFavoritos = json.load(fp)

				for i in range(0, len(datosFavoritos)):
					self.frame.emoListFAV.append(datosFavoritos[i][0])
					self.frame.emoListNameFAV.append(datosFavoritos[i][1])
			else:
				with open(fileFavoritos, "w") as fp:
					json.dump([], fp)

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
