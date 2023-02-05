from os import getenv


#def list_admins():
    #data = getenv('admins', '')
    #return data.split(',')

import locale
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
from pytils import dt

from abc import ABC
from calendar import monthcalendar
from datetime import date, datetime, timedelta
from time import mktime
from typing import List, Callable, Union, Awaitable, TypedDict, Optional

from aiogram.types import InlineKeyboardButton, CallbackQuery

from aiogram_dialog.context.events import ChatEvent
from aiogram_dialog.manager.protocols import DialogManager,ManagedDialogProto
from aiogram_dialog.widgets.widget_event import WidgetEventProcessor, ensure_event_processor
#from .base import Keyboard
from aiogram_dialog.widgets.kbd.base import Keyboard
#from ..managed import ManagedWidgetAdapter
from aiogram_dialog.widgets.managed import ManagedWidgetAdapter
#from ...deprecation_utils import manager_deprecated

from typing import Optional, Any
import warnings
import pytils

def manager_deprecated(manager: Optional[Any]):
    if manager is not None:
        warnings.warn(
            "Passing `DialogManager` instance directly is deprecated"
            " and will be removed in aiogram_dialog==2.0",
            DeprecationWarning,
            stacklevel=3,
        )

OnDateSelected = Callable[[ChatEvent, "ManagedCalendarAdapter", DialogManager, datetime], Awaitable]

# Constants for managing widget rendering scope
SCOPE_MINUTES = "SCOPE_MINUTES"
SCOPE_HOURS = "SCOPE_HOURS"
SCOPE_DAYS = "SCOPE_DAYS"
SCOPE_MONTHS = "SCOPE_MONTHS"
SCOPE_YEARS = "SCOPE_YEARS"

# Constants for scrolling months
MONTH_NEXT = "+"
MONTH_PREV = "-"

# Constants for prefixing month and year values
PREFIX_MINUTE = "MINUTE"
PREFIX_HOUR = "HOUR"
PREFIX_DAY = "DAY"
PREFIX_MONTH = "MONTH"
PREFIX_YEAR = "YEAR"

MONTHS_NUMBERS = [(1, 2, 3), (4, 5, 6), (7, 8, 9), (10, 11, 12)]


class CalendarData(TypedDict):
    current_scope: str
    current_offset: str


