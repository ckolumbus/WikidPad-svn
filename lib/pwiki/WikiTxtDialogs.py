## import hotshot
## _prof = hotshot.Profile("hotshot.prf")

import traceback

import wx, wx.xrc

# from Utilities import *  # TODO Remove this

from wxHelper import GUI_ID, XrcControls, getAccelPairFromKeyDown, \
        runDialogModalFactory


from StringOps import unescapeForIni

import SystemInfo


try:
    import WindowsHacks
except:
    if SystemInfo.isWindows():
        traceback.print_exc()
    WindowsHacks = None



class IncrementalSearchDialog(wx.Frame):
    
    COLOR_YELLOW = wx.Colour(255, 255, 0);
    COLOR_GREEN = wx.Colour(0, 255, 0);
    
    def __init__(self, parent, id, txtCtrl, rect, font, mainControl, searchInit=None):
        # Frame title is invisible but is helpful for workarounds with
        # third-party tools
        wx.Frame.__init__(self, parent, id, u"WikidPad i-search",
                rect.GetPosition(), rect.GetSize(),
                wx.NO_BORDER | wx.FRAME_FLOAT_ON_PARENT)

        self.txtCtrl = txtCtrl
        self.mainControl = mainControl
        self.tfInput = wx.TextCtrl(self, GUI_ID.INC_SEARCH_TEXT_FIELD,
                _(u"Incremental search (ENTER/ESC to finish)"),
                style=wx.TE_PROCESS_ENTER | wx.TE_RICH)

        self.tfInput.SetFont(font)
        self.tfInput.SetBackgroundColour(IncrementalSearchDialog.COLOR_YELLOW)
        mainsizer = wx.BoxSizer(wx.HORIZONTAL)
        mainsizer.Add(self.tfInput, 1, wx.ALL | wx.EXPAND, 0)

        self.SetSizer(mainsizer)
        self.Layout()
        self.tfInput.SelectAll()  #added for Mac compatibility
        self.tfInput.SetFocus()

        config = self.mainControl.getConfig()

        self.closeDelay = 1000 * config.getint("main", "incSearch_autoOffDelay",
                0)  # Milliseconds to close or 0 to deactivate

        wx.EVT_TEXT(self, GUI_ID.INC_SEARCH_TEXT_FIELD, self.OnText)
        wx.EVT_KEY_DOWN(self.tfInput, self.OnKeyDownInput)
        wx.EVT_KILL_FOCUS(self.tfInput, self.OnKillFocus)
        wx.EVT_TIMER(self, GUI_ID.TIMER_INC_SEARCH_CLOSE,
                self.OnTimerIncSearchClose)
        wx.EVT_MOUSE_EVENTS(self.tfInput, self.OnMouseAnyInput)

        if searchInit:
            self.tfInput.SetValue(searchInit)
            self.tfInput.SetSelection(-1, -1)

        if self.closeDelay:
            self.closeTimer = wx.Timer(self, GUI_ID.TIMER_INC_SEARCH_CLOSE)
            self.closeTimer.Start(self.closeDelay, True)

#     def Close(self):
#         wx.Frame.Close(self)
#         self.txtCtrl.SetFocus()


    def OnKillFocus(self, evt):
        self.txtCtrl.forgetIncrementalSearch()
        self.Close()

    def OnText(self, evt):
        self.txtCtrl.searchStr = self.tfInput.GetValue()
        foundPos = self.txtCtrl.executeIncrementalSearch()

        if foundPos == -1:
            # Nothing found
            self.tfInput.SetBackgroundColour(IncrementalSearchDialog.COLOR_YELLOW)
        else:
            # Found
            self.tfInput.SetBackgroundColour(IncrementalSearchDialog.COLOR_GREEN)

    def OnMouseAnyInput(self, evt):
