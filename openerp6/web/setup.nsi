#####################################################################################
#
# Copyright (c) 2004-TODAY OpenERP S.A. (http://www.openerp.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#####################################################################################

!include 'MUI2.nsh'
!include 'FileFunc.nsh'
!include 'LogicLib.nsh'
!include 'Sections.nsh'

!define PUBLISHER 'OpenERP S.A.'

!ifndef MAJOR_VERSION
    !define MAJOR_VERSION '6'
!endif

!ifndef MINOR_VERSION
    !define MINOR_VERSION '0'
!endif

!ifndef REVISION_VERSION
    !define REVISION_VERSION '0'
!endif 

!ifndef BUILD_VERSION
    !define VERSION "${MAJOR_VERSION}.${MINOR_VERSION}.${REVISION_VERSION}"
!else
    !define VERSION "${MAJOR_VERSION}.${MINOR_VERSION}.${REVISION_VERSION}-${BUILD_VERSION}"
!endif

!define PRODUCT_NAME "OpenERP Web Client"
!define DISPLAY_NAME "${PRODUCT_NAME} ${MAJOR_VERSION}.${MINOR_VERSION}"

!define UNINSTALL_REGISTRY_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${DISPLAY_NAME}"

!define REGISTRY_KEY "Software\${DISPLAY_NAME}"

Name '${DISPLAY_NAME}'
Caption "${PRODUCT_NAME} ${VERSION} Setup"
OutFile "openerp-web-setup-${VERSION}.exe"
SetCompressor /final /solid lzma
SetCompress auto
ShowInstDetails show

XPStyle on

InstallDir "$PROGRAMFILES\OpenERP ${MAJOR_VERSION}.${MINOR_VERSION}\Web"
InstallDirRegKey HKCU "${REGISTRY_KEY}" ""

BrandingText '${PRODUCT_NAME} ${VERSION}'

RequestExecutionLevel admin

#VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
#VIAddVersionKey "CompanyName" "${PUBLISHER}"
#VIAddVersionKey "FileDescription" "Installer of ${DISPLAY_NAME}" 
#VIAddVersionKey "LegalCopyright" "${PUBLISHER}"
#VIAddVersionKey "LegalTrademark" "OpenERP is a trademark of ${PUBLISHER}"
#VIAddVersionKey "FileVersion" "${MAJOR_VERSION}.${MINOR_VERSION}.${RELEASE_VERSION}"
#VIProductVersion "${MAJOR_VERSION}.${MINOR_VERSION}.${RELEASE_VERSION}"

!insertmacro GetParameters
!insertmacro GetOptions

Var Option_AllInOne
Var cmdLineParams

Var MUI_TEMP
Var STARTMENU_FOLDER

!define MUI_ABORTWARNING
!define MUI_ICON ".\pixmaps\openerp-icon.ico"

!define MUI_WELCOMEFINISHPAGE_BITMAP ".\pixmaps\openerp-intro.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP ".\pixmaps\openerp-intro.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP ".\pixmaps\openerp-slogan.bmp"
!define MUI_HEADERIMAGE_BITMAP_NOSTRETCH
!define MUI_HEADER_TRANSPARENT_TEXT ""

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "doc\License.txt"
!insertmacro MUI_PAGE_DIRECTORY

!define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKLM" 
!define MUI_STARTMENUPAGE_REGISTRY_KEY "${REGISTRY_KEY}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "${DISPLAY_NAME}"

!insertmacro MUI_PAGE_STARTMENU Application $STARTMENU_FOLDER
!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_FINISHPAGE_LINK $(DESC_FinishPage_Link) 
!define MUI_FINISHPAGE_LINK_LOCATION "http://www.openerp.com/contact"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_RESERVEFILE_LANGDLL

!macro CreateInternetShortcut FILENAME URL
	WriteINIStr "${FILENAME}.url" "InternetShortcut" "URL" "${URL}"
!macroend

; English
LangString DESC_FinishPage_Link ${LANG_ENGLISH} "Contact OpenERP for Partnership and/or Support"


; French
LangString DESC_FinishPage_Link ${LANG_FRENCH} "Contactez OpenERP pour un Partenariat et/ou du Support"

Section -StopService
    nsExec::Exec "net stop openerp-web-6.0"
    sleep 2
SectionEnd

