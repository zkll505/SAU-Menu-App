from datetime import datetime, timedelta
import threading

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp


def parse_menu_text(text):
    if not text:
        return {}
    meals = {}
    current_meal = None

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if any(meal in line.lower() for meal in ['breakfast', 'lunch', 'supper']):
            current_meal = line.split(':')[0].strip()
            meals[current_meal] = []
        elif current_meal and line:
            meals[current_meal].append(line)

    return meals


def fetch_menus():
    """Network + parsing logic
    Returns (today_name, today_menu, tomorrow_name, tomorrow_menu, error)
    """
    url = "https://www.southern.edu/administration/food/index.html"
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        try:
            from zoneinfo import ZoneInfo
            eastern = ZoneInfo('US/Eastern')
            now = datetime.now(tz=eastern)
        except Exception:
            now = datetime.now()

        today_name = now.strftime('%A')
        tomorrow_name = (now + timedelta(days=1)).strftime('%A')

        day_details = {}
        for det in soup.find_all('details'):
            det_id = det.get('id')
            if det_id:
                name = str(det_id).strip().lower()
                day_details[name] = det

        def extract_menu_for(day_name):
            key = day_name.strip().lower()
            det = day_details.get(key)
            if not det:
                for d in soup.find_all('details'):
                    summary = d.find('summary')
                    if summary and summary.get_text(strip=True).lower() == key:
                        det = d
                        break
            if not det:
                return None
            content = det.find(attrs={'name': 'content'})
            if content:
                return content.get_text(separator='\n', strip=True)
            return det.get_text(separator='\n', strip=True)

        today_menu = parse_menu_text(extract_menu_for(today_name))
        tomorrow_menu = parse_menu_text(extract_menu_for(tomorrow_name))
        return today_name, today_menu, tomorrow_name, tomorrow_menu, None

    except Exception as e:
        return None, None, None, None, str(e)


class MenuColumn(BoxLayout):

    def __init__(self, title, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        self.title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(40),
            font_size=dp(18),
            bold=True,
        )
        self.add_widget(self.title_label)

        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(4), padding=dp(8))
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.add_widget(self.scroll)

    def display(self, menu_data, skip_breakfast=False):
        self.grid.clear_widgets()

        if not menu_data:
            self.grid.add_widget(Label(
                text="No menu available",
                size_hint_y=None,
                height=dp(30),
            ))
            return

        for meal, items in menu_data.items():
            if skip_breakfast and meal.lower() == "breakfast":
                continue

            self.grid.add_widget(Label(
                text=meal,
                size_hint_y=None,
                height=dp(32),
                font_size=dp(16),
                bold=True,
                halign='left',
                valign='middle',
            ))

            for item in items:
                lbl = Label(
                    text=f"\u2022 {item}",
                    size_hint_y=None,
                    height=dp(28),
                    font_size=dp(13),
                    halign='left',
                    valign='middle',
                )
                lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w, None)))
                self.grid.add_widget(lbl)


class MenuRootWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)

        columns = BoxLayout(orientation='horizontal', spacing=dp(8), padding=dp(8))
        self.today_col = MenuColumn("Today's Menu")
        self.tomorrow_col = MenuColumn("Tomorrow's Menu")
        columns.add_widget(self.today_col)
        columns.add_widget(self.tomorrow_col)
        self.add_widget(columns)

        self.refresh_btn = Button(
            text="Refresh Menus",
            size_hint_y=None,
            height=dp(48),
        )
        self.refresh_btn.bind(on_release=lambda *_: self.refresh_menus())
        self.add_widget(self.refresh_btn)

        Clock.schedule_once(lambda dt: self.refresh_menus(), 0.2)

    def refresh_menus(self):
        self.refresh_btn.disabled = True
        self.refresh_btn.text = "Loading..."

        def worker():
            today_name, today_menu, tomorrow_name, tomorrow_menu, error = fetch_menus()
            Clock.schedule_once(lambda dt: self._apply_result(
                today_name, today_menu, tomorrow_name, tomorrow_menu, error
            ))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_result(self, today_name, today_menu, tomorrow_name, tomorrow_menu, error):
        self.refresh_btn.disabled = False
        self.refresh_btn.text = "Refresh Menus"

        if error:
            popup = Popup(
                title="Error",
                content=Label(text=f"Failed to fetch menus:\n{error}"),
                size_hint=(0.8, 0.4),
            )
            popup.open()
            return

        self.today_col.title_label.text = f"Today's Menu ({today_name})"
        self.tomorrow_col.title_label.text = f"Tomorrow's Menu ({tomorrow_name})"

        # Same "skip breakfast for today" behavior as the desktop version
        self.today_col.display(today_menu, skip_breakfast=True)
        self.tomorrow_col.display(tomorrow_menu, skip_breakfast=False)


class SouthernMenuApp(App):
    def build(self):
        self.title = "Southern University Menu"
        return MenuRootWidget()


if __name__ == "__main__":
    SouthernMenuApp().run()
