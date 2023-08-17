# -*- coding: utf8 -*-

import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import simplejson as json
import AutoCompletion
from typing import List, Dict, Optional

ADDON = xbmcaddon.Addon()
ADDON_VERSION = ADDON.getAddonInfo('version')
KODI_VERSION_THRESHOLD = 17
BUSY_DIALOG = 'Dialog.Close(busydialog)'
BUSY_DIALOG_NOCANCEL = 'Dialog.Close(busydialognocancel)'
WINDOW_ID = 10103

def get_kodi_json(method, params):
    json_query = xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "%s", "params": %s, "id": 1}' % (method, json.dumps(params)))
    return json.loads(json_query)

def close_dialog():
    if int(xbmc.getInfoLabel('System.BuildVersion')[:2]) > KODI_VERSION_THRESHOLD:
        xbmc.sleep(50)
        xbmc.executebuiltin(BUSY_DIALOG_NOCANCEL)
    else:
        xbmc.sleep(50)
        xbmc.executebuiltin(BUSY_DIALOG)

def handle_autocomplete(params):
    return AutoCompletion.get_autocomplete_items(params["id"], params.get("limit", 10))

def handle_selectautocomplete(params):
    if params.get("handle"):
        xbmcplugin.setResolvedUrl(handle=int(params.get("handle")), succeeded=False, listitem=xbmcgui.ListItem())
    try:
        window = xbmcgui.Window(WINDOW_ID)
    except Exception:
        return None
    close_dialog()
    window.setFocusId(312)
    kodi_params = {
        "jsonrpc": "2.0",
        "method": "Input.SendText",
        "params": {"text": params.get("id"), "done": False},
        "id": 1
    }
    xbmc.executeJSONRPC(json.dumps(kodi_params))
    window.setFocusId(300)

def start_info_actions(infos, params):
    listitems = []
    for info in infos:
        if info == 'autocomplete':
            listitems = handle_autocomplete(params)
        elif info == 'selectautocomplete':
            handle_selectautocomplete(params)
        pass_list_to_skin(data=listitems, handle=params.get("handle", ""), limit=params.get("limit", 20))

def pass_list_to_skin(data: Optional[List[Dict]] = None, handle: Optional[int] = None, limit: Optional[int] = None) -> None:
    if data is None:
        data = []
    limit = int(limit) if limit else None
    if limit and len(data) > limit:
        data = data[:limit]
    if handle and data:
        items = create_listitems(data)
        xbmcplugin.addDirectoryItems(
            handle=handle,
            items=[(i.getProperty("path"), i, False) for i in items],
            totalItems=len(items)
        )
    xbmcplugin.endOfDirectory(handle)

def create_listitems(data: List[Dict]) -> List[xbmcgui.ListItem]:
    itemlist = []
    for count, result in enumerate(data):
        listitem = xbmcgui.ListItem(str(count))
        for key, value in result.items():
            if not value:
                continue
            if key.lower() in ["label"]:
                listitem.setLabel(str(value))
            elif key.lower() in ["search_string"]:
                path = f"plugin://plugin.program.autocompletion/?info=selectautocomplete&&id={value}"
                listitem.setPath(path=path)
                listitem.setProperty('path', path)
        listitem.setProperty("index", str(count))
        listitem.setProperty("isPlayable", "false")
        itemlist.append(listitem)
    return itemlist

if __name__ == "__main__":
    xbmc.log(f"version {ADDON_VERSION} started")
    args = sys.argv[2][1:]
    handle = int(sys.argv[1])
    infos = []
    params = {"handle": handle}
    delimiter = "&&"
    for arg in args.split(delimiter):
        param = arg.replace('"', '').replace("'", " ")
        if param.startswith('info='):
            infos.append(param[5:])
        else:
            try:
                params[param.split("=")[0].lower()] = "=".join(param.split("=")[1:]).strip()
            except Exception:
                pass
    if infos:
        start_info_actions(infos, params)
    xbmc.log('finished')