class Calendar(Keyboard, ABC):
    def __init__(self,
                 id: str,
                 on_click: Union[OnDateSelected, WidgetEventProcessor, None] = None,
                 when: Union[str, Callable] = None):
        super().__init__(id, when)
        self.on_click = ensure_event_processor(on_click)

    async def _render_keyboard(self,
                              data,
                              manager: DialogManager) -> List[List[InlineKeyboardButton]]:
        offset = self.get_offset(manager)
        current_scope = self.get_scope(manager)

        if current_scope == SCOPE_MINUTES:
            return self.minutes_kbd(offset)
        elif current_scope == SCOPE_HOURS:
            return self.hours_kbd(offset)
        elif current_scope == SCOPE_DAYS:
            return self.days_kbd(offset)
        elif current_scope == SCOPE_MONTHS:
            return self.months_kbd(offset)
        elif current_scope == SCOPE_YEARS:
            return self.years_kbd(offset)

    async def process_callback(self,
                               c: CallbackQuery,
                               dialog: ManagedDialogProto,
                               manager: DialogManager) -> bool:
        prefix = f"{self.widget_id}:"
        if not c.data.startswith(prefix):
            return False
        current_offset = self.get_offset(manager)
        data = c.data[len(prefix):]
        if data == 'wrong_date':
            print('wrong date')
            await c.answer('Это в прошлом!', show_alert = True)
            return

        if data == MONTH_NEXT:
            new_offset = current_offset.replace(
                year=current_offset.year + (current_offset.month // 12),
                month=((current_offset.month % 12) + 1),
                day = 1,
            )
            self.set_offset(new_offset, manager)

        elif data == MONTH_PREV:
            if current_offset.month == 1:
                new_offset = current_offset.replace(year = current_offset.year - 1, month = 12, day = 1)
                self.set_offset(new_offset, manager)
            else:
                new_offset = current_offset.replace(month = (current_offset.month - 1), day = 1)
                self.set_offset(new_offset, manager)

        elif data in [SCOPE_MINUTES, SCOPE_HOURS, SCOPE_DAYS, SCOPE_MONTHS, SCOPE_YEARS]:
            self.set_scope(data, manager)

        elif data.startswith(PREFIX_MINUTE):
            data = int(c.data[len(prefix) + len(PREFIX_MINUTE):])
            new_offset = current_offset.replace(minute = data)
            await self.on_click.process_event(
                c, self.managed(manager), manager,
                new_offset,
            )
            self.set_scope(SCOPE_DAYS, manager)
            self.set_offset(new_offset, manager)
            return

        elif data.startswith(PREFIX_HOUR):
            data = int(c.data[len(prefix) + len(PREFIX_HOUR):])
            new_offset = current_offset.replace(hour = data)
            self.set_scope(SCOPE_MINUTES, manager)
            self.set_offset(new_offset, manager)

        elif data.startswith(PREFIX_DAY):
            data = int(c.data[len(prefix) + len(PREFIX_DAY):])
            new_offset = current_offset.replace(day = data)
            self.set_scope(SCOPE_HOURS, manager)
            self.set_offset(new_offset, manager)

        elif data.startswith(PREFIX_MONTH):
            data = int(c.data[len(prefix) + len(PREFIX_MONTH):])
            new_offset = current_offset.replace(month = data)
            self.set_scope(SCOPE_DAYS, manager)
            self.set_offset(new_offset, manager)

        elif data.startswith(PREFIX_YEAR):
            data = int(c.data[len(prefix) + len(PREFIX_YEAR):])
            new_offset = current_offset.replace(year = data)
            self.set_scope(SCOPE_MONTHS, manager)
            self.set_offset(new_offset, manager)

        #else:
            #raw_date = int(data)
            #await self.on_click.process_event(
                #c, self.managed(manager), manager,
                #date.fromtimestamp(raw_date),
            #)
        return True

    def years_kbd(self, offset) -> List[List[InlineKeyboardButton]]:
        years = []
        for n in range(offset.year - 7, offset.year + 7, 3):
            year_row = []
            for year in range(n, n + 3):
                year_row.append(InlineKeyboardButton(text=str(year),
                                                     callback_data=f"{self.widget_id}:{PREFIX_YEAR}{year}"))
            years.append(year_row)
        return years

    def months_kbd(self, offset) -> List[List[InlineKeyboardButton]]:
        header_year = offset.strftime("%Y год")
        months = []
        for n in MONTHS_NUMBERS:
            season = []
            for month in n:
                #month_text = date(offset.year, month, 1).strftime("%B")
                month_text = dt.ru_strftime("%B", date(offset.year, month, 1)).capitalize()
                season.append(InlineKeyboardButton(text=month_text,
                                                   callback_data=f"{self.widget_id}:{PREFIX_MONTH}{month}"))
            months.append(season)
        return [
            [
                InlineKeyboardButton(text=header_year,
                                     callback_data=f"{self.widget_id}:{SCOPE_YEARS}"),
            ],
            *months
        ]

    def days_kbd(self, offset) -> List[List[InlineKeyboardButton]]:
        #header_week = offset.strftime("%B %Y")
        header_week = dt.ru_strftime("%B %Y", offset).capitalize()
        weekheader = [InlineKeyboardButton(text=dayname, callback_data=" ")
                      for dayname in ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]]
        days = []
        for week in monthcalendar(offset.year, offset.month):
            week_row = []
            for day in week:
                if day == 0:
                    week_row.append(InlineKeyboardButton(text=" ",
                                                         callback_data=" "))
                else:
                    #raw_date = int(mktime(datetime(offset.year, offset.month, day, offset.hour, offset.minute).timetuple()))
                    if date(offset.year, offset.month, day) == date.today():
                        week_row.append(InlineKeyboardButton(text=f'☑️',
                                                         callback_data=f"{self.widget_id}:{PREFIX_DAY}{day}"))
                                                         #callback_data=f"{self.widget_id}:{raw_date}"))
                    elif date(offset.year, offset.month, day) < date.today():
                        week_row.append(InlineKeyboardButton(text=str(day),
                                                         callback_data=f"{self.widget_id}:wrong_date"))
                    else:
                        week_row.append(InlineKeyboardButton(text=str(day),
                                                         callback_data=f"{self.widget_id}:{PREFIX_DAY}{day}"))
                                                         #callback_data=f"{self.widget_id}:{raw_date}"))
            days.append(week_row)
        return [
            [
                InlineKeyboardButton(text="<",
                                     callback_data=f"{self.widget_id}:{MONTH_PREV}"),
                InlineKeyboardButton(text=header_week,
                                     callback_data=f"{self.widget_id}:{SCOPE_MONTHS}"),
                InlineKeyboardButton(text=">",
                                     callback_data=f"{self.widget_id}:{MONTH_NEXT}"),
            ],
            weekheader,
            *days,
            #[
                #InlineKeyboardButton(text="◀️",
                                     #callback_data=f"{self.widget_id}:{MONTH_PREV}"),
                ##InlineKeyboardButton(text="Уменьшить",
                                     ##callback_data=f"{self.widget_id}:{SCOPE_MONTHS}"),
                #InlineKeyboardButton(text="▶️",
                                     #callback_data=f"{self.widget_id}:{MONTH_NEXT}"),
            #],
        ]

    def hours_kbd(self, offset) -> List[List[InlineKeyboardButton]]:
        hours = []
        curr_hour = 0
        if offset.date() <= datetime.now().date():
            curr_hour = datetime.now().hour
        for n in range(0, 23, 4):
            hour_row = []
            for hour in range(n, n + 4):
                hour_row.append(InlineKeyboardButton(text=str('%02.d' % hour),
                                                     callback_data=f"{self.widget_id}:{PREFIX_HOUR}{hour}" if hour >= curr_hour else f"{self.widget_id}:wrong_date"))
            hours.append(hour_row)
        #return hours
        return [
            [InlineKeyboardButton(text = pytils.dt.ru_strftime('%d %B %Y', offset, inflected = True), callback_data=f"{self.widget_id}:{SCOPE_DAYS}")],
            [InlineKeyboardButton(text = "Выберите час (МСК)", callback_data="")],
            *hours
        ]
    

    def minutes_kbd(self, offset) -> List[List[InlineKeyboardButton]]:
        minutes = []
        curr_minute = 0
        if offset <= datetime.now():
            curr_minute = datetime.now().minute
        for n in range(0, 60, 20):
            minute_row = []
            for minute in range(n, n + 20, 5):
                minute_row.append(InlineKeyboardButton(text=str('%02.d' % minute),
                                                     callback_data=f"{self.widget_id}:{PREFIX_MINUTE}{minute}" if minute >= curr_minute else f"{self.widget_id}:wrong_date"))
            minutes.append(minute_row)
        #return minutes
        return [
            [InlineKeyboardButton(text = pytils.dt.ru_strftime('%d %B %Y время: %H:', offset, inflected = True), callback_data=f"{self.widget_id}:{SCOPE_DAYS}")],
            [InlineKeyboardButton(text = "Выберите минуты", callback_data="")],
            *minutes
        ]
    
    
    def get_scope(self, manager: DialogManager) -> str:
        calendar_data: CalendarData = manager.current_context().widget_data.get(self.widget_id, {})
        current_scope = calendar_data.get("current_scope")
        return current_scope or SCOPE_DAYS

    def get_offset(self, manager: DialogManager) -> date:
        calendar_data: CalendarData = manager.current_context().widget_data.get(self.widget_id, {})
        current_offset = calendar_data.get("current_offset")
        if current_offset is None:
            dt = datetime.now()
            return (dt + timedelta(minutes = 60 - dt.minute)).replace(second = 0, microsecond = 0)
        return datetime.fromisoformat(current_offset)

    def set_offset(self, new_offset: datetime, manager: DialogManager) -> None:
        data = manager.current_context().widget_data.setdefault(self.widget_id, {})
        data["current_offset"] = new_offset.isoformat()

    def set_scope(self, new_scope: str, manager: DialogManager) -> None:
        data = manager.current_context().widget_data.setdefault(self.widget_id, {})
        data["current_scope"] = new_scope

    def managed(self, manager: DialogManager):
        return ManagedCalendarAdapter(self, manager)


class ManagedCalendarAdapter(ManagedWidgetAdapter[Calendar]):
    def get_scope(self, manager: Optional[DialogManager] = None) -> str:
        manager_deprecated(manager)
        return self.widget.get_scope(self.manager)

    def get_offset(self, manager: Optional[DialogManager] = None) -> datetime:
        manager_deprecated(manager)
        return self.widget.get_offset(self.manager)

    def set_offset(self, new_offset: datetime,
                   manager: Optional[DialogManager] = None) -> None:
        manager_deprecated(manager)
        return self.widget.set_offset(new_offset, self.manager)

    def set_scope(self, new_scope: str,
                  manager: Optional[DialogManager] = None) -> None:
        manager_deprecated(manager)
        return self.widget.set_scope(new_scope, self.manager)