#         if evt.Button(wx.MOUSE_BTN_ANY) and self.closeDelay:

        # Workaround for name clash in wx.MouseEvent.Button:
        if wx._core_.MouseEvent_Button(evt, wx.MOUSE_BTN_ANY) and self.closeDelay:
            # If a mouse button was pressed/released, restart timer
            self.closeTimer.Start(self.closeDelay, True)

        evt.Skip()


    def OnKeyDownInput(self, evt):
        if self.closeDelay:
            self.closeTimer.Start(self.closeDelay, True)

        key = evt.GetKeyCode()
        accP = getAccelPairFromKeyDown(evt)
        matchesAccelPair = self.mainControl.keyBindings.matchesAccelPair

        foundPos = -2
        if accP in ((wx.ACCEL_NORMAL, wx.WXK_NUMPAD_ENTER),
                (wx.ACCEL_NORMAL, wx.WXK_RETURN)):
            # Return pressed
            self.txtCtrl.endIncrementalSearch()
            self.Close()
        elif accP == (wx.ACCEL_NORMAL, wx.WXK_ESCAPE):
            # Esc -> Abort inc. search, go back to start
            self.txtCtrl.resetIncrementalSearch()
            self.Close()
        elif matchesAccelPair("ContinueSearch", accP):
            foundPos = self.txtCtrl.executeIncrementalSearch(next=True)
        # do the next search on another ctrl-f
        elif matchesAccelPair("StartIncrementalSearch", accP):
            foundPos = self.txtCtrl.executeIncrementalSearch(next=True)
        elif accP in ((wx.ACCEL_NORMAL, wx.WXK_DOWN),
                (wx.ACCEL_NORMAL, wx.WXK_PAGEDOWN),
                (wx.ACCEL_NORMAL, wx.WXK_NUMPAD_DOWN),
                (wx.ACCEL_NORMAL, wx.WXK_NUMPAD_PAGEDOWN),
                (wx.ACCEL_NORMAL, wx.WXK_NEXT)):
            foundPos = self.txtCtrl.executeIncrementalSearch(next=True)
        elif matchesAccelPair("BackwardSearch", accP):
            foundPos = self.txtCtrl.executeIncrementalSearchBackward()
        elif accP in ((wx.ACCEL_NORMAL, wx.WXK_UP),
                (wx.ACCEL_NORMAL, wx.WXK_PAGEUP),
                (wx.ACCEL_NORMAL, wx.WXK_NUMPAD_UP),
                (wx.ACCEL_NORMAL, wx.WXK_NUMPAD_PAGEUP),
                (wx.ACCEL_NORMAL, wx.WXK_PRIOR)):
            foundPos = self.txtCtrl.executeIncrementalSearchBackward()
        elif matchesAccelPair("ActivateLink", accP):
            # ActivateLink is normally Ctrl-L
            self.txtCtrl.endIncrementalSearch()
            self.Close()
            self.txtCtrl.OnKeyDown(evt)
        elif matchesAccelPair("ActivateLinkNewTab", accP):
            # ActivateLinkNewTab is normally Ctrl-Alt-L
            self.txtCtrl.endIncrementalSearch()
            self.Close()
            self.txtCtrl.OnKeyDown(evt)
        elif matchesAccelPair("ActivateLink2", accP):
            # ActivateLink2 is normally Ctrl-Return
            self.txtCtrl.endIncrementalSearch()
            self.Close()
            self.txtCtrl.OnKeyDown(evt)
        elif matchesAccelPair("ActivateLinkBackground", accP):
            # ActivateLinkNewTab is normally Ctrl-Alt-L
            self.txtCtrl.endIncrementalSearch()
            self.Close()
            self.txtCtrl.OnKeyDown(evt)
        # handle the other keys
        else:
            evt.Skip()

        if foundPos == -1:
            # Nothing found
            self.tfInput.SetBackgroundColour(IncrementalSearchDialog.COLOR_YELLOW)
        elif foundPos >= 0:
            # Found
            self.tfInput.SetBackgroundColour(IncrementalSearchDialog.COLOR_GREEN)

        # Else don't change

    if SystemInfo.isOSX():
        # Fix focus handling after close
        def Close(self):
            wx.Frame.Close(self)
            wx.CallAfter(self.txtCtrl.SetFocus)

    def OnTimerIncSearchClose(self, evt):
        self.txtCtrl.endIncrementalSearch()  # TODO forgetIncrementalSearch() instead?
        self.Close()




