import logging
import objc
import requests
import threading
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo
from AppKit import (NSApplication, NSStatusBar, NSVariableStatusItemLength,
                    NSMenu, NSMenuItem, NSTimer, NSObject, NSApp,
                    NSApplicationActivationPolicyProhibited, NSFont,
                    NSAttributedString, NSSound)
from PyObjCTools import AppHelper

from premium_fetch import fetch_premium
from resources import load_sessions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PREMIUM_ALERT_THRESHOLD_PCT = 0.1
UI_UPDATE_INTERVAL_SEC = 60.0
PROGRESS_BAR_WIDTH = 10


class CryptoMasterSessionsApp(NSObject):
    def init(self):
        self = objc.super(CryptoMasterSessionsApp, self).init()
        if self is None:
            return None
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        self.last_active_count = 0
        self._http_session: requests.Session = requests.Session()
        self._fetch_generation = 0

        self.sessions = load_sessions()

        return self

    def applicationDidFinishLaunching_(self, notification):
        NSApp.setActivationPolicy_(NSApplicationActivationPolicyProhibited)
        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            UI_UPDATE_INTERVAL_SEC, self, "updateUI:", None, True
        )
        self.updateUI_(None)

    def _fetch_premium_in_background(self, generation: int) -> None:
        """Fetch premium data in background; refresh UI only if generation is still current."""
        try:
            btc = fetch_premium("BTC", self._http_session)
            eth = fetch_premium("ETH", self._http_session)
        except Exception as e:
            logger.warning("Premium fetch failed: %s", e)
            btc, eth = (None, 0.0, 0.0), (None, 0.0, 0.0)
        AppHelper.callAfter(self._apply_premium_if_current, generation, btc, eth)

    @objc.python_method
    def _apply_premium_if_current(self, generation: int, btc, eth) -> None:
        if generation != self._fetch_generation:
            logger.debug(
                "Stale premium fetch ignored (gen %s, current %s)",
                generation,
                self._fetch_generation,
            )
            return
        self._applyPremiumAndRefreshMenu_(btc, eth)

    @objc.python_method
    def get_progress_bar(self, current: float, start: float, end: float) -> str:
        width = PROGRESS_BAR_WIDTH
        if end < start:  # Midnight wrap logic (CME)
            total = (24 - start) + end
            prog_val = (current - start) if current >= start else (24 - start + current)
        else:
            total = end - start
            prog_val = current - start
        
        if total <= 0:
            return ""
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
            if diff < 0:
                diff += 1440
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
    def _format_price(self, price):
        """Format price for display (e.g. 97234.5 -> '97,234.50')."""
        if price is None:
            return "—"
        return f"{price:,.2f}"

    @objc.python_method
    def _buildAndSetMenuWithPremium_(self, premium_btc=None, premium_eth=None):
        """Build status menu and set it. premium_btc/premium_eth are (price, amount, pct) or None (no network)."""
        active_codes = []
        upcoming = []
        new_menu = NSMenu.alloc().init()
        
        # First two lines: current BTC and ETH prices
        price_btc = premium_btc[0] if premium_btc is not None else None
        price_eth = premium_eth[0] if premium_eth is not None else None
        new_menu.addItem_(self.create_menu_item(f"BTC  ${self._format_price(price_btc)}", is_active=True))
        new_menu.addItem_(self.create_menu_item(f"ETH  ${self._format_price(price_eth)}", is_active=True))
        
        now_local = datetime.now()
        
        # Gap Risk: visible Sat, Sun, and Mon until 10:00 local time
        show_gap_risk = (now_local.weekday() >= 5) or (now_local.weekday() == 0 and now_local.hour < 10)

        # Block before exchanges: trading hours section
        new_menu.addItem_(NSMenuItem.separatorItem())
        new_menu.addItem_(self.create_menu_item("🕐 Exchange trading hours", is_active=False))
        new_menu.addItem_(NSMenuItem.separatorItem())

        for s in self.sessions:
            try:
                tz = ZoneInfo(s["tz"])
                now = datetime.now(tz)
                curr_f = now.hour + now.minute / 60.0
                
                if s.get("venue") == "cme":
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
                
                if is_active:
                    active_codes.append(f"{s['icon']} {s['id']}")
                else:
                    upcoming.append((diff, s['id']))
                
                menu_title = f"{s['mkt']} {s['icon']} {now.strftime('%H:%M')} » {status_str}"
                new_menu.addItem_(self.create_menu_item(menu_title, is_active=is_active))
            except (KeyError, ValueError) as e:
                logger.warning("Skipping invalid session row: %s", e)

        if show_gap_risk:
            new_menu.addItem_(NSMenuItem.separatorItem())
            new_menu.addItem_(self.create_menu_item("⚠️ !!! CME GAP RISK ACTIVE !!! ⚠️", is_alert=True))

        # Block after exchanges: CPI section (same structure as above)
        new_menu.addItem_(NSMenuItem.separatorItem())
        new_menu.addItem_(self.create_menu_item("📊 US CPI", is_active=False))
        new_menu.addItem_(NSMenuItem.separatorItem())

        if len(active_codes) > self.last_active_count:
            NSSound.soundNamed_("Glass").play()
        self.last_active_count = len(active_codes)

        # Use passed-in premium data (from background fetch) or skip row
        premium_alert_played = False
        if premium_btc is not None:
            _, premium_amount_btc, premium_percentage_btc = premium_btc
            if abs(premium_percentage_btc) >= PREMIUM_ALERT_THRESHOLD_PCT and not premium_alert_played:
                NSSound.soundNamed_("Basso").play()
                premium_alert_played = True
            if premium_amount_btc != 0 or premium_percentage_btc != 0:
                color = "🟢" if premium_amount_btc > 0 else "🔴"
                premium_str = f"BTC Prem: {color} {premium_amount_btc:.4f} ({premium_percentage_btc:.2f}%)"
                new_menu.addItem_(self.create_menu_item(premium_str, is_active=True))

        if premium_eth is not None:
            _, premium_amount_eth, premium_percentage_eth = premium_eth
            if abs(premium_percentage_eth) >= PREMIUM_ALERT_THRESHOLD_PCT and not premium_alert_played:
                NSSound.soundNamed_("Basso").play()
                premium_alert_played = True
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

    @objc.python_method
    def _applyPremiumAndRefreshMenu_(self, premium_btc, premium_eth):
        """Called on main thread after background fetch; refreshes menu with premium data."""
        self._buildAndSetMenuWithPremium_(premium_btc, premium_eth)

    def updateUI_(self, _):
        # Build menu immediately without network (sessions only); UI stays responsive
        self._buildAndSetMenuWithPremium_(None, None)
        self._fetch_generation += 1
        gen = self._fetch_generation
        threading.Thread(
            target=lambda: self._fetch_premium_in_background(gen),
            daemon=True,
        ).start()

    @objc.typedSelector(b"v@:@")
    def dummyAction_(self, _): pass

    @objc.typedSelector(b"v@:@")
    def terminateApp_(self, _: Any) -> None:
        NSApp.terminate_(self)

if __name__ == "__main__":
    app = NSApplication.sharedApplication()
    delegate = CryptoMasterSessionsApp.alloc().init()
    app.setDelegate_(delegate)
    AppHelper.runEventLoop()
    