from spreadsheetbot.sheets.registration import RegistrationAdapterClass

from spreadsheetbot.sheets.i18n import I18n

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

import pandas as pd

RegistrationAdapterClass.default_process_df_update = RegistrationAdapterClass._process_df_update
async def _process_df_update(self):
    await self.default_process_df_update()
    self.first_rerun_test = self._get(self.as_df.is_main_question == False)
RegistrationAdapterClass._process_df_update = _process_df_update

def int_get(self, selector, iloc = 0) -> pd.Series:
    row = self.as_df.loc[selector]
    if row.empty:
        return None
    return row.iloc[iloc]
RegistrationAdapterClass.int_get = int_get

def _get(self, selector, iloc=0) -> pd.Series:
    curr = self.int_get(selector, iloc)
    if type(curr) != pd.Series and curr == None:
        return None
    if curr.reply_keyboard == '':
        curr.reply_keyboard = ReplyKeyboardRemove()
    else:
        curr.reply_keyboard = ReplyKeyboardMarkup.from_column(curr.reply_keyboard.split("\n"))
    return curr
RegistrationAdapterClass._get = _get