# -*- coding: utf-8 -*-
import sys
import platform
import importlib
import os
import json
import re
import time
import socket
from collections import Counter
from datetime import datetime

import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
from resources.lib import xml_structure
from resources.providers import magenta_DE
from resources.providers import tvspielfilm_DE
from resources.providers import swisscom_CH
from resources.providers import horizon
from resources.providers import zattoo


ADDON = xbmcaddon.Addon(id="service.takealug.epg-grabber")
addon_name = ADDON.getAddonInfo("name")
addon_version = ADDON.getAddonInfo("version")
loc = ADDON.getLocalizedString
datapath = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
temppath = os.path.join(datapath, "temp")
thread_temppath = os.path.join(temppath, "multithread")
machine = platform.machine()


def str2bool(in_val: str) -> bool:
    """
    Takes a string and converts it to a boolean value
    """
    return in_val.lower() in ("y", "yes", "t", "true", "on", "1")


def getAddonConfig(setting: str) -> str:
    """
    Takes a configuration key and returns its value as string.
    """
    return xbmcaddon.Addon(id="service.takealug.epg-grabber").getSetting(setting)


def getAddonConfigBool(setting: str) -> bool:
    """
    Takes a configuration key and returns its value as boolean.
    """
    return str2bool(getAddonConfig(setting))


def getAddonConfigInt(setting: str) -> int:
    """
    Takes a configuration key and returns its value as int.
    """
    return int(getAddonConfig(setting))


## Read Global Settings
storage_path = getAddonConfig("storage_path")
auto_download = getAddonConfigBool("auto_download")
timeswitch_1 = getAddonConfigInt("timeswitch_1")
timeswitch_2 = getAddonConfigInt("timeswitch_2")
timeswitch_3 = getAddonConfigInt("timeswitch_3")
enable_rating_mapper = getAddonConfigBool("enable_rating_mapper")
use_local_sock = getAddonConfigBool("use_local_sock")
tvh_local_sock = getAddonConfig("tvh_local_sock")
download_threads = getAddonConfigInt("download_threads")
enable_multithread = getAddonConfigBool("enable_multithread")

## Get Enabled Grabbers
# Divers
enable_grabber_magentaDE = getAddonConfigBool("enable_grabber_magentaDE")
enable_grabber_tvsDE = getAddonConfigBool("enable_grabber_tvsDE")
enable_grabber_swcCH = getAddonConfigBool("enable_grabber_swcCH")

# Horizon
enable_grabber_hznDE = getAddonConfigBool("enable_grabber_hznDE")
enable_grabber_hznAT = getAddonConfigBool("enable_grabber_hznAT")
enable_grabber_hznCH = getAddonConfigBool("enable_grabber_hznCH")
enable_grabber_hznNL = getAddonConfigBool("enable_grabber_hznNL")
enable_grabber_hznPL = getAddonConfigBool("enable_grabber_hznPL")
enable_grabber_hznIE = getAddonConfigBool("enable_grabber_hznIE")
enable_grabber_hznGB = getAddonConfigBool("enable_grabber_hznGB")
enable_grabber_hznSK = getAddonConfigBool("enable_grabber_hznSK")
enable_grabber_hznCZ = getAddonConfigBool("enable_grabber_hznCZ")
enable_grabber_hznHU = getAddonConfigBool("enable_grabber_hznHU")
enable_grabber_hznRO = getAddonConfigBool("enable_grabber_hznRO")

