# Autogenerated file
def render(*a, **d):
    yield """<!DOCTYPE html> <html lang=en > <title>Vilmio converter</title> <link rel=icon  href=\"main/static/favicon.png\"> <meta charset=UTF-8 /> <meta name=viewport  content=\"width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no\"/> <link href=\"main/static/style.css\" rel=stylesheet /> <script type=\"application/javascript\" src=\"main/static/func.js\"></script> <body onload=\"loadSettings()\"> <div class=header > <h1 style=\"color: #fff;\">RS485/TCP converter</h1> </div> <div id=loader  class=loader > <div class=loader-inner > <div class=\"lds-roller mb-3\"> <div></div> <div></div> <div></div> <div></div> <div></div> <div></div> <div></div> <div></div> </div> <h4 id=Lw >Loading</h4> </div> </div> <div class=settings-holder > <div class=flex > <div class=col > <p>FIRMWARE VERSION</p> </div> <div class=vl ></div> <div class=col > <p id=ACTUAL_SW_VERSION ></p> </div> </div> <hr> <div class=flex > <div class=col > <p>ERRORS</p> </div> <div class=vl ></div> <div class=col > <p id=ERRORS ></p> </div> </div> <hr> <div class=flex > <div class=col > <p>ID</p> </div> <div class=vl ></div> <div class=col > <p id=ID ></p> </div> </div> <hr> <div class=flex > <div class=col > <p>RESET CONVERTER</p> </div> <div class=vl ></div> <div class=col > <button class=btn  onclick=\"resetClick()\" type=button  id=RESET_BTN >RESET</button> </div> </div> <hr> <div class=flex > <div class=col > <p>AUTOMATIC UPDATE</p> </div> <div class=vl ></div> <div class=col > <label for=AUTOMATIC_UPDATE ></label> <input onchange=\"automaticUpdateChanged(this)\" id=AUTOMATIC_UPDATE  type=checkbox > </div> </div> <hr> <div class=flex > <div class=col > <p>INVERTER</p> </div> <div class=vl ></div> <div class=col > <label for=inverter_select ></label> <select class=btn  id=inverter_select  > <option value=1 >Sofar <option value=2 >Deye </select> </div> </div> <hr> <div class=flex > <div class=col > <p>SAVE INVERTER</p> </div> <div class=vl ></div> <div class=col > <button class=btn  onclick=\"saveInverterClick()\" type=button  id=save_inverter >SAVE</button> </div> </div> <hr> <div class=flex > <div class=col > <p>CONNECTED WIFI</p> </div> <div class=vl ></div> <div class=col > <p id=SSID ></p> </div> </div> <hr> <div class=flex > <div class=col > <p>NEW WIFI SSID</p> </div> <div class=vl ></div> <div class=col > <label for=wifiSELECT ></label> <select class=btn  id=wifiSELECT ></select> </div> </div> <hr> <div class=flex > <div class=col > <p>NEW WIFI PASSWORD</p> </div> <div class=vl ></div> <div class=col > <label for=wifiPWD ></label> <input class=btn  id=wifiPWD  type=password  value=\"\"> <label for=showPassword ></label> <input type=checkbox  id=showPassword  onclick=\"togglePasswordVisibility()\"> </div> </div> <hr> <div class=flex > <div class=col > <p>SAVE WIFI</p> </div> <div class=vl ></div> <div class=col > <button class=btn  onclick=\"saveWifiClick()\" type=button >SAVE</button> </div> </div> <hr> <div class=flex > <div class=col > <p>REFRESH WIFI</p> </div> <div class=vl ></div> <div class=col > <button class=btn  onclick=\"refreshWifiClick()\" type=button >REFRESH</button> </div> </div> </div> <div style=\"text-align: center; margin-bottom: 50px;\"> <button class=\"btn orange\" style=\"height:30px; background-color: #ff5c20ff\" onclick=\"refreshPage()\" type=button >REFRESH PAGE</button> </div> <div class=footer > </div>"""