Section OpenERP_Web_Client SectionOpenERP_Web_Client
    SetOutPath '$INSTDIR'

    File /r "dist\*"

    SetOutPath '$INSTDIR\service'
    File /r "win32\dist\*"
    File "win32\start.bat"
    File "win32\stop.bat"

    SetOutPath "$INSTDIR\conf"
    File "/oname=openerp-web.cfg" ".\openerp-web.cfg"

    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
        ;Create shortcuts
        CreateDirectory "$SMPROGRAMS\$STARTMENU_FOLDER"
        
        CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Start OpenERP Web.lnk" "$INSTDIR\service\start.bat"
        CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Stop OpenERP Web.lnk" "$INSTDIR\service\stop.bat"
        CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Edit Web Config.lnk" "notepad.exe" "$INSTDIR\conf\openerp-web.cfg"
        CreateShortCut "$SMPROGRAMS\$STARTMENU_FOLDER\Uninstall.lnk" "$INSTDIR\uninstall.exe"
        !insertmacro CreateInternetShortcut "$SMPROGRAMS\$STARTMENU_FOLDER\Forum" "http://www.openerp.com/forum"
        !insertmacro CreateInternetShortcut "$SMPROGRAMS\$STARTMENU_FOLDER\Translation" "https://translations.launchpad.net/openobject"
    !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section -RestartService
    nsExec::Exec '"$INSTDIR\service\OpenERPWebService.exe" -auto -install'
    sleep 2
    nsExec::Exec "net start openerp-web-6.0"
    sleep 2
SectionEnd

Section -Post
    WriteRegExpandStr HKLM "${UNINSTALL_REGISTRY_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegExpandStr HKLM "${UNINSTALL_REGISTRY_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "DisplayName" "${DISPLAY_NAME}"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "DisplayVersion" "${MAJOR_VERSION}.${MINOR_VERSION}"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "Publisher" "${PUBLISHER}"
    WriteRegDWORD HKLM     "${UNINSTALL_REGISTRY_KEY}" "Version" "${VERSION}"
    WriteRegDWORD HKLM     "${UNINSTALL_REGISTRY_KEY}" "VersionMajor" "${MAJOR_VERSION}.${MINOR_VERSION}"
    WriteRegDWORD HKLM     "${UNINSTALL_REGISTRY_KEY}" "VersionMinor" "${REVISION_VERSION}"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "HelpLink" "support@openerp.com"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "HelpTelephone" "+32.81.81.37.00"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "URLInfoAbout" "http://www.openerp.com"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "Contact" "sales@openerp.com"
    WriteRegDWORD HKLM     "${UNINSTALL_REGISTRY_KEY}" "NoModify" "1"
    WriteRegDWORD HKLM     "${UNINSTALL_REGISTRY_KEY}" "NoRepair" "1"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Uninstall"
    nsExec::Exec "net stop openerp-web-6.0"
    sleep 2
    nsExec::Exec '"$INSTDIR\service\OpenERPWebService.exe" -remove'
    sleep 2

    Rmdir /r "$INSTDIR"


    !insertmacro MUI_STARTMENU_GETFOLDER Application $MUI_TEMP
    Delete "$SMPROGRAMS\$MUI_TEMP\Forum.url"
    Delete "$SMPROGRAMS\$MUI_TEMP\Translation.url"
    Delete "$SMPROGRAMS\$MUI_TEMP\Uninstall.lnk"
    Delete "$SMPROGRAMS\$MUI_TEMP\Uninstall.lnk"
    Delete "$SMPROGRAMS\$MUI_TEMP\Start OpenERP Web.lnk"
    Delete "$SMPROGRAMS\$MUI_TEMP\Stop OpenERP Web.lnk"
    Delete "$SMPROGRAMS\$MUI_TEMP\Edit Web Config.lnk"

    ;Delete empty start menu parent diretories
    StrCpy $MUI_TEMP "$SMPROGRAMS\$MUI_TEMP"
 
    startMenuDeleteLoop:
        ClearErrors
        RMDir $MUI_TEMP
        GetFullPathName $MUI_TEMP "$MUI_TEMP\.."

        IfErrors startMenuDeleteLoopDone

        StrCmp $MUI_TEMP $SMPROGRAMS startMenuDeleteLoopDone startMenuDeleteLoop

    startMenuDeleteLoopDone:

    DeleteRegKey HKLM "${UNINSTALL_REGISTRY_KEY}"

SectionEnd

Function .onInit
    Push $R0

    ${GetParameters} $cmdLineParams
    ClearErrors

    Pop $R0

    StrCpy $Option_AllInOne 0

    Push $R0
    ${GetOptions} $cmdLineParams '/allinone' $R0
    IfErrors +2 0
    StrCpy $Option_AllInOne 1
    Pop $R0

    StrCmp $Option_AllInOne 1 AllInOneMode
    StrCmp $Option_AllInOne 0 NoAllInOneMode

    AllInOneMode:
        MessageBox MB_OK|MB_ICONINFORMATION "All In One"

    NoAllInOneMode:
    
    !insertmacro MUI_LANGDLL_DISPLAY

FunctionEnd
