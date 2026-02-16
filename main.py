import os
import objc
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from AppKit import (NSApplication, NSStatusBar, NSVariableStatusItemLength, 
                    NSMenu, NSMenuItem, NSTimer, NSObject, NSApp,
                    NSApplicationActivationPolicyProhibited, NSFont, 
                    NSAttributedString, NSSound)
from PyObjCTools import AppHelper

class CryptoMasterSessionsApp(NSObject):
    def init(self):
        self = objc.super(CryptoMasterSessionsApp, self).init()
        if self is None: return None
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        self.last_active_count = 0
        
        # Session Configuration
        self.sessions = [
            {"id": "HKG", "mkt": "HKEX ", "type": "MAIN", "tz": "Asia/Hong_Kong", "open": 9, "close": 18, "icon": "🏮"},
            {"id": "FRA", "mkt": "XETRA", "type": "MAIN", "tz": "Europe/Berlin", "open": 9, "close": 17.5, "icon": "🇩🇪"},
            {"id": "LDN", "mkt": "LSE  ", "type": "MAIN", "tz": "Europe/London", "open": 8, "close": 16, "icon": "🔵"},
            {"id": "NYC", "mkt": "NYSE ", "type": "PRE ", "tz": "America/New_York", "open": 4, "close": 9.5, "icon": "🌤️"},
            {"id": "NYC", "mkt": "NYSE ", "type": "MAIN", "tz": "America/New_York", "open": 9.5, "close": 16, "icon": "🗽"},
            {"id": "CHI", "mkt": "CME  ", "type": "CME ", "tz": "America/Chicago", "open": 17, "close": 16, "icon": "📊"} 
        ]
        return self

    def applicationDidFinishLaunching_(self, notification):
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyProhibited)
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            60.0, self, "updateUI:", None, True
        )
        self.updateUI_(None)

    @objc.python_method
    def get_progress_bar(self, current, start, end):
        width = 10
        if end < start: # Midnight wrap logic (CME)
            total = (24 - start) + end
            prog_val = (current - start) if current >= start else (24 - start + current)
        else:
            total = end - start
            prog_val = current - start
        
        if total <= 0: return ""
        progress = int((prog_val / total) * width)
        progress = max(0, min(width, progress))
        return f"[{'▬' * progress}{' ' * (width - progress)}]"

    @objc.python_method
    def get_time_diff_minutes(self, now, target_hour, is_weekend_override=False):
        current_total = now.hour * 60 + now.minute
        target_total = int(target_hour * 60)
        if is_weekend_override:
            days_to_mon = 7 - now.weekday()
            diff = (1440 - current_total) + ((days_to_mon - 1) * 1440) + target_total
        else:
            diff = target_total - current_total
            if diff < 0: diff += 1440
        return diff

    @objc.python_method
    def create_menu_item(self, title, is_alert=False, is_active=False):
        action = "dummyAction:" if (is_alert or is_active) else None
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, "")
        if action:
            item.setTarget_(self)
            item.setEnabled_(True)
        
        font_name = "Menlo-Bold" if (is_alert or is_active) else "Menlo"
        font = NSFont.fontWithName_size_(font_name, 14.0)
        attr_title = NSAttributedString.alloc().initWithString_attributes_(title, {"NSFont": font})
        item.setAttributedTitle_(attr_title)
        return item

    @objc.python_method
    def calculate_premium_btc(self):
        try:
            cb_res = requests.get("https://api.exchange.coinbase.com/products/BTC-USD/ticker", timeout=5).json()
            price_cb = float(cb_res['price'])

            bn_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5).json()
            price_bn = float(bn_res['price'])

            premium_amount = price_cb - price_bn
            premium_percentage = ((premium_amount) / price_bn) * 100
            
            # Sound alert when deviation is 0.1% or more
            if abs(premium_percentage) >= 0.1:
                NSSound.soundNamed_("Basso").play()
                
            return premium_amount, premium_percentage
        except (requests.RequestException, KeyError, ValueError):
            return 0, 0

    @objc.python_method
    def calculate_premium_eth(self):
        try:
            cb_res = requests.get("https://api.exchange.coinbase.com/products/ETH-USD/ticker", timeout=5).json()
            price_cb = float(cb_res['price'])

            bn_res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=5).json()
            price_bn = float(bn_res['price'])

            premium_amount = price_cb - price_bn
            premium_percentage = ((premium_amount) / price_bn) * 100
            
            # Sound alert when deviation is 0.1% or more
            if abs(premium_percentage) >= 0.1:
                NSSound.soundNamed_("Basso").play()
                
            return premium_amount, premium_percentage
        except (requests.RequestException, KeyError, ValueError):
            return 0, 0

    def updateUI_(self, _):
        active_codes = []
        upcoming = []
        new_menu = NSMenu.alloc().init()
        
        now_local = datetime.now()
        
        # Gap Risk: visible Sat, Sun, and Mon until 10:00 local time
        show_gap_risk = (now_local.weekday() >= 5) or (now_local.weekday() == 0 and now_local.hour < 10)

        for s in self.sessions:
            try:
                tz = ZoneInfo(s["tz"])
                now = datetime.now(tz)
                curr_f = now.hour + now.minute / 60.0
                
                if s["icon"] == "📊": # CME Special Logic
                    is_cme_closed = (now.weekday() == 4 and now.hour >= 16) or \
                                    (now.weekday() == 5) or \
                                    (now.weekday() == 6 and now.hour < 17)
                    is_active = not is_cme_closed and now.hour != 16
                    diff = self.get_time_diff_minutes(now, 16 if is_active else 17)
                    prog = self.get_progress_bar(curr_f, 17, 16) if is_active else ""
                    
                    if is_active:
                        status_lbl = "ACT"
                    elif is_cme_closed:
                        status_lbl = "WKND"
                    else:
                        status_lbl = "OPEN"
                else:
                    is_wknd = now.weekday() >= 5
                    is_active = (s["open"] <= curr_f < s["close"]) and not is_wknd
                    diff = self.get_time_diff_minutes(now, s['close'] if is_active else s['open'], is_wknd)
                    prog = self.get_progress_bar(curr_f, s['open'], s['close']) if is_active else ""
                    
                    if is_active:
                        status_lbl = "ACT"
                    elif is_wknd:
                        status_lbl = "WKND"
                    elif curr_f < s["open"]:
                        status_lbl = "OPEN"
                    else:
                        status_lbl = "CLSD"

                status_str = f"{status_lbl} {prog}" if is_active else f"{status_lbl} in {diff//60:02d}h {diff%60:02d}m"
                
                if is_active: active_codes.append(f"{s['icon']} {s['id']}")
                else: upcoming.append((diff, s['id']))
                
                menu_title = f"{s['mkt']} {s['icon']} {now.strftime('%H:%M')} » {status_str}"
                new_menu.addItem_(self.create_menu_item(menu_title, is_active=is_active))
            except (KeyError, ValueError):
                # Skip invalid session configuration
                pass

        if show_gap_risk:
            new_menu.addItem_(NSMenuItem.separatorItem())
            new_menu.addItem_(self.create_menu_item("⚠️ !!! CME GAP RISK ACTIVE !!! ⚠️", is_alert=True))

        if len(active_codes) > self.last_active_count:
            NSSound.soundNamed_("Glass").play()
        self.last_active_count = len(active_codes)

        premium_amount_btc, premium_percentage_btc = self.calculate_premium_btc()
        premium_amount_eth, premium_percentage_eth = self.calculate_premium_eth()
        
        # Display BTC premium if available
        if premium_amount_btc != 0 or premium_percentage_btc != 0:
            color = "🟢" if premium_amount_btc > 0 else "🔴"
            premium_str = f"BTC Prem: {color} {premium_amount_btc:.4f} ({premium_percentage_btc:.2f}%)"
            new_menu.addItem_(self.create_menu_item(premium_str, is_active=True))

        # Display ETH premium if available
        if premium_amount_eth != 0 or premium_percentage_eth != 0:
            color = "🟢" if premium_amount_eth > 0 else "🔴"
            premium_str = f"ETH Prem: {color} {premium_amount_eth:.4f} ({premium_percentage_eth:.2f}%)"
            new_menu.addItem_(self.create_menu_item(premium_str, is_active=True))

        new_menu.addItem_(NSMenuItem.separatorItem())
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit App", "terminateApp:", "q")
        quit_item.setTarget_(self)
        new_menu.addItem_(quit_item)
        self.status_item.setMenu_(new_menu)
        
        if active_codes:
            prefix = "🔥 " if len(active_codes) >= 3 else ""
            self.status_item.button().setTitle_(f"{prefix}{' '.join(active_codes)}")
        else:
            if upcoming:
                upcoming.sort()
                next_m, next_id = upcoming[0]
                self.status_item.button().setTitle_(f"💤 {next_id}: {next_m//60}h {next_m%60}m")
            else:
                self.status_item.button().setTitle_("💤 No sessions")

    @objc.typedSelector(b"v@:@")
    def dummyAction_(self, _): pass

    @objc.typedSelector(b"v@:@")
    def terminateApp_(self, _): os._exit(0)

if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    delegate = CryptoMasterSessionsApp.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()
    