# Zattoo
enable_grabber_zttDE = getAddonConfigBool("enable_grabber_zttDE")
enable_grabber_zttCH = getAddonConfigBool("enable_grabber_zttCH")
enable_grabber_1und1DE = getAddonConfigBool("enable_grabber_1und1DE")
enable_grabber_qlCH = getAddonConfigBool("enable_grabber_qlCH")
enable_grabber_mnetDE = getAddonConfigBool("enable_grabber_mnetDE")
enable_grabber_walyCH = getAddonConfigBool("enable_grabber_walyCH")
enable_grabber_mweltAT = getAddonConfigBool("enable_grabber_mweltAT")
enable_grabber_bbvDE = getAddonConfigBool("enable_grabber_bbvDE")
enable_grabber_vtxCH = getAddonConfigBool("enable_grabber_vtxCH")
enable_grabber_myvisCH = getAddonConfigBool("enable_grabber_myvisCH")
enable_grabber_gvisCH = getAddonConfigBool("enable_grabber_gvisCH")
enable_grabber_sakCH = getAddonConfigBool("enable_grabber_sakCH")
enable_grabber_nettvDE = getAddonConfigBool("enable_grabber_nettvDE")
enable_grabber_eweDE = getAddonConfigBool("enable_grabber_eweDE")
enable_grabber_qttvCH = getAddonConfigBool("enable_grabber_qttvCH")
enable_grabber_saltCH = getAddonConfigBool("enable_grabber_saltCH")
enable_grabber_swbDE = getAddonConfigBool("enable_grabber_swbDE")
enable_grabber_eirIE = getAddonConfigBool("enable_grabber_eirIE")

# Check if any Grabber is enabled
enabled_grabber = (
    enable_grabber_magentaDE
    or enable_grabber_tvsDE
    or enable_grabber_swcCH
    or enable_grabber_hznDE
    or enable_grabber_hznAT
    or enable_grabber_hznCH
    or enable_grabber_hznNL
    or enable_grabber_hznPL
    or enable_grabber_hznIE
    or enable_grabber_hznGB
    or enable_grabber_hznSK
    or enable_grabber_hznCZ
    or enable_grabber_hznHU
    or enable_grabber_hznRO
    or enable_grabber_zttDE
    or enable_grabber_zttCH
    or enable_grabber_1und1DE
    or enable_grabber_qlCH
    or enable_grabber_mnetDE
    or enable_grabber_walyCH
    or enable_grabber_mweltAT
    or enable_grabber_bbvDE
    or enable_grabber_vtxCH
    or enable_grabber_myvisCH
    or enable_grabber_gvisCH
    or enable_grabber_sakCH
    or enable_grabber_nettvDE
    or enable_grabber_eweDE
    or enable_grabber_qttvCH
    or enable_grabber_saltCH
    or enable_grabber_swbDE
    or enable_grabber_eirIE
)

guide_temp_path = os.path.join(datapath, "guide.xml")
guide_dest_path = os.path.join(storage_path, "guide.xml")
grabber_cron_path = os.path.join(datapath, "grabber_cron.json")
grabber_cron_temp_path = os.path.join(temppath, "grabber_cron.json")
xmltv_dtd_path = os.path.join(datapath, "xmltv.dtd")


def log(message: str, loglevel=xbmc.LOGDEBUG) -> None:
    """
    Takes a message and an optional `loglevel` option.
    Writes a string to Kodi's log file and the debug window.
    """
    xbmc.log("[{} {}] {}".format(addon_name, addon_version, message), loglevel)


## Make OSD Notify Messages
OSD = xbmcgui.Dialog()

## MAKE an Monitor
class Monitor(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)
        self.settingsChanged = False

    def onSettingsChanged(self):
        self.settingsChanged = True


monitor = Monitor()


def notify(title: str, message: str, icon=xbmcgui.NOTIFICATION_INFO) -> None:
    """
    Takes a title, message and an optional icon.
    Show a Notification alert.
    """
    OSD.notification(title, message, icon)