class FilePasteParams:
    """
    Helper class to store file paste settings
    """
    def __init__(self):
        self.rawPrefix = u""  # Prefix before file links
                # (before calling StringOps.strftimeUB on it)
        self.rawMiddle = u" "  # Middle text between links
        self.rawSuffix = u""  # Suffix after links

        self.unifActionName = None  # Unified name of the action to do 
#         self.actionParamDict = None  # Parameter dict of action


    def readOptionsFromConfig(self, config):
        """
        config -- SingleConfiguration or CombinedConfiguration to read default
                settings from into the object
        """
        self.rawPrefix = unescapeForIni(config.get("main",
                "editor_filePaste_prefix", u""))
        self.rawMiddle = unescapeForIni(config.get("main",
                "editor_filePaste_middle", u" "))
        self.rawSuffix = unescapeForIni(config.get("main",
                "editor_filePaste_suffix", u""))



class FilePasteDialog(wx.Dialog):
    def __init__(self, pWiki, ID, filepastesaver, title=None,
                 pos=wx.DefaultPosition, size=wx.DefaultSize):
        d = wx.PreDialog()
        self.PostCreate(d)

        self.pWiki = pWiki
        res = wx.xrc.XmlResource.Get()
        res.LoadOnDialog(self, self.pWiki, "FilePasteDialog")

        self.ctrls = XrcControls(self)

        if title is not None:
            self.SetTitle(title)

        self.ctrls.tfEditorFilePastePrefix.SetValue(filepastesaver.rawPrefix)
        self.ctrls.tfEditorFilePasteMiddle.SetValue(filepastesaver.rawMiddle)
        self.ctrls.tfEditorFilePasteSuffix.SetValue(filepastesaver.rawSuffix)

        self.filepastesaver = None

        self.ctrls.btnOk.SetId(wx.ID_OK)
        self.ctrls.btnCancel.SetId(wx.ID_CANCEL)
        
        # Fixes focus bug under Linux
        self.SetFocus()

        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)


    def GetValue(self):
        return self.filepastesaver


    _ACTIONSEL_TO_UNIFNAME = {
            0: u"action/editor/this/paste/files/insert/url/absolute",
            1: u"action/editor/this/paste/files/insert/url/relative",
            2: u"action/editor/this/paste/files/insert/url/tostorage",
            3: u"action/editor/this/paste/files/insert/url/movetostorage"
        }

    def OnOk(self, evt):
        try:
            filepastesaver = FilePasteParams()

            actionSel = self.ctrls.chEditorFilePasteOperation.GetSelection()
            filepastesaver.unifActionName = self._ACTIONSEL_TO_UNIFNAME[actionSel]

            filepastesaver.rawPrefix = \
                    self.ctrls.tfEditorFilePastePrefix.GetValue()
            filepastesaver.rawMiddle = \
                    self.ctrls.tfEditorFilePasteMiddle.GetValue()
            filepastesaver.rawSuffix = \
                    self.ctrls.tfEditorFilePasteSuffix.GetValue()

            self.filepastesaver = filepastesaver

        finally:
            self.EndModal(wx.ID_OK)


FilePasteDialog.runModal = staticmethod(runDialogModalFactory(FilePasteDialog))




class ImagePasteSaver:
    """
    Helper class to store image settings (format, quality) and to 
    perform saving on request.
    """
    def __init__(self):
        self.prefix = u""  # Prefix before random numbers in filename
        self.formatNo = 0  # Currently either 0:None, 1:PNG or 2:JPG
        self.quality = 75   # Quality for JPG image


    def readOptionsFromConfig(self, config):
        """
        config -- SingleConfiguration or CombinedConfiguration to read default
                settings from into the object
        """
        self.prefix = config.get("main", "editor_imagePaste_filenamePrefix", u"")

        self.formatNo = config.getint("main", "editor_imagePaste_fileType", u"")

        quality = config.getint("main", "editor_imagePaste_quality", 75)
        quality = min(100, quality)
        quality = max(0, quality)

        self.quality = quality


    def setQualityByString(self, s):
        try:
            quality = int(s)
            quality = min(100, quality)
            quality = max(0, quality)
    
            self.quality = quality
        except ValueError:
            return