def copy_guide_to_destination():
    """
    Copies the guide file to its final destination.
    """
    if xbmcvfs.copy(guide_temp_path, guide_dest_path):
        try:
            ## Write new setting last_download
            with open(grabber_cron_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["last_download"] = str(int(time.time()))

            with open(grabber_cron_temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            ## rename temporary file replacing old file
            xbmcvfs.copy(grabber_cron_temp_path, grabber_cron_path)
            xbmc.sleep(3000)
            xbmcvfs.delete(grabber_cron_temp_path)
            notify(addon_name, loc(32350), icon=xbmcgui.NOTIFICATION_INFO)
            log(loc(32350), xbmc.LOGINFO)
        except:
            log(
                "Worker can´t read cron File, creating new File...".format(loc(32356)),
                xbmc.LOGERROR,
            )
            with open(grabber_cron_path, "w", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "last_download": str(int(time.time())),
                            "next_download": str(int(time.time()) + 86400),
                        }
                    )
                )
            notify(addon_name, loc(32350), icon=xbmcgui.NOTIFICATION_INFO)
            log(loc(32350), xbmc.LOGINFO)
    else:
        notify(addon_name, loc(32351), icon=xbmcgui.NOTIFICATION_ERROR)
        log(loc(32351), xbmc.LOGERROR)


def check_channel_dupes():
    with open(guide_temp_path, encoding="utf-8") as f:
        c = Counter(c.strip() for c in f if c.strip())  # for case-insensitive search
        dupe = []
        for line in c:
            if c[line] > 1:
                if "display-name" in line or "icon src" in line or "</channel" in line:
                    pass
                else:
                    dupe.append(line + "\n")
        dupes = "".join(dupe)

        if not dupes == "":
            log("{} {}".format(loc(32400), dupes), xbmc.LOGERROR)
            dialog = xbmcgui.Dialog()
            ok = dialog.ok("-]ERROR[- {}".format(loc(32400)), dupes)
            if ok:
                return False
            return False
        else:
            return True