#     def setFormatByFormatNo(self, formatNo):
#         if formatNo == 1:
#             self.format = "png"
#         elif formatNo == 2:
#             self.format = "jpg"
#         else:  # formatNo == 0
#             self.format = "none"


    def saveFile(self, fs, img):
        """
        fs -- FileStorage to save into
        img -- wx.Image to save

        Returns absolute path of saved image or None if not saved
        """
        if self.formatNo < 1 or self.formatNo > 2:
            return None

        img.SetOptionInt(u"quality", self.quality)

        if self.formatNo == 1:   # PNG
            destPath = fs.findDestPathNoSource(u".png", self.prefix)
        elif self.formatNo == 2:   # JPG
            destPath = fs.findDestPathNoSource(u".jpg", self.prefix)

        if destPath is None:
            # Couldn't find unused filename
            return None

        if self.formatNo == 1:   # PNG
            img.SaveFile(destPath, wx.BITMAP_TYPE_PNG)
        elif self.formatNo == 2:   # JPG
            img.SaveFile(destPath, wx.BITMAP_TYPE_JPEG)

        return destPath


    def saveWmfFromClipboardToFileStorage(self, fs):
        if WindowsHacks is None:
            return None
        
        return WindowsHacks.saveWmfFromClipboardToFileStorage(fs, self.prefix)


    def saveMetaFile(self, fs, metaFile):
        """
        fs -- FileStorage to save into
        rawData -- raw bytestring to save

        Returns absolute path of saved image or None if not saved
        """
        destPath = fs.findDestPathNoSource(u".wmf", self.prefix)
        
        if destPath is None:
            # Couldn't find unused filename
            return None

        metaDC = wx.MetaFileDC(destPath)
        metaFile.Play(metaDC)
        metaDC.Close()

#         writeEntireFile(destPath, rawData)
        
        return destPath




class ImagePasteDialog(wx.Dialog):
    def __init__(self, pWiki, ID, imgpastesaver, title=None,
                 pos=wx.DefaultPosition, size=wx.DefaultSize):
        d = wx.PreDialog()
        self.PostCreate(d)

        self.pWiki = pWiki
        res = wx.xrc.XmlResource.Get()
        res.LoadOnDialog(self, self.pWiki, "ImagePasteDialog")

        self.ctrls = XrcControls(self)

        if title is not None:
            self.SetTitle(title)

        self.ctrls.tfEditorImagePasteFilenamePrefix.SetValue(imgpastesaver.prefix)
        self.ctrls.chEditorImagePasteFileType.SetSelection(imgpastesaver.formatNo)
        self.ctrls.tfEditorImagePasteQuality.SetValue(unicode(
                imgpastesaver.quality))

        self.imgpastesaver = ImagePasteSaver()

        self.ctrls.btnOk.SetId(wx.ID_OK)
        self.ctrls.btnCancel.SetId(wx.ID_CANCEL)
        
        self.OnFileTypeChoice(None)
        
        # Fixes focus bug under Linux
        self.SetFocus()

        wx.EVT_BUTTON(self, wx.ID_OK, self.OnOk)
        wx.EVT_CHOICE(self, GUI_ID.chEditorImagePasteFileType,
                self.OnFileTypeChoice)


    def getImagePasteSaver(self):
        return self.imgpastesaver
        
    def OnFileTypeChoice(self, evt):
        # Make quality field gray if not JPG format
        enabled = self.ctrls.chEditorImagePasteFileType.GetSelection() == 2
        self.ctrls.tfEditorImagePasteQuality.Enable(enabled)


    def OnOk(self, evt):
        try:
            imgpastesaver = ImagePasteSaver()
            imgpastesaver.prefix = \
                    self.ctrls.tfEditorImagePasteFilenamePrefix.GetValue()
            imgpastesaver.formatNo = \
                    self.ctrls.chEditorImagePasteFileType.GetSelection()
            imgpastesaver.setQualityByString(
                    self.ctrls.tfEditorImagePasteQuality.GetValue())

            self.imgpastesaver = imgpastesaver
        finally:
            self.EndModal(wx.ID_OK)