def run_grabber():
    if check_startup():
        importlib.reload(xml_structure)
        importlib.reload(magenta_DE)
        importlib.reload(tvspielfilm_DE)
        importlib.reload(swisscom_CH)
        importlib.reload(horizon)
        importlib.reload(zattoo)
        xml_structure.xml_start()
        ## Check Provider , Create XML Channels
        if enable_grabber_magentaDE and magenta_DE.startup():
            magenta_DE.create_xml_channels()
        if enable_grabber_tvsDE and tvspielfilm_DE.startup():
            tvspielfilm_DE.create_xml_channels()
        if enable_grabber_swcCH and swisscom_CH.startup():
            swisscom_CH.create_xml_channels()
        if enable_grabber_hznDE and horizon.startup("de"):
            horizon.create_xml_channels("de")
        if enable_grabber_hznAT and horizon.startup("at"):
            horizon.create_xml_channels("at")
        if enable_grabber_hznCH and horizon.startup("ch"):
            horizon.create_xml_channels("ch")
        if enable_grabber_hznNL and horizon.startup("nl"):
            horizon.create_xml_channels("nl")
        if enable_grabber_hznPL and horizon.startup("pl"):
            horizon.create_xml_channels("pl")
        if enable_grabber_hznIE and horizon.startup("ie"):
            horizon.create_xml_channels("ie")
        if enable_grabber_hznGB and horizon.startup("gb"):
            horizon.create_xml_channels("gb")
        if enable_grabber_hznSK and horizon.startup("sk"):
            horizon.create_xml_channels("sk")
        if enable_grabber_hznCZ and horizon.startup("cz"):
            horizon.create_xml_channels("cz")
        if enable_grabber_hznHU and horizon.startup("hu"):
            horizon.create_xml_channels("hu")
        if enable_grabber_hznRO and horizon.startup("ro"):
            horizon.create_xml_channels("ro")
        if enable_grabber_zttDE and zattoo.startup("ztt_de"):
            zattoo.create_xml_channels("ztt_de")
        if enable_grabber_zttCH and zattoo.startup("ztt_ch"):
            zattoo.create_xml_channels("ztt_ch")
        if enable_grabber_1und1DE and zattoo.startup("1und1_de"):
            zattoo.create_xml_channels("1und1_de")
        if enable_grabber_qlCH and zattoo.startup("ql_ch"):
            zattoo.create_xml_channels("ql_ch")
        if enable_grabber_mnetDE and zattoo.startup("mnet_de"):
            zattoo.create_xml_channels("mnet_de")
        if enable_grabber_walyCH and zattoo.startup("walytv_ch"):
            zattoo.create_xml_channels("walytv_ch")
        if enable_grabber_mweltAT and zattoo.startup("meinewelt_at"):
            zattoo.create_xml_channels("meinewelt_at")
        if enable_grabber_bbvDE and zattoo.startup("bbtv_de"):
            zattoo.create_xml_channels("bbtv_de")
        if enable_grabber_vtxCH and zattoo.startup("vtxtv_ch"):
            zattoo.create_xml_channels("vtxtv_ch")
        if enable_grabber_myvisCH and zattoo.startup("myvision_ch"):
            zattoo.create_xml_channels("myvision_ch")
        if enable_grabber_gvisCH and zattoo.startup("glattvision_ch"):
            zattoo.create_xml_channels("glattvision_ch")
        if enable_grabber_sakCH and zattoo.startup("sak_ch"):
            zattoo.create_xml_channels("sak_ch")
        if enable_grabber_nettvDE and zattoo.startup("nettv_de"):
            zattoo.create_xml_channels("nettv_de")
        if enable_grabber_eweDE and zattoo.startup("tvoewe_de"):
            zattoo.create_xml_channels("tvoewe_de")
        if enable_grabber_qttvCH and zattoo.startup("quantum_ch"):
            zattoo.create_xml_channels("quantum_ch")
        if enable_grabber_saltCH and zattoo.startup("salt_ch"):
            zattoo.create_xml_channels("salt_ch")
        if enable_grabber_swbDE and zattoo.startup("tvoswe_de"):
            zattoo.create_xml_channels("tvoswe_de")
        if enable_grabber_eirIE and zattoo.startup("eir_ie"):
            zattoo.create_xml_channels("eir_ie")

        # Check for Channel Dupes
        if check_channel_dupes():

            ## Create XML Broadcast
            if enable_grabber_magentaDE and magenta_DE.startup():
                magenta_DE.create_xml_broadcast(
                    enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_tvsDE and tvspielfilm_DE.startup():
                tvspielfilm_DE.create_xml_broadcast(
                    enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_swcCH and swisscom_CH.startup():
                swisscom_CH.create_xml_broadcast(
                    enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_hznDE and horizon.startup("de"):
                horizon.create_xml_broadcast(
                    "de", enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_hznAT and horizon.startup("at"):
                horizon.create_xml_broadcast(
                    "at", enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_hznCH and horizon.startup("ch"):
                horizon.create_xml_broadcast(
                    "ch", enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_hznNL and horizon.startup("nl"):
                horizon.create_xml_broadcast(
                    "nl", enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_hznPL and horizon.startup("pl"):
                horizon.create_xml_broadcast(
                    "pl", enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_hznIE and horizon.startup("ie"):
                horizon.create_xml_broadcast(
                    "ie", enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_hznGB and horizon.startup("gb"):
                horizon.create_xml_broadcast(
                    "gb", enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_hznSK and horizon.startup("sk"):
                horizon.create_xml_broadcast(
                    "sk", enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_hznCZ and horizon.startup("cz"):
                horizon.create_xml_broadcast(
                    "cz", enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_hznHU and horizon.startup("hu"):
                horizon.create_xml_broadcast(
                    "hu", enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_hznRO and horizon.startup("ro"):
                horizon.create_xml_broadcast(
                    "ro", enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_zttDE and zattoo.startup("ztt_de"):
                zattoo.create_xml_broadcast(
                    "ztt_de",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_zttCH and zattoo.startup("ztt_ch"):
                zattoo.create_xml_broadcast(
                    "ztt_ch",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_1und1DE and zattoo.startup("1und1_de"):
                zattoo.create_xml_broadcast(
                    "1und1_de",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_qlCH and zattoo.startup("ql_ch"):
                zattoo.create_xml_broadcast(
                    "ql_ch", enable_rating_mapper, thread_temppath, download_threads
                )
            if enable_grabber_mnetDE and zattoo.startup("mnet_de"):
                zattoo.create_xml_broadcast(
                    "mnet_de",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_walyCH and zattoo.startup("walytv_ch"):
                zattoo.create_xml_broadcast(
                    "walytv_ch",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_mweltAT and zattoo.startup("meinewelt_at"):
                zattoo.create_xml_broadcast(
                    "meinewelt_at",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_bbvDE and zattoo.startup("bbtv_de"):
                zattoo.create_xml_broadcast(
                    "bbtv_de",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_vtxCH and zattoo.startup("vtxtv_ch"):
                zattoo.create_xml_broadcast(
                    "vtxtv_ch",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_myvisCH and zattoo.startup("myvision_ch"):
                zattoo.create_xml_broadcast(
                    "myvision_ch",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_gvisCH and zattoo.startup("glattvision_ch"):
                zattoo.create_xml_broadcast(
                    "glattvision_ch",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_sakCH and zattoo.startup("sak_ch"):
                zattoo.create_xml_broadcast(
                    "sak_ch",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_nettvDE and zattoo.startup("nettv_de"):
                zattoo.create_xml_broadcast(
                    "nettv_de",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_eweDE and zattoo.startup("tvoewe_de"):
                zattoo.create_xml_broadcast(
                    "tvoewe_de",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_qttvCH and zattoo.startup("quantum_ch"):
                zattoo.create_xml_broadcast(
                    "quantum_ch",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_saltCH and zattoo.startup("salt_ch"):
                zattoo.create_xml_broadcast(
                    "salt_ch",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_swbDE and zattoo.startup("tvoswe_de"):
                zattoo.create_xml_broadcast(
                    "tvoswe_de",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )
            if enable_grabber_eirIE and zattoo.startup("eir_ie"):
                zattoo.create_xml_broadcast(
                    "eir_ie",
                    enable_rating_mapper,
                    thread_temppath,
                    download_threads,
                )

            ## Finish XML
            xml_structure.xml_end()
            copy_guide_to_destination()

            ## Write Guide in TVH Socked
            if use_local_sock:
                write_to_sock()


def write_to_sock():
    """
    Write the generated guide file to the configured socket.
    """
    if check_startup():
        if use_local_sock and os.path.isfile(guide_temp_path):
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            epg = open(guide_temp_path, "rb")
            epg_data = epg.read()
            try:
                log("{} {}".format(loc(32380), tvh_local_sock), xbmc.LOGINFO)
                notify(addon_name, loc(32380), icon=xbmcgui.NOTIFICATION_INFO)
                sock.connect(tvh_local_sock)
                sock.sendall(epg_data)
                log("{} {}".format(sock.recv, tvh_local_sock), xbmc.LOGINFO)
            except socket.error as e:
                notify(
                    addon_name,
                    "{} {}".format(loc(32379), e),
                    icon=xbmcgui.NOTIFICATION_ERROR,
                )
                log("{} {}".format(loc(32379), e), xbmc.LOGERROR)
            finally:
                sock.close()
                epg.close()
        else:
            ok = dialog.ok(loc(32119), loc(32409))
            if ok:
                log(loc(32409), xbmc.LOGERROR)


def worker(trigger1_hour: int, trigger2_hour: int, trigger3_hour: int) -> None:
    """
    Takes three hour variables and downloads epg data if the current time matches.
    """
    initiate_download = False

    ## Read Settings for last / next_download
    try:
        with open(grabber_cron_path, "r", encoding="utf-8") as f:
            cron = json.load(f)
            next_download = cron["next_download"]
            last_download = cron["last_download"]
    except:
        log(
            "Worker can´t read cron File, creating new File...".format(loc(32356)),
            xbmc.LOGERROR,
        )
        with open(grabber_cron_path, "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "last_download": int(time.time()),
                        "next_download": int(time.time()) + 86400,
                    }
                )
            )
        with open(grabber_cron_path, "r", encoding="utf-8") as f:
            cron = json.load(f)
            next_download = cron["next_download"]
            last_download = cron["last_download"]

    log(
        "{} {}".format(
            loc(32352),
            datetime.fromtimestamp(last_download).strftime("%d.%m.%Y %H:%M"),
        ),
        xbmc.LOGDEBUG,
    )

    if next_download > last_download:
        log(
            "{} {}".format(
                loc(32353),
                datetime.fromtimestamp(int(next_download)).strftime("%d.%m.%Y %H:%M"),
            ),
            xbmc.LOGDEBUG,
        )

    if next_download < int(time.time()):
        # suggested download time has passed (e.g. system was offline) or time is now, download epg
        # and set a new timestamp for the next download
        log(
            "{} {}".format(
                loc(32352),
                datetime.fromtimestamp(last_download).strftime("%d.%m.%Y %H:%M"),
            ),
            xbmc.LOGINFO,
        )
        log(
            "{} {}".format(
                loc(32353),
                datetime.fromtimestamp(next_download).strftime("%d.%m.%Y %H:%M"),
            ),
            xbmc.LOGINFO,
        )
        log("{}".format(loc(32356)), xbmc.LOGINFO)
        initiate_download = True

    ## If next_download < last_download, initiate an Autodownload
    if initiate_download:
        notify(addon_name, loc(32357), icon=xbmcgui.NOTIFICATION_INFO)
        run_grabber()
        ## Update Cron Settings
        with open(grabber_cron_path, "r", encoding="utf-8") as f:
            cron = json.load(f)
            next_download = cron["next_download"]
            last_download = cron["last_download"]

    ## Calculate the next_download Setting

    # get Settings for daily_1, daily_2, daily_3
    today = datetime.today()
    now = int(time.time())
    calc_daily_1 = datetime(
        today.year, today.month, day=today.day, hour=trigger1_hour, minute=0, second=0
    )
    calc_daily_2 = datetime(
        today.year, today.month, day=today.day, hour=trigger2_hour, minute=0, second=0
    )
    calc_daily_3 = datetime(
        today.year, today.month, day=today.day, hour=trigger3_hour, minute=0, second=0
    )

    try:
        daily_1 = int(calc_daily_1.strftime("%s"))
        daily_2 = int(calc_daily_2.strftime("%s"))
        daily_3 = int(calc_daily_3.strftime("%s"))
    except ValueError:
        daily_1 = int(time.mktime(calc_daily_1.timetuple()))
        daily_2 = int(time.mktime(calc_daily_2.timetuple()))
        daily_3 = int(time.mktime(calc_daily_3.timetuple()))

    ## If sheduleplan for daily 1,2,3 is in the past, plan it for next day
    if daily_1 <= now:
        daily_1 += 86400
    if daily_2 <= now:
        daily_2 += 86400
    if daily_3 <= now:
        daily_3 += 86400

    ## Find the lowest Integer for next download
    next_download = min([int(daily_1), int(daily_2), int(daily_3)])

    ## Write new setting next_download
    with open(grabber_cron_path, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "last_download": last_download,
                    "next_download": next_download,
                }
            )
        )


def check_internet(host: str = "8.8.8.8", port: int = 53, timeout: float = 3.0) -> bool:
    """
    Takes optional arguments `host`, `port` and `timeout` and checks if
    a connection can be established.
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
    except socket.error as ex:
        return False
    return True


def check_startup() -> bool:
    """
    Check if everything is setup correctly.
    """
    # Create Tempfolder if not exist
    if not os.path.exists(temppath):
        os.makedirs(temppath)
    if not os.path.exists(thread_temppath):
        os.makedirs(thread_temppath)

    if storage_path == "choose":
        notify(addon_name, loc(32359), icon=xbmcgui.NOTIFICATION_ERROR)
        log(loc(32359), xbmc.LOGERROR)
        return False

    if not enabled_grabber:
        notify(addon_name, loc(32360), icon=xbmcgui.NOTIFICATION_ERROR)
        log(loc(32360), xbmc.LOGERROR)
        return False

    if use_local_sock:
        socked_string = ".sock"
        if not re.search(socked_string, tvh_local_sock):
            notify(addon_name, loc(32378), icon=xbmcgui.NOTIFICATION_ERROR)
            log(loc(32378), xbmc.LOGERROR)
            return False

    # if enable_multithread:
    # if (not machine == 'x86_64' and not machine == 'armv7l' and not machine == 'armv8l'):
    # log(machine, xbmc.LOGERROR)
    # dialog = xbmcgui.Dialog()
    # log(loc(32381), xbmc.LOGERROR)
    # ok = dialog.ok(addon_name, loc(32381))
    # if ok:
    # return False
    # return False

    if enable_multithread:
        log(machine, xbmc.LOGERROR)
        dialog = xbmcgui.Dialog()
        log(
            "Multithreading is currently under Kodi 19 broken, please disable it",
            xbmc.LOGERROR,
        )
        ok = dialog.ok(
            addon_name,
            "Multithreading is currently under Kodi 19 broken, please disable it",
        )
        return not ok

    ## create Crontab File which not exists at first time
    if not os.path.isfile(grabber_cron_path) or os.stat(grabber_cron_path).st_size <= 1:
        with open(grabber_cron_path, "w", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "last_download": int(time.time()),
                        "next_download": int(time.time()) + 86400,
                    }
                )
            )

    ## Clean Tempfiles
    for file in os.listdir(temppath):
        xbmcvfs.delete(os.path.join(temppath, file))

    ## Check internet Connection
    if not check_internet():
        retries = 12
        while retries > 0:
            log(loc(32385), xbmc.LOGINFO)
            notify(addon_name, loc(32385), icon=xbmcgui.NOTIFICATION_INFO)
            xbmc.sleep(5000)
            if check_internet():
                log(loc(32386), xbmc.LOGINFO)
                notify(addon_name, loc(32386), icon=xbmcgui.NOTIFICATION_INFO)
                return True
            else:
                retries -= 1
        if retries == 0:
            log(loc(32387), xbmc.LOGERROR)
            notify(addon_name, loc(32387), icon=xbmcgui.NOTIFICATION_ERROR)
            return False
    return True


if __name__ == "__main__":
    if check_startup():
        try:
            dialog = xbmcgui.Dialog()
            if sys.argv[1] == "manual_download":
                if not auto_download:
                    # TODO: Check why manual download is disabled when auto_download is enabled.
                    ret = dialog.yesno("Takealug EPG Grabber", loc(32401))
                    if ret:
                        notify(addon_name, loc(32376), icon=xbmcgui.NOTIFICATION_INFO)
                        run_grabber()
                elif auto_download:
                    _ = dialog.ok(addon_name, loc(32414))
            if sys.argv[1] == "write_to_sock":
                ret = dialog.yesno(loc(32119), loc(32408))
                if ret:
                    write_to_sock()

        except IndexError:
            while not monitor.waitForAbort(30):
                if monitor.settingsChanged:
                    log("Settings changed Reloading", xbmc.LOGINFO)
                    auto_download = getAddonConfigBool("auto_download")
                    if auto_download:
                        timeswitch_1 = getAddonConfigInt("timeswitch_1")
                        timeswitch_2 = getAddonConfigInt("timeswitch_2")
                        timeswitch_3 = getAddonConfigInt("timeswitch_3")
                    monitor.settingsChanged = False
                if auto_download:
                    worker(timeswitch_1, timeswitch_2, timeswitch_3)